import random
from bot.macro.macro_helpers_mixin import MacroHelpersMixin

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit

# TODO
# Add speed mining functionality
# Expand more carefully
# Cancel buildings under attack
# You can save data to a ./data directory that will be persisted between games.
# That is how you do machine learning on the ladder


## Bot to handle macro behaviors
## Desgined to be combined with the MicroBot
## and extended in the main bot class
class MacroBotMixin(MacroHelpersMixin):
    NAME: str = "MacroBot"
    build_type = "BIO"

    async def build_add_ons(self):
        for b in self.structures(UnitTypeId.BARRACKS):
            if not b.has_add_on and not await self.can_place_single(
                UnitTypeId.SUPPLYDEPOT, b.position.offset((2.5, -0.5))
            ):
                b(AbilityId.LIFT_BARRACKS)
            else:
                if len(self.structures(UnitTypeId.BARRACKSTECHLAB)) == 0:
                    b(AbilityId.BUILD_TECHLAB, queue=True)
                else:
                    b(AbilityId.BUILD_REACTOR, queue=True)

        for f in self.structures(UnitTypeId.FACTORY).idle:
            if not f.has_add_on and not await self.can_place_single(
                UnitTypeId.SUPPLYDEPOT, f.position.offset((2.5, -0.5))
            ):
                f(AbilityId.LIFT_FACTORY)
            else:
                f(AbilityId.BUILD_TECHLAB, queue=True)

        for s in self.structures(UnitTypeId.STARPORT).idle:
            if not s.has_add_on and not await self.can_place_single(
                UnitTypeId.SUPPLYDEPOT, s.position.offset((2.5, -0.5))
            ):
                s(AbilityId.LIFT_STARPORT)
            else:
                s(AbilityId.BUILD_REACTOR, queue=True)

        # Find new positions for buildings without add on space
        for structure in (
            self.structures(UnitTypeId.BARRACKSFLYING).idle
            + self.structures(UnitTypeId.FACTORYFLYING).idle
            + self.structures(UnitTypeId.STARPORTFLYING).idle
        ):
            new_position = await self.find_placement(
                UnitTypeId.BARRACKS, structure.position, addon_place=True
            )
            if new_position is not None:
                structure(
                    AbilityId.LAND,
                    new_position,
                )

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
            and self.supply_left < 5 * len(self.townhalls.ready)
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

                if latest_cc is None:
                    latest_cc == random.choice(self.townhalls)

                if latest_cc is not None:
                    vg: Unit = random.choice(
                        self.vespene_geyser.closer_than(10, latest_cc)
                    )
                    position = await self.find_placement(
                        UnitTypeId.SUPPLYDEPOT,
                        vg.position.towards(
                            latest_cc,
                            2
                            * (
                                1
                                + len(
                                    self.structures.filter(
                                        lambda structure: structure.type_id
                                        == UnitTypeId.SUPPLYDEPOT
                                        or structure.type_id
                                        == UnitTypeId.SUPPLYDEPOTLOWERED
                                    ).closer_than(10, vg.position)
                                )
                            ),
                        ),
                    )

                    if position is None:
                        position = await self.find_placement(
                            UnitTypeId.SUPPLYDEPOT, latest_cc.position
                        )

                    await self.build_structure(UnitTypeId.SUPPLYDEPOT, position)

        await self.handle_depot_height()

    async def build_production(self):
        # 1-1-1 -> 3-1-1 -> 5-1-1 -> 5-2-1 -> 8-2-1
        # Rax, factories and starports per base.
        # Index of outer array is base count
        production_buidings_per_base = [
            ([UnitTypeId.BARRACKS, UnitTypeId.BARRACKSFLYING], [1, 3, 5, 8]),
            ([UnitTypeId.FACTORY, UnitTypeId.FACTORYFLYING], [1, 1, 2, 2]),
            ([UnitTypeId.STARPORT, UnitTypeId.STARPORTFLYING], [1, 1, 1, 3]),
        ]

        # Max of 4 ccs of production supported
        ccs = min(len(self.townhalls.ready), 4)

        for production_building in production_buidings_per_base:
            building_id = production_building[0][0]
            flying_building_id = production_building[0][1]
            building_count = production_building[1]
            if (
                len(self.structures(building_id))
                + self.already_pending(building_id)
                + len(self.structures(flying_building_id))
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

        for starport in self.structures(UnitTypeId.STARPORT).ready:
            if starport.is_idle:
                starport.train(UnitTypeId.VIKINGFIGHTER, can_afford_check=True)
                if starport.has_reactor:
                    starport.train(UnitTypeId.VIKINGFIGHTER, can_afford_check=True)
            starport(AbilityId.RALLY_UNITS, rally_point)

        for factory in self.structures(UnitTypeId.FACTORY).ready:
            if factory.is_idle:
                factory.train(UnitTypeId.SIEGETANK, can_afford_check=True)
            factory(AbilityId.RALLY_UNITS, rally_point)

        for rax in self.structures(UnitTypeId.BARRACKS).ready:
            if rax.is_idle:
                rax.train(UnitTypeId.MARINE, can_afford_check=True)
                if rax.has_reactor:
                    rax.train(UnitTypeId.MARINE, can_afford_check=True)
            rax(AbilityId.RALLY_UNITS, rally_point)

    async def build_workers(self):
        for cc in self.townhalls.ready:
            if len(self.structures(UnitTypeId.ORBITALCOMMAND)) < 3:
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

            if not self.structures(UnitTypeId.MISSILETURRET).closer_than(
                10, cc
            ).ready and not self.already_pending(UnitTypeId.MISSILETURRET):
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

    async def repair(self):
        priority_repair_buildings = [
            UnitTypeId.PLANETARYFORTRESS,
            UnitTypeId.BUNKER,
            UnitTypeId.MISSILETURRET,
        ]

        for unit in self.all_own_units:
            available_workers = self.workers.filter(
                lambda worker: not worker.is_repairing
            )

            if (
                unit.type_id in priority_repair_buildings
                and unit.health_percentage < 100
            ):
                # Always pull lots of workers for priority buildings
                for worker in available_workers.closest_n_units(unit.position, 10):
                    if worker is None:
                        break
                    worker.repair(unit)

            elif unit.health_percentage < 50 and unit.is_mechanical:
                worker = available_workers.closest_to(unit.position)
                if worker is None or worker.distance_to(unit) > 20:
                    break
                worker.repair(unit)

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
            elif not self.already_pending(AbilityId.RESEARCH_CONCUSSIVESHELLS):
                tech_lab(AbilityId.RESEARCH_CONCUSSIVESHELLS, can_afford_check=True)

        if self.structures(UnitTypeId.FACTORYTECHLAB).idle:
            tech_lab = self.structures(UnitTypeId.FACTORYTECHLAB).idle.first
            if not self.already_pending_upgrade(UpgradeId.SMARTSERVOS):
                tech_lab.research(UpgradeId.SMARTSERVOS, can_afford_check=True)

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
        await self.build_add_ons()
        await self.build_units()
        await self.build_refineries()
        await self.handle_upgrades()
        await self.expand()
        await self.build_defenses()
        await self.build_production()
        await self.finish_buildings_under_construction()
        await self.repair()
