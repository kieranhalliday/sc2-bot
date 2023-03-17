import random
from bot.macro.macro_helpers_mixin import MacroHelpersMixin

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

# TODO
# Wall other bases that aren't the main
# create repair function
# build add on when no space (atm if no space add on won't be built)


## Bot to handle macro behaviors
## Desgined to be combined with the MicroBot
## and extended in the main bot class
class MacroBotMixin(MacroHelpersMixin):
    NAME: str = "MacroBot"
    build_type = "BIO"

    async def build_add_ons(self):
        for b in self.structures(UnitTypeId.BARRACKS).idle:
            if len(self.structures(UnitTypeId.BARRACKSTECHLAB)) == 0:
                b(AbilityId.BUILD_TECHLAB)
            else:
                b(AbilityId.BUILD_REACTOR)
        for f in self.structures(UnitTypeId.FACTORY).idle:
            f(AbilityId.BUILD_TECHLAB)
        for s in self.structures(UnitTypeId.STARPORT).idle:
            s(AbilityId.BUILD_REACTOR)

    async def build_depots(self):
        depot_placement_positions = self.main_base_ramp.corner_depots

        finished_depots = self.structures(UnitTypeId.SUPPLYDEPOT) | self.structures(
            UnitTypeId.SUPPLYDEPOTLOWERED
        )

        # Filter finish depot locations
        if finished_depots:
            depot_placement_positions = {
                d
                for d in depot_placement_positions
                if finished_depots.closest_distance_to(d) > 1
            }

        # Build depots
        if (
            self.can_afford(UnitTypeId.SUPPLYDEPOT)
            and self.supply_left < 5 * len(self.townhalls)
            and self.already_pending(UnitTypeId.SUPPLYDEPOT)
            < min(len(self.townhalls), 4)
            and self.supply_cap < 200
        ):
            if len(depot_placement_positions) > 0:
                target_depot_location = depot_placement_positions.pop()
                await self.build_structure(
                    UnitTypeId.SUPPLYDEPOT, target_depot_location
                )
            else:
                max_minerals_left = 0

                latest_cc = None
                for cc in self.townhalls:
                    mfs = self.mineral_field.closer_than(10, cc)
                    if mfs:
                        minerals_left = sum(map(lambda mf: mf.mineral_contents, mfs))
                        if minerals_left > max_minerals_left:
                            latest_cc = cc

                    if latest_cc is not None:
                        await self.build_structure(
                            UnitTypeId.SUPPLYDEPOT,
                            latest_cc.position.towards(
                                self.game_info.map_center, 4
                            ).random_on_distance(6),
                        )

        await self.handle_depot_height()

    async def build_production(self):
        # 1-1-1 -> 3-1-1 -> 5-1-1 -> 5-2-1 -> 8-2-1
        # Rax, factories and starports per base.
        # Index of outer array is base count
        production_buidings_per_base = [
            (UnitTypeId.BARRACKS, [1, 3, 5, 8]),
            (UnitTypeId.FACTORY, [1, 1, 2, 2]),
            (UnitTypeId.STARPORT, [1, 1, 1, 3]),
        ]

        # Max of 4 ccs of production supported
        ccs = min(len(self.townhalls.ready), 4)

        for production_building in production_buidings_per_base:
            building_id = production_building[0]
            building_count = production_building[1]

            if (
                len(self.structures(building_id)) + self.already_pending(building_id)
                < building_count[ccs - 1]
            ):
                if (
                    building_id == UnitTypeId.BARRACKS
                    and len(self.structures(building_id)) == 0
                ):
                    await self.build_structure(
                        building_id,
                        self.main_base_ramp.barracks_correct_placement,
                    )
                else:
                    await self.build_structure(building_id)

    async def build_refineries(self):
        for cc in self.townhalls.filter(lambda x: x.build_progress > 0.6):
            scvs_at_this_cc = []
            for scv in self.units(UnitTypeId.SCV):
                if scv.position.to2.distance_to(cc.position.to2) < 11:
                    scvs_at_this_cc.append(scv)

            if len(scvs_at_this_cc) < (
                16 + (len(self.structures(UnitTypeId.REFINERY).closer_than(11, cc)) * 3)
            ):
                # Don't build gas if minerals not saturated
                # Don't build second gas until first gas saturated
                return

            for vg in self.vespene_geyser.closer_than(10, cc):
                worker = self.select_build_worker(vg.position)
                if worker is None:
                    return

                worker.build(UnitTypeId.REFINERY, vg)

    async def build_upgrade_buildings(self):
        if (
            len(self.structures(UnitTypeId.BARRACKS)) >= 3
            and len(self.structures(UnitTypeId.ENGINEERINGBAY)) < 1
            and self.already_pending(UnitTypeId.ENGINEERINGBAY) < 1
        ):
            await self.build_structure(UnitTypeId.ENGINEERINGBAY)
        if (
            len(self.structures(UnitTypeId.ENGINEERINGBAY)) == 1
            and self.already_pending(UnitTypeId.ENGINEERINGBAY) == 1
        ):
            await self.build_structure(UnitTypeId.ENGINEERINGBAY)

        if (
            not self.structures(UnitTypeId.ARMORY)
            and not self.already_pending(UnitTypeId.ARMORY)
            and self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1)
            > 0.5
            or len(self.structures(UnitTypeId.FACTORY)) > 1
            and len(self.structures(UnitTypeId.ARMORY)) < 2
            and not self.already_pending(UnitTypeId.ARMORY)
        ):
            await self.build_structure(UnitTypeId.ARMORY)

        if (
            len(self.structures(UnitTypeId.FACTORY)) > 1
            and not self.already_pending(UnitTypeId.ARMORY)
            and self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1)
            > 0.5
            and self.already_pending_upgrade(UpgradeId.TERRANINFANTRYARMORSLEVEL1) > 0.5
        ):
            await self.build_structure(UnitTypeId.ARMORY)

    async def build_units(self):
        center = self.game_info.map_center
        rally_point = center
        if len(self.townhalls) > 0:
            rally_point = self.townhalls.closest_to(
                self.enemy_start_locations[0]
            ).position.towards(center, 5)

        for rax in self.structures(UnitTypeId.BARRACKS).ready:
            if rax.is_idle:
                rax.train(UnitTypeId.MARINE, can_afford_check=True)
                if rax.has_reactor:
                    rax.train(UnitTypeId.MARINE, can_afford_check=True)
            rax(AbilityId.RALLY_UNITS, rally_point)

        for factory in self.structures(UnitTypeId.FACTORY).ready:
            if factory.is_idle:
                factory.train(UnitTypeId.SIEGETANK, can_afford_check=True)
            factory(AbilityId.RALLY_UNITS, rally_point)

        for starport in self.structures(UnitTypeId.STARPORT).ready:
            if starport.is_idle:
                starport.train(UnitTypeId.VIKINGFIGHTER, can_afford_check=True)
                if starport.has_reactor:
                    starport.train(UnitTypeId.VIKINGFIGHTER, can_afford_check=True)
            starport(AbilityId.RALLY_UNITS, rally_point)

    async def build_workers(self):
        for cc in self.townhalls.ready:
            if (
                len(self.structures(UnitTypeId.ORBITALCOMMAND)) < 3
                and len(self.structures(UnitTypeId.BARRACKS)) > 0
            ):
                cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)
            elif len(self.structures(UnitTypeId.ENGINEERINGBAY)) > 0:
                cc(AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS)
            if (
                self.units(UnitTypeId.SCV).amount < self.townhalls.amount * 22
                and cc.is_idle
            ):
                cc.train(UnitTypeId.SCV)

    async def expand(self):
        # Expand when all CC's have at least all minerals and one gas saturated
        if (
            self.can_afford(UnitTypeId.COMMANDCENTER)
            and self.units(UnitTypeId.SCV).amount >= self.townhalls.amount * 18
            and self.already_pending(UnitTypeId.COMMANDCENTER)
            <= len(self.townhalls.ready)
            and await self.get_next_expansion() is not None
        ):
            await self.expand_now()

    async def build_defenses(self):
        for cc in self.townhalls:
            if (
                not self.structures(UnitTypeId.BUNKER).closer_than(6, cc).ready
                and len(self.structures(UnitTypeId.BARRACKS)) > 1
                and not self.already_pending(UnitTypeId.BUNKER)
            ):
                await self.build_structure(
                    UnitTypeId.BUNKER,
                    cc.position.towards(self.game_info.map_center, 6),
                )

            if (
                not self.structures(UnitTypeId.MISSILETURRET).closer_than(6, cc).ready
                and len(self.structures(UnitTypeId.ENGINEERINGBAY)) > 0
                and not self.already_pending(UnitTypeId.MISSILETURRET)
            ):
                await self.build_structure(
                    UnitTypeId.MISSILETURRET,
                    cc.position.towards(
                        random.choice(self.mineral_field.closer_than(10, cc)), 6
                    ),
                )

    async def finish_buildings_under_construction(self):
        structures_to_finish = self.structures_without_construction_SCVs()

        for structure in structures_to_finish:
            worker = self.select_build_worker(structure.position)
            if worker is None:
                break
            worker.smart(structure)

    async def handle_depot_height(self):
        # Raise depos when enemies are nearby
        for depo in self.structures(UnitTypeId.SUPPLYDEPOTLOWERED).ready:
            for unit in self.enemy_units:
                if unit.position.to2.distance_to(depo.position.to2) < 10:
                    depo(AbilityId.MORPH_SUPPLYDEPOT_RAISE)

        # Lower depos when no enemies are nearby
        for depo in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
            for unit in self.enemy_units:
                if unit.position.to2.distance_to(depo.position.to2) < 15:
                    break
            else:
                depo(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

    async def manage_cc_actions(self):
        for cc in self.townhalls:
            mfs = self.mineral_field.closer_than(10, cc)
            if mfs:
                mf = max(mfs, key=lambda x: x.mineral_contents)
                cc(AbilityId.RALLY_WORKERS, mf)
                cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf, can_afford_check=True)

    async def handle_upgrades(
        self,
        ebay_upgrade_order=None,
        armory_upgrade_order=None,
        prioritize_armory=False,
    ):
        await self.build_upgrade_buildings()

        if ebay_upgrade_order is None:
            ebay_upgrade_order = [
                UpgradeId.TERRANINFANTRYWEAPONSLEVEL1,
                UpgradeId.TERRANINFANTRYARMORSLEVEL1,
                UpgradeId.TERRANINFANTRYWEAPONSLEVEL2,
                UpgradeId.TERRANINFANTRYARMORSLEVEL2,
                UpgradeId.TERRANINFANTRYWEAPONSLEVEL3,
                UpgradeId.TERRANINFANTRYARMORSLEVEL3,
                UpgradeId.HISECAUTOTRACKING,
                UpgradeId.TERRANBUILDINGARMOR,
            ]

        if armory_upgrade_order is None:
            armory_upgrade_order = [
                UpgradeId.TERRANVEHICLEWEAPONSLEVEL1,
                UpgradeId.TERRANVEHICLEWEAPONSLEVEL2,
                UpgradeId.TERRANSHIPWEAPONSLEVEL1,
                UpgradeId.TERRANSHIPWEAPONSLEVEL2,
                UpgradeId.TERRANSHIPWEAPONSLEVEL3,
                UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1,
                UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2,
                UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3,
                UpgradeId.TERRANVEHICLEWEAPONSLEVEL3,
            ]

        if self.structures(UnitTypeId.ENGINEERINGBAY).idle:
            ebay = self.structures(UnitTypeId.ENGINEERINGBAY).idle.first

            for upgrade in ebay_upgrade_order:
                if not self.already_pending_upgrade(upgrade):
                    ebay.research(upgrade, can_afford_check=True)
                    break

        if self.structures(UnitTypeId.ARMORY).idle:
            armory = self.structures(UnitTypeId.ARMORY).idle.first
            for upgrade in armory_upgrade_order:
                if not self.already_pending_upgrade(upgrade):
                    armory.research(upgrade, can_afford_check=True)
                    break

        if self.structures(UnitTypeId.BARRACKSTECHLAB).idle:
            tech_lab = self.structures(UnitTypeId.BARRACKSTECHLAB).idle.first
            if not self.already_pending_upgrade(UpgradeId.STIMPACK):
                tech_lab.research(UpgradeId.STIMPACK, can_afford_check=True)
            elif not self.already_pending(AbilityId.RESEARCH_COMBATSHIELD):
                tech_lab(AbilityId.RESEARCH_COMBATSHIELD, can_afford_check=True)

    async def on_step_macro(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        # Macro cycle
        if iteration % 25 == 0:
            await self.manage_cc_actions()

        await self.distribute_workers()
        await self.build_workers()
        await self.build_depots()
        await self.build_refineries()
        await self.handle_upgrades()
        await self.expand()
        await self.build_defenses()
        await self.build_production()
        await self.finish_buildings_under_construction()
        await self.build_add_ons()
        await self.build_units()
