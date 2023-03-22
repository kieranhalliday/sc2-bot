import random
from typing import Dict, List, Optional, Tuple, Union
from bot.build_orders.TvT_Standard import TvTStandardBuildOrder

from bot.build_orders.TvZ_Standard import TvZStandardBuildOrder
from bot.macro.basic_macro_mixin import BasicMacroMixin
from bot.types.add_on_movement import AddOnMovement
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class BuildOrderMixin(BasicMacroMixin):
    BUILD_ORDER: List[
        Tuple[
            Union[UnitTypeId, AbilityId, AddOnMovement],
            Optional[Point2],
            Optional[bool],
        ]
    ] = None
    BUILD_ORDER_META: Dict[str, str] = None

    BUILD_ORDER_FINISHED = False

    FIRST_SCV_TAG = None
    RAMP_CAN_FIT_ADD_ON = False

    async def on_unit_created(self, unit: Unit):
        if not self.FIRST_SCV_TAG and unit.type_id == UnitTypeId.SCV:
            self.FIRST_SCV_TAG = unit.tag

    async def on_building_construction_started(self, unit: Unit):
        print(f"{self.supply_used} {unit.name} started building")
        if len(self.BUILD_ORDER) == 0:
            # Build order is finished, nothing to remove
            return

        if unit.type_id == self.BUILD_ORDER[0][0]:
            self.BUILD_ORDER.pop(0)

    def get_first_scv(self):
        return self.workers.find_by_tag(self.FIRST_SCV_TAG)

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

        for building in self.structures(structure_type_id).ready:
            if self.can_afford(unit_type_id):
                building.train(unit_type_id)
                self.BUILD_ORDER.pop(0)

        if len(self.townhalls) > 0:
            rally_point = self.townhalls.closest_to(
                self.enemy_start_locations[0]
            ).position.towards(self.game_info.map_center, 5)

            (AbilityId.RALLY_UNITS, rally_point)

    def build_order_upgrades(self, ability_id):
        upgrade_building = None

        if ability_id in [
            AbilityId.RESEARCH_COMBATSHIELD,
            AbilityId.RESEARCH_CONCUSSIVESHELLS,
            AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK,
        ]:
            if self.structures(UnitTypeId.BARRACKSTECHLAB):
                upgrade_building = self.structures(UnitTypeId.BARRACKSTECHLAB).first

        elif ability_id in [
            AbilityId.RESEARCH_INFERNALPREIGNITER,
            AbilityId.RESEARCH_DRILLINGCLAWS,
            AbilityId.RESEARCH_SMARTSERVOS,
            AbilityId.RESEARCH_CYCLONELOCKONDAMAGE,
        ]:
            if self.structures(UnitTypeId.STARPORTTECHLAB):
                upgrade_building = self.structures(UnitTypeId.FACTORYTECHLAB).first

        if ability_id in [
            AbilityId.RESEARCH_BANSHEECLOAKINGFIELD,
            AbilityId.RESEARCH_BANSHEEHYPERFLIGHTROTORS,
        ]:
            if self.structures(UnitTypeId.STARPORTTECHLAB):
                upgrade_building = self.structures(UnitTypeId.STARPORTTECHLAB).first

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
            if self.structures(UnitTypeId.ENGINEERINGBAY):
                upgrade_building = self.structures(UnitTypeId.ENGINEERINGBAY).idle.first

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
            if self.structures(UnitTypeId.ARMORY):
                upgrade_building = self.structures(UnitTypeId.ARMORY).idle.first

        if self.can_afford(ability_id):
            upgrade_building(ability_id)
            self.BUILD_ORDER.pop(0)

    async def handle_add_on_movement(self, add_on_movement):
        if add_on_movement == AddOnMovement.BARRACKS_LEAVE_REACTOR:
            barracks = self.structures(UnitTypeId.BARRACKS).idle.filter(
                lambda rax: rax.has_reactor
            )
            if barracks:
                barracks.first(AbilityId.LIFT_BARRACKS)
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.BARRACKS_LEAVE_TECHLAB:
            barracks = self.structures(UnitTypeId.BARRACKS).idle.filter(
                lambda rax: rax.has_techlab
            )
            if barracks:
                barracks.first(AbilityId.LIFT_BARRACKS)
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.BARRACKS_LIFT_EMPTY:
            barracks = self.structures(UnitTypeId.BARRACKS).idle.filter(
                lambda b: not b.has_add_on
            )
            if barracks:
                barracks.first(AbilityId.LIFT_BARRACKS)
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.BARRACKS_LAND_REACTOR:
            barracks = self.structures(UnitTypeId.BARRACKSFLYING)
            free_reactors = self.structures(UnitTypeId.REACTOR).idle.filter(
                lambda r: self.structures.not_flying.closest_distance_to(
                    r.add_on_land_position
                )
                > 1
            )
            if barracks and free_reactors:
                barracks.first(
                    AbilityId.LAND_BARRACKS, free_reactors.first.add_on_land_position
                )
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.BARRACKS_LAND_TECHLAB:
            barracks = self.structures(UnitTypeId.BARRACKSFLYING)
            free_tech_labs = self.structures(UnitTypeId.TECHLAB).idle.filter(
                lambda r: self.structures.not_flying.closest_distance_to(
                    r.add_on_land_position
                )
                > 1
            )

            if barracks and free_tech_labs:
                barracks.first(
                    AbilityId.LAND_BARRACKS, free_tech_labs.first.add_on_land_position
                )
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.BARRACKS_LAND_EMPTY:
            barracks = self.structures(UnitTypeId.BARRACKSFLYING)
            if barracks:
                new_position = await self.find_placement(
                    UnitTypeId.BARRACKS, barracks.first.position, addon_place=True
                )
                if new_position is not None:
                    barracks.first(
                        AbilityId.LAND_BARRACKS,
                        new_position,
                    )
                    self.BUILD_ORDER.pop(0)

        # Factory Movements
        elif add_on_movement == AddOnMovement.FACTORY_LEAVE_REACTOR:
            factories = self.structures(UnitTypeId.FACTORY).idle.filter(
                lambda factory: factory.has_reactor
            )
            if factories:
                factories.first(AbilityId.LIFT_FACTORY)
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.FACTORY_LEAVE_TECHLAB:
            factories = self.structures(UnitTypeId.FACTORY).idle.filter(
                lambda factory: factory.has_techlab
            )
            if factories:
                factories.first(AbilityId.LIFT_FACTORY)
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.FACTORY_LIFT_EMPTY:
            factories = self.structures(UnitTypeId.FACTORY).idle.filter(
                lambda f: not f.has_add_on
            )
            if factories:
                factories.first(AbilityId.LIFT_FACTORY)
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.FACTORY_LAND_REACTOR:
            factories = self.structures(UnitTypeId.FACTORYFLYING)
            free_reactors = self.structures(UnitTypeId.REACTOR).idle.filter(
                lambda r: self.structures.not_flying.closest_distance_to(
                    r.add_on_land_position
                )
                > 1
            )
            if factories and free_reactors:
                factories.first(
                    AbilityId.LAND_FACTORY, free_reactors.first.add_on_land_position
                )
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.FACTORY_LAND_TECHLAB:
            factories = self.structures(UnitTypeId.FACTORYFLYING)
            free_tech_labs = self.structures(UnitTypeId.TECHLAB).idle.filter(
                lambda r: self.structures.not_flying.closest_distance_to(
                    r.add_on_land_position
                )
                > 1
            )

            if factories and free_tech_labs:
                factories.first(
                    AbilityId.LAND_FACTORY, free_tech_labs.first.add_on_land_position
                )
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.FACTORY_LAND_EMPTY:
            factories = self.structures(UnitTypeId.FACTORYFLYING)
            if factories:
                new_position = await self.find_placement(
                    UnitTypeId.FACTORY, factories.first.position, addon_place=True
                )
                if new_position is not None:
                    factories.first(
                        AbilityId.LAND_FACTORY,
                        new_position,
                    )
                    self.BUILD_ORDER.pop(0)

        # Starport movements
        elif add_on_movement == AddOnMovement.STARPORT_LEAVE_REACTOR:
            starports = self.structures(UnitTypeId.STARPORT).idle.filter(
                lambda starport: starport.has_reactor
            )
            if starports:
                starports.first(AbilityId.LIFT_STARPORT)
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.STARPORT_LEAVE_TECHLAB:
            starports = self.structures(UnitTypeId.STARPORT).idle.filter(
                lambda starport: starport.has_techlab
            )
            if starports:
                starports.first(AbilityId.LIFT_STARPORT)
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.STARPORT_LIFT_EMPTY:
            starports = self.structures(UnitTypeId.STARPORT).idle.filter(
                lambda f: not f.has_add_on
            )
            if starports:
                starports.first(AbilityId.LIFT_STARPORT)
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.STARPORT_LAND_REACTOR:
            starports = self.structures(UnitTypeId.STARPORTFLYING)
            free_reactors = self.structures(UnitTypeId.REACTOR).idle.filter(
                lambda r: self.structures.not_flying.closest_distance_to(
                    r.add_on_land_position
                )
                > 1
            )
            if starports and free_reactors:
                starports.first(
                    AbilityId.LAND_STARPORT, free_reactors.first.add_on_land_position
                )
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.STARPORT_LAND_TECHLAB:
            starports = self.structures(UnitTypeId.STARPORTFLYING)
            free_tech_labs = self.structures(UnitTypeId.TECHLAB).idle.filter(
                lambda r: self.structures.not_flying.closest_distance_to(
                    r.add_on_land_position
                )
                > 1
            )

            if starports and free_tech_labs:
                starports.first(
                    AbilityId.LAND_STARPORT, free_tech_labs.first.add_on_land_position
                )
                self.BUILD_ORDER.pop(0)

        elif add_on_movement == AddOnMovement.STARPORT_LAND_EMPTY:
            starports = self.structures(UnitTypeId.STARPORTFLYING)
            if starports:
                new_position = await self.find_placement(
                    UnitTypeId.starports, starports.first.position, addon_place=True
                )
                if new_position is not None:
                    starports.first(
                        AbilityId.LAND_STARPORT,
                        new_position,
                    )
                    self.BUILD_ORDER.pop(0)

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

            if next_unit in self.army_unit_type_ids:
                self.build_order_units(next_unit)
            elif type(next_unit) is AbilityId:
                self.build_order_upgrades(next_unit)
            elif type(next_unit) is AddOnMovement:
                await self.handle_add_on_movement(next_unit)
            else:
                # If next unit is a structure
                if (
                    next_unit == UnitTypeId.COMMANDCENTER
                    and self.already_pending(UnitTypeId.COMMANDCENTER) == 0
                    and await self.get_next_expansion() is not None
                ):
                    await self.expand_now()

                elif next_unit == UnitTypeId.SUPPLYDEPOT and not self.already_pending(
                    next_unit
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

                elif not self.already_pending(next_unit) and self.can_afford(next_unit):
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
        tvp_build_orders = [TvTStandardBuildOrder]
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

            # try:
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
                f.write(
                    f"Build order {self.BUILD_ORDER_META['name']} ended in {self.time_formatted} with supply {self.supply_used}\n"
                )
                f.close()

                print(
                    f"Build order {self.BUILD_ORDER_META['name']} ended in {self.time_formatted} with supply {self.supply_used}"
                )
                self.BUILD_ORDER_FINISHED = True
            # except Exception as e:
            #     # Something failed, end build order
            #     print("Build order failed ", e)
            #     self.BUILD_ORDER_FINISHED = True

        await super().on_step(iteration, build_order_finished=self.BUILD_ORDER_FINISHED)
