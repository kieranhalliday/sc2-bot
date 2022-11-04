import random
from typing import Optional, Union

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2, Point3


# TODO
# Wall other bases that aren't the main
# get build incomplete buildings to work
# create repair function
# Be able to build 2 production buildings at once,
#   atm it only start the next one once the previous once is finished
# Monitor the performance of all the functions

## Bot to handle macro behaviors
## Desgined to be combined with the MicroBot
## and extended in the main bot class
class MacroBotMixin(BotAI):
    NAME: str = "MacroBot"
    build_type = "BIO"

    async def build_add_ons(self):
        production_buildings = (
            self.structures(UnitTypeId.BARRACKS)
            | self.structures(UnitTypeId.FACTORY)
            | self.structures(UnitTypeId.STARPORT)
        )

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
            and not self.already_pending(UnitTypeId.SUPPLYDEPOT)
        ):
            if len(depot_placement_positions) > 0:
                target_depot_location = depot_placement_positions.pop()
                await self.build_structure(
                    UnitTypeId.SUPPLYDEPOT, target_depot_location
                )
            else:
                max_minerals_left = 0

                for cc in self.townhalls:
                    mfs = self.mineral_field.closer_than(10, cc)
                    if mfs:
                        minerals_left = sum(map(lambda mf: mf.mineral_contents, mfs))
                        if minerals_left > max_minerals_left:
                            latest_cc = cc

                    if latest_cc:
                        await self.build_structure(
                            UnitTypeId.SUPPLYDEPOT,
                            latest_cc.position.towards(
                                self.game_info.map_center, 4
                            ).random_on_distance(6),
                        )

        await self.handle_depot_height()

    async def build_production(self):
        # 1-1-1 -> 3-1-1 -> 5-1-1 -> 5-2-1 -> 8-2-1
        production_buidings_per_base = [3, 5, 7, 11]
        if self.build_type == "BIO":
            production_build_order = [
                UnitTypeId.BARRACKS,
                UnitTypeId.FACTORY,
                UnitTypeId.STARPORT,
                UnitTypeId.BARRACKS,
                UnitTypeId.BARRACKS,
                UnitTypeId.BARRACKS,
                UnitTypeId.BARRACKS,
                UnitTypeId.FACTORY,
                UnitTypeId.BARRACKS,
                UnitTypeId.BARRACKS,
                UnitTypeId.BARRACKS,
            ]
            num_production_buildings = len(
                self.structures(UnitTypeId.BARRACKS)
                | self.structures(UnitTypeId.FACTORY)
                | self.structures(UnitTypeId.STARPORT)
            )

            # Avoid index errors
            ccs = max(
                min(
                    len(self.townhalls.ready) - 1, len(production_buidings_per_base) - 1
                ),
                0,
            )
            next_production_building = production_build_order[
                min(num_production_buildings, len(production_build_order) - 1)
            ]

            if num_production_buildings < production_buidings_per_base[ccs]:
                if num_production_buildings == 0 and not self.already_pending(
                    next_production_building
                ):
                    await self.build_structure(
                        next_production_building,
                        self.main_base_ramp.barracks_correct_placement,
                    )

                await self.build_structure(next_production_building)

        elif self.build_type == "MECH":
            pass

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

    async def build_structure(self, structure_id, position=None, can_afford_check=True):
        army_building = structure_id in [
            UnitTypeId.BARRACKS,
            UnitTypeId.FACTORY,
            UnitTypeId.STARPORT,
        ]

        if position == None:
            if army_building:
                near = self.main_base_ramp.barracks_correct_placement.to2
            elif len(self.townhalls) > 0:
                near = self.start_location.towards(
                    self.game_info.map_center, 4
                ).random_on_distance(3)
            else:
                near = self.all_own_units.random.position

            position = await self.find_placement(
                structure_id,
                near,
                placement_step=4,
                max_distance=20,
                addon_place=army_building,
            )
            # No position was found
            if position is None:
                print("No position found for ", structure_id)
                return

        worker = self.select_build_worker(position)
        if worker is None:
            return

        if await self.can_place_single(structure_id, position):
            worker.build(structure_id, position, can_afford_check=can_afford_check)

    async def build_upgrade_buildings(self):
        if (
            len(self.structures(UnitTypeId.BARRACKS)) >= 3
            and len(self.structures(UnitTypeId.ENGINEERINGBAY)) < 1
        ):
            await self.build_structure(UnitTypeId.ENGINEERINGBAY)
        if (
            len(self.structures(UnitTypeId.ENGINEERINGBAY)) == 1
            and self.already_pending(UnitTypeId.ENGINEERINGBAY) == 1
        ):
            await self.build_structure(UnitTypeId.ENGINEERINGBAY)

        if (
            not self.structures(UnitTypeId.ARMORY)
            and self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1)
            > 0.5
        ):
            await self.build_structure(UnitTypeId.ARMORY)

        if len(self.structures(UnitTypeId.FACTORY)) > 1 and not self.already_pending(
            UnitTypeId.ARMORY
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
            and await self.get_next_expansion() is not None
        ):
            await self.expand_now()

    async def finish_buildings_under_construction(self):
        structures_to_finish = self.structures_without_construction_SCVs()
        for structure in structures_to_finish:
            await self.build_structure(structure.type_id, structure.position)

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
            await self.distribute_workers()
            await self.manage_cc_actions()

        await self.build_workers()
        await self.build_depots()
        await self.build_refineries()
        await self.handle_upgrades()
        await self.expand()
        await self.build_production()
        await self.finish_buildings_under_construction()
        await self.build_add_ons()
        await self.build_units()

    async def find_placement(
        self,
        building: Union[UnitTypeId, AbilityId],
        near: Point2,
        max_distance: int = 20,
        random_alternative: bool = True,
        placement_step: int = 2,
        addon_place: bool = False,
    ) -> Optional[Point2]:
        """Finds a placement location for building.

        Example::

            if self.townhalls:
                cc = self.townhalls[0]
                depot_position = await self.find_placement(UnitTypeId.SUPPLYDEPOT, near=cc)

        :param building:
        :param near:
        :param max_distance:
        :param random_alternative:
        :param placement_step:
        :param addon_place:"""

        assert isinstance(building, (AbilityId, UnitTypeId))
        assert isinstance(near, Point2), f"{near} is no Point2 object"

        if isinstance(building, UnitTypeId):
            building = self.game_data.units[building.value].creation_ability.id

        if await self.can_place_single(building, near) and (
            not addon_place
            or await self.can_place_single(
                UnitTypeId.SUPPLYDEPOT, near.offset((2.5, -0.5))
            )
        ):
            return near

        if max_distance == 0:
            return None

        for distance in range(placement_step, max_distance, placement_step):
            possible_positions = [
                Point2(p).offset(near).to2
                for p in (
                    [
                        (dx, -distance)
                        for dx in range(-distance, distance + 1, placement_step)
                    ]
                    + [
                        (dx, distance)
                        for dx in range(-distance, distance + 1, placement_step)
                    ]
                    + [
                        (-distance, dy)
                        for dy in range(-distance, distance + 1, placement_step)
                    ]
                    + [
                        (distance, dy)
                        for dy in range(-distance, distance + 1, placement_step)
                    ]
                )
            ]
            res = await self.client._query_building_placement_fast(
                building, possible_positions
            )
            # Filter all positions if building can be placed
            possible = [p for r, p in zip(res, possible_positions) if r]

            # The find add on place logic did not work in the sc2 version of this function
            if addon_place:
                # Filter remaining positions if addon can be placed
                res = []

                for p in possible:
                    res.append(
                        await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, p.offset((2.5, -0.5))
                        )
                    )
                possible = [p for r, p in zip(res, possible) if r]

            if not possible:
                continue

            if random_alternative:
                return random.choice(possible)
            return min(possible, key=lambda p: p.distance_to_point2(near))
        return None
