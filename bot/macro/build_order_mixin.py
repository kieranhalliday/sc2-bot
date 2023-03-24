import random
from typing import Dict, List, Optional, Tuple, Union
from bot.build_orders.TvP_3rax import TvP3RaxBuildOrder
from bot.build_orders.TvT_Standard import TvTStandardBuildOrder

from bot.build_orders.TvZ_Standard import TvZStandardBuildOrder
from bot.macro.basic_macro_mixin import BasicMacroMixin
from bot.types.add_on_movement import AddOnMovementType, AddOnType
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class BuildOrderMixin(BasicMacroMixin):
    BUILD_ORDER: List[
        Tuple[
            Union[
                str,
                UnitTypeId,
                AbilityId,
                Tuple[UnitTypeId, AddOnMovementType, AddOnType],
            ],
            Optional[Point2],
            Optional[bool],
        ]
    ] = None
    BUILD_ORDER_META: Dict[str, str] = None
    BUILD_ORDER_FINISHED = False

    FIRST_SCV_TAG = None
    RAMP_CAN_FIT_ADD_ON = False
    COMBAT_MODE = "defend"

    last_build_order_step_success_time = 0

    async def on_unit_created(self, unit: Unit):
        if not self.FIRST_SCV_TAG and unit.type_id == UnitTypeId.SCV:
            self.FIRST_SCV_TAG = unit.tag

    async def on_building_construction_started(self, unit: Unit):
        print(f"{self.supply_used} {unit.name} started building")
        if len(self.BUILD_ORDER) == 0:
            # Build order is finished, nothing to remove
            return

        if unit.type_id == self.BUILD_ORDER[0][0]:
            self.build_order_step_complete()

    def get_first_scv(self):
        return self.workers.find_by_tag(self.FIRST_SCV_TAG)

    def build_order_step_complete(self):
        self.last_build_order_step_success_time = self.time
        self.BUILD_ORDER.pop(0)

    def rally_workers_and_mules(self):
        for cc in self.townhalls:
            if not self.FIRST_SCV_TAG:
                cc(
                    AbilityId.RALLY_WORKERS,
                    self.main_base_ramp.bottom_center,
                )
            else:
                mfs = self.mineral_field.closer_than(10, cc)
                if mfs:
                    mf = max(mfs, key=lambda x: x.mineral_contents)
                    cc(AbilityId.RALLY_WORKERS, mf)
                    cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf, can_afford_check=True)

    def build_order_units(self, unit_type_id):
        structure_type_id = UnitTypeId.BARRACKS
        if unit_type_id in [
            UnitTypeId.HELLION,
            UnitTypeId.WIDOWMINE,
            UnitTypeId.CYCLONE,
            UnitTypeId.SIEGETANK,
            UnitTypeId.THOR,
        ]:
            structure_type_id = UnitTypeId.FACTORY

        if unit_type_id in [
            UnitTypeId.VIKING,
            UnitTypeId.MEDIVAC,
            UnitTypeId.LIBERATOR,
            UnitTypeId.RAVEN,
            UnitTypeId.BANSHEE,
            UnitTypeId.BATTLECRUISER,
        ]:
            structure_type_id = UnitTypeId.STARPORT

        available_structures = self.structures(structure_type_id).ready.filter(
            lambda s: s.is_idle
            or (s.has_reactor and self.already_pending(unit_type_id, [s]) < 2)
        )

        if not available_structures:
            return

        building = available_structures.first

        if self.can_afford(unit_type_id):
            building.train(unit_type_id)
            self.build_order_step_complete()

        if len(self.townhalls) > 0:
            rally_point = self.townhalls.closest_to(
                self.enemy_start_locations[0]
            ).position.towards(self.game_info.map_center, 5)

            building(AbilityId.RALLY_UNITS, rally_point)

    def build_order_upgrades(self, ability_id):
        upgrade_building = None
        if ability_id in [
            AbilityId.RESEARCH_COMBATSHIELD,
            AbilityId.RESEARCH_CONCUSSIVESHELLS,
            AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK,
        ]:
            if self.structures(UnitTypeId.BARRACKSTECHLAB).idle.ready:
                upgrade_building = self.structures(
                    UnitTypeId.BARRACKSTECHLAB
                ).idle.ready.first

        elif ability_id in [
            AbilityId.RESEARCH_INFERNALPREIGNITER,
            AbilityId.RESEARCH_DRILLINGCLAWS,
            AbilityId.RESEARCH_SMARTSERVOS,
            AbilityId.RESEARCH_CYCLONELOCKONDAMAGE,
        ]:
            if self.structures(UnitTypeId.FACTORYTECHLAB).idle.ready:
                upgrade_building = self.structures(
                    UnitTypeId.FACTORYTECHLAB
                ).idle.ready.first

        elif ability_id in [
            AbilityId.RESEARCH_BANSHEECLOAKINGFIELD,
            AbilityId.RESEARCH_BANSHEEHYPERFLIGHTROTORS,
        ]:
            if self.structures(UnitTypeId.STARPORTTECHLAB).idle.ready:
                upgrade_building = self.structures(
                    UnitTypeId.STARPORTTECHLAB
                ).idle.ready.first

        elif ability_id in [
            AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL1,
            AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL2,
            AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL3,
            AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL1,
            AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL2,
            AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL3,
            AbilityId.RESEARCH_HISECAUTOTRACKING,
            AbilityId.RESEARCH_NEOSTEELFRAME,
        ]:
            if self.structures(UnitTypeId.ENGINEERINGBAY).idle.ready:
                upgrade_building = self.structures(
                    UnitTypeId.ENGINEERINGBAY
                ).idle.ready.first

        elif ability_id in [
            AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL1,
            AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL2,
            AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL3,
            AbilityId.ARMORYRESEARCH_TERRANSHIPWEAPONSLEVEL1,
            AbilityId.ARMORYRESEARCH_TERRANSHIPWEAPONSLEVEL2,
            AbilityId.ARMORYRESEARCH_TERRANSHIPWEAPONSLEVEL3,
            AbilityId.ARMORYRESEARCH_TERRANVEHICLEWEAPONSLEVEL1,
            AbilityId.ARMORYRESEARCH_TERRANVEHICLEWEAPONSLEVEL2,
            AbilityId.ARMORYRESEARCH_TERRANVEHICLEWEAPONSLEVEL3,
        ]:
            if self.structures(UnitTypeId.ARMORY).idle.ready:
                upgrade_building = self.structures(UnitTypeId.ARMORY).idle.ready.first

        if upgrade_building is not None and self.can_afford(ability_id):
            upgrade_building(ability_id, can_afford_check=True)
            self.build_order_step_complete()

    async def handle_add_on_movement(self, add_on_movement):
        structure_to_move = add_on_movement[0]
        movement_type = add_on_movement[1]
        target_add_on = add_on_movement[2]

        # Filter for strucutres without add on by default
        filter_lambda = lambda structure: not structure.has_add_on

        if target_add_on == AddOnType.REACTOR:
            filter_lambda = lambda structure: structure.has_reactor
        elif target_add_on == AddOnType.TECHLAB:
            filter_lambda = lambda structure: structure.has_techlab

        if movement_type == AddOnMovementType.LIFT:
            structures = self.structures(structure_to_move).idle.ready.filter(
                filter_lambda
            )
            if structures:
                if structure_to_move == UnitTypeId.BARRACKS:
                    structures.first(AbilityId.LIFT_BARRACKS)
                elif structure_to_move == UnitTypeId.FACTORY:
                    structures.first(AbilityId.LIFT_FACTORY)
                elif structure_to_move == UnitTypeId.STARPORT:
                    structures.first(AbilityId.LIFT_STARPORT)
                self.build_order_step_complete()
        elif movement_type == AddOnMovementType.LAND:
            landing_ability = AbilityId.LAND_BARRACKS
            if structure_to_move == UnitTypeId.FACTORYFLYING:
                landing_ability = AbilityId.LAND_FACTORY
            elif structure_to_move == UnitTypeId.STARPORTFLYING:
                landing_ability = AbilityId.LAND_STARPORT

            # All these unit types should be the flying versions of the building
            if target_add_on == AddOnType.EMPTY:
                structures = self.structures(structure_to_move)
                if structures:
                    for placement_step in range(2, 5):
                        new_position = await self.find_placement(
                            UnitTypeId.BARRACKS,
                            structures.first.position,
                            addon_place=True,
                            placement_step=placement_step,
                        )
                        if (
                            new_position is not None
                            and new_position.distance_to_closest(
                                map(
                                    lambda addon: addon.add_on_land_position,
                                    self.structures(
                                        {UnitTypeId.REACTOR, UnitTypeId.TECHLAB}
                                    ),
                                )
                            )
                            > 3
                        ):
                            structures.first(
                                landing_ability,
                                new_position,
                            )
                            self.build_order_step_complete()
                            return
            elif target_add_on == AddOnType.REACTOR:
                structures = self.structures(structure_to_move)
                free_reactors = self.structures(UnitTypeId.REACTOR).idle.ready.filter(
                    lambda r: self.structures.not_flying.closest_distance_to(
                        r.add_on_land_position
                    )
                    > 1
                )
                if structures and free_reactors:
                    structures.first(
                        landing_ability, free_reactors.first.add_on_land_position
                    )
                    self.build_order_step_complete()
            elif target_add_on == AddOnType.TECHLAB:
                structures = self.structures(structure_to_move)
                free_tech_labs = self.structures(UnitTypeId.TECHLAB).idle.ready.filter(
                    lambda r: self.structures.not_flying.closest_distance_to(
                        r.add_on_land_position
                    )
                    > 1
                )
                if structures and free_tech_labs:
                    structures.first(
                        landing_ability, free_tech_labs.first.add_on_land_position
                    )
                    self.build_order_step_complete()

    async def build_order_step(self):
        if len(self.BUILD_ORDER) > 0:
            next_step = self.BUILD_ORDER[0]
            next_unit = next_step[0]
            next_unit_pos = None
            is_builder_first_worker = False
            if len(next_step) == 2:
                next_unit_pos = self.BUILD_ORDER[1]
            if len(next_step) == 3:
                next_unit_pos = self.BUILD_ORDER[1]
                is_builder_first_worker = self.BUILD_ORDER[2]

            # Only attempt to build something for 90 seconds
            if self.time - self.last_build_order_step_success_time > 90:
                f = open(f"data/{self.BUILD_ORDER_META['name']}.txt", "a")
                f.write(
                    f"""Build order {self.BUILD_ORDER_META['name']} failed in {self.time_formatted} on building {next_unit}\n"""
                )
                f.close()
                self.COMBAT_MODE = False
                self.BUILD_ORDER_FINISHED = True
                return

            if next_step[0] in ["attack", "defend"]:
                # Tell the micro bot to change modes
                self.COMBAT_MODE = next_step[0]
                self.build_order_step_complete()
                return

            if self.supply_left < 4 and not self.already_pending(
                UnitTypeId.SUPPLYDEPOT
            ):
                await self.build_depots(force=True)

            if next_unit in self.army_unit_type_ids:
                self.build_order_units(next_unit)
            elif type(next_unit) is AbilityId:
                self.build_order_upgrades(next_unit)
            elif type(next_unit) is tuple:
                await self.handle_add_on_movement(next_unit)
            else:
                # If next unit is a structure
                if (
                    next_unit == UnitTypeId.COMMANDCENTER
                    and self.already_pending(UnitTypeId.COMMANDCENTER) == 0
                    and await self.get_next_expansion() is not None
                ):
                    await self.expand_now()

                elif (
                    next_unit == UnitTypeId.SUPPLYDEPOT
                    and not self.already_pending(next_unit)
                ) or (
                    self.supply_left < 4
                    and not self.already_pending(UnitTypeId.SUPPLYDEPOT)
                ):
                    await self.build_depots(force=True)

                elif next_unit == UnitTypeId.REFINERY:
                    await self.build_refinery(force=True)

                elif (
                    next_unit == UnitTypeId.BARRACKSREACTOR
                    or next_unit == UnitTypeId.BARRACKSTECHLAB
                ):
                    barracks = self.structures(UnitTypeId.BARRACKS).filter(
                        lambda b: not b.has_add_on
                    )

                    if barracks:
                        rax = barracks.first
                        if not rax.has_add_on and not await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, rax.position.offset((2.5, -0.5))
                        ):
                            rax(AbilityId.LIFT_BARRACKS)
                        else:
                            if next_unit == UnitTypeId.BARRACKSREACTOR:
                                rax(AbilityId.BUILD_REACTOR_BARRACKS)
                            else:
                                rax(AbilityId.BUILD_TECHLAB_BARRACKS)

                elif (
                    next_unit == UnitTypeId.FACTORYREACTOR
                    or next_unit == UnitTypeId.FACTORYTECHLAB
                ):
                    factories = self.structures(UnitTypeId.FACTORY).filter(
                        lambda f: not f.has_add_on
                    )

                    if factories:
                        factory = factories.first
                        if not factory.has_add_on and not await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, factory.position.offset((2.5, -0.5))
                        ):
                            factory(AbilityId.LIFT_FACTORY)
                        else:
                            if next_unit == UnitTypeId.FACTORYREACTOR:
                                factory(AbilityId.BUILD_REACTOR_FACTORY)
                            else:
                                factory(AbilityId.BUILD_TECHLAB_FACTORY)

                elif (
                    next_unit == UnitTypeId.STARPORTREACTOR
                    or next_unit == UnitTypeId.STARPORTTECHLAB
                ):
                    starports = self.structures(UnitTypeId.STARPORT).filter(
                        lambda s: not s.has_add_on
                    )

                    if starports:
                        starport = starports.first
                        if not starport.has_add_on and not await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT,
                            starport.position.offset((2.5, -0.5)),
                        ):
                            starport(AbilityId.LIFT_STARPORT)
                        else:
                            if next_unit == UnitTypeId.STARPORTREACTOR:
                                starport(AbilityId.BUILD_REACTOR_STARPORT)
                            else:
                                starport(AbilityId.BUILD_TECHLAB_STARPORT)

                elif self.can_afford(next_unit):
                    # Finish wall if not already finished
                    if (
                        self.structures.closest_distance_to(
                            self.main_base_ramp.barracks_correct_placement
                        )
                        > 1
                    ):
                        await self.build_structure(
                            next_unit,
                            position=self.main_base_ramp.barracks_correct_placement,
                            worker=self.get_first_scv(),
                        )
                    else:
                        await self.build_structure(next_unit)

    async def build_order_on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        tvt_build_orders = [TvTStandardBuildOrder]
        tvp_build_orders = [TvP3RaxBuildOrder]
        tvz_build_orders = [TvZStandardBuildOrder]
        chosen_build_order = None

        if self.enemy_race == Race.Terran:
            chosen_build_order = random.choice(tvt_build_orders)
        elif self.enemy_race == Race.Protoss:
            chosen_build_order = random.choice(tvp_build_orders)
        elif self.enemy_race == Race.Zerg:
            chosen_build_order = random.choice(tvz_build_orders)
        elif self.enemy_race == Race.Random:
            chosen_build_order = random.choice(
                tvt_build_orders + tvp_build_orders + tvz_build_orders
            )
        else:
            self.BUILD_ORDER_FINISHED = True

        self.BUILD_ORDER_META = chosen_build_order.build_order(self)["meta"]
        self.BUILD_ORDER = chosen_build_order.build_order(self)["build"]

        print(f"Chosen bot {self.BUILD_ORDER_META['name']}")

    async def build_order_on_step(self, iteration: int):
        if not self.BUILD_ORDER_FINISHED:
            self.RAMP_CAN_FIT_ADD_ON = self.main_base_ramp.barracks_can_fit_addon

            try:
                self.rally_workers_and_mules()
                await self.build_order_step()

                # TODO: remove this when speed mining is implemented
                if self.structures(UnitTypeId.FACTORY).amount < 1:
                    for refinery in self.gas_buildings.ready:
                        if refinery.assigned_harvesters < 3:
                            for worker in self.workers.closest_n_units(
                                refinery.position, 3 - refinery.assigned_harvesters
                            ):
                                worker.gather(refinery)

                if len(self.BUILD_ORDER) == 0:
                    f = open(f"data/{self.BUILD_ORDER_META['name']}.txt", "a")
                    goal_time = self.BUILD_ORDER_META["goal_time_sec"]
                    f.write(
                        f"""Build order {self.BUILD_ORDER_META['name']} ended in {self.time_formatted} with supply {self.supply_used}. Seconds behind goal: {self.time} of {goal_time}\n"""
                    )
                    f.close()
                    self.BUILD_ORDER_FINISHED = True
            except Exception as e:
                # Something failed, end build order
                print("Build order failed ", e)
                self.BUILD_ORDER_FINISHED = True

        await super().on_step(iteration, build_order_finished=self.BUILD_ORDER_FINISHED)
        return self.COMBAT_MODE
