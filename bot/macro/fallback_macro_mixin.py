import random
from bot.macro.basic_macro_mixin import BasicMacroMixin

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit

# You can save data to a ./data directory that will be persisted between games.
# That is how you do machine learning on the ladder


## Bot to handle fallback macro behaviors
## When a build order ends, this will be executed
class FallbackMacroMixin(BasicMacroMixin):
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
            if (
                not s.has_add_on
                and not await self.can_place_single(
                    UnitTypeId.SUPPLYDEPOT, s.position.offset((2.5, -0.5))
                )
                or s.has_techlab
            ):
                s(AbilityId.LIFT_STARPORT)
            else:
                s(AbilityId.BUILD_REACTOR, queue=True)

    async def build_production(self):
        # 1-1-1 -> 3-1-1 -> 5-1-1 -> 5-2-1 -> 8-2-1
        # Rax, factories and starports per base.
        # Index of outer array is base count
        production_buidings_per_base = [
            ([UnitTypeId.BARRACKS, UnitTypeId.BARRACKSFLYING], [1, 3, 5, 8, 11]),
            ([UnitTypeId.FACTORY, UnitTypeId.FACTORYFLYING], [1, 1, 2, 2, 4]),
            ([UnitTypeId.STARPORT, UnitTypeId.STARPORTFLYING], [1, 1, 1, 3, 4]),
        ]

        # Max of 4 ccs of production supported
        ccs = min(len(self.townhalls.ready), 5)

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

    async def expand(self):
        # Expand when all CC's have at least all minerals and one gas saturated
        if (
            self.can_afford(UnitTypeId.COMMANDCENTER)
            and self.units(UnitTypeId.SCV).amount >= self.townhalls.amount * 18
            and not self.already_pending(UnitTypeId.COMMANDCENTER)
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
                not self.structures(UnitTypeId.MISSILETURRET).closer_than(10, cc)
                and not self.already_pending(UnitTypeId.MISSILETURRET)
                and self.mineral_field.closer_than(10, cc)
            ):
                await self.build_structure(
                    UnitTypeId.MISSILETURRET,
                    cc.position.towards(
                        random.choice(self.mineral_field.closer_than(10, cc)), 6
                    ),
                )

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

    async def on_step_fallback_macro(self, iteration: int):
        await self.manage_cc_actions()
        await self.build_depots()
        await self.build_add_ons()
        await self.build_units()
        await self.build_refinery()
        await self.handle_upgrades()
        await self.expand()
        await self.build_defenses()
        await self.build_production()

        await super().on_step(iteration)
