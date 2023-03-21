from typing import List
from bot.macro.basic_macro_mixin import BasicMacroMixin
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit


# TODO
# Scout with second scv
# Saturate gas until factory
# Pull out of gas
class TvPStandardBuildOrderMixin(BasicMacroMixin):
    BUILD_ORDER_NAME: str = "TvPStandard"
    FIRST_SCV_TAG = None
    LATEST_CC = None

    build_order: List[UnitTypeId] = [
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.BARRACKS,
        UnitTypeId.REFINERY,
        UnitTypeId.REFINERY,
        UnitTypeId.REAPER,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.FACTORY,
        UnitTypeId.REAPER,
        UnitTypeId.COMMANDCENTER,
        UnitTypeId.HELLION,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.REAPER,
        UnitTypeId.STARPORT,
        UnitTypeId.HELLION,
        UnitTypeId.BARRACKSREACTOR,
        UnitTypeId.REFINERY,
        UnitTypeId.FACTORYTECHLAB,
        UnitTypeId.STARPORTTECHLAB,
        UnitTypeId.CYCLONE,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.RAVEN,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.SIEGETANK,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.RAVEN,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.SIEGETANK,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
    ]

    async def on_unit_created(self, unit: Unit):
        if not self.FIRST_SCV_TAG and unit.type_id == UnitTypeId.SCV:
            self.FIRST_SCV_TAG = unit.tag

    async def on_building_construction_started(self, unit: Unit):
        print(f"{self.supply_used} {unit.name} started building")
        if len(self.build_order) == 0 or unit.type_id not in self.build_order:
            # Build order is finished, nothing to remove
            return
        if unit.type_id == UnitTypeId.COMMANDCENTER:
            self.LATEST_CC = unit.tag

        self.build_order.remove(unit.type_id)

    def get_first_scv(self):
        return self.workers.find_by_tag(self.FIRST_SCV_TAG)

    async def build_order_step(self):
        if len(self.townhalls) > 0:
            rally_point = self.townhalls.closest_to(
                self.enemy_start_locations[0]
            ).position.towards(self.game_info.map_center, 5)

        if len(self.build_order) > 0:
            unit_type_id = self.build_order[0]
            if unit_type_id in [
                UnitTypeId.REAPER,
                UnitTypeId.MARINE,
                UnitTypeId.MARAUDER,
                UnitTypeId.GHOST,
            ]:
                for building in self.structures(UnitTypeId.BARRACKS).ready.idle:
                    if self.can_afford(unit_type_id):
                        building.train(self.build_order.pop(0))

                    if (
                        building.has_reactor
                        and len(self.build_order) > 0
                        and self.can_afford(self.build_order[0])
                        and self.build_order[0]
                        in [
                            UnitTypeId.REAPER,
                            UnitTypeId.MARINE,
                        ]
                    ):
                        building.train(self.build_order.pop(0))

                    building(AbilityId.RALLY_UNITS, rally_point)

            elif unit_type_id in [
                UnitTypeId.HELLION,
                UnitTypeId.WIDOWMINE,
                UnitTypeId.CYCLONE,
                UnitTypeId.SIEGETANK,
                UnitTypeId.THOR,
            ]:
                for building in self.structures(UnitTypeId.FACTORY).ready.idle:
                    if self.can_afford(unit_type_id):
                        building.train(self.build_order.pop(0))

                    if (
                        building.has_reactor
                        and len(self.build_order) > 0
                        and self.can_afford(self.build_order[0])
                        and self.build_order[0]
                        in [
                            UnitTypeId.HELLION,
                            UnitTypeId.WIDOWMINE,
                        ]
                    ):
                        building.train(self.build_order.pop(0))

                    building(AbilityId.RALLY_UNITS, rally_point)

            elif unit_type_id in [
                UnitTypeId.VIKING,
                UnitTypeId.MEDIVAC,
                UnitTypeId.LIBERATOR,
                UnitTypeId.RAVEN,
                UnitTypeId.BANSHEE,
                UnitTypeId.BATTLECRUISER,
            ]:
                for building in self.structures(UnitTypeId.STARPORT).ready.idle:
                    if self.can_afford(unit_type_id):
                        building.train(self.build_order.pop(0))

                    if (
                        building.has_reactor
                        and len(self.build_order) > 0
                        and self.can_afford(self.build_order[0])
                        and self.build_order[0]
                        in [UnitTypeId.VIKING, UnitTypeId.LIBERATOR, UnitTypeId.MEDIVAC]
                    ):
                        building.train(self.build_order.pop(0))

                    (AbilityId.RALLY_UNITS, rally_point)
            else:
                # If next unit is a structure
                if (
                    unit_type_id == UnitTypeId.COMMANDCENTER
                    and self.already_pending(UnitTypeId.COMMANDCENTER) == 0
                ):
                    await self.expand_now()

                elif unit_type_id == UnitTypeId.BARRACKSREACTOR:
                    rax_options = self.structures(UnitTypeId.BARRACKS).filter(
                        lambda rax: not rax.has_add_on
                    )
                    if not rax_options:
                        return
                    rax = rax_options.first
                    if not await self.can_place_single(
                        UnitTypeId.SUPPLYDEPOT, rax.position.offset((2.5, -0.5))
                    ):
                        rax(AbilityId.LIFT_BARRACKS)
                    else:
                        rax(AbilityId.BUILD_REACTOR)

                elif unit_type_id == UnitTypeId.FACTORYTECHLAB:
                    factory_options = self.structures(UnitTypeId.FACTORY).filter(
                        lambda factory: not factory.has_add_on
                    )
                    if not factory_options:
                        return
                    factory = factory_options.first
                    if not factory.has_add_on and not await self.can_place_single(
                        UnitTypeId.SUPPLYDEPOT, factory.position.offset((2.5, -0.5))
                    ):
                        factory(AbilityId.LIFT_FACTORY)
                    else:
                        factory(AbilityId.BUILD_TECHLAB)

                elif unit_type_id == UnitTypeId.STARPORTTECHLAB:
                    starport_options = self.structures(UnitTypeId.STARPORT).filter(
                        lambda starport: not starport.has_add_on
                    )
                    if not starport_options:
                        return
                    starport = starport_options.first
                    if not starport.has_add_on and not await self.can_place_single(
                        UnitTypeId.SUPPLYDEPOT, starport.position.offset((2.5, -0.5))
                    ):
                        starport(AbilityId.LIFT_STARPORT)
                    else:
                        starport(AbilityId.BUILD_TECHLAB)

                elif (
                    unit_type_id == UnitTypeId.SUPPLYDEPOT
                    and not self.already_pending(unit_type_id)
                ):
                    await self.build_depots(force=True)

                elif unit_type_id == UnitTypeId.REFINERY:
                    await self.build_refinery(force=True)

                elif not self.already_pending(unit_type_id):
                    # Finish wall if not already finished
                    if (
                        self.structures.closest_distance_to(
                            self.main_base_ramp.barracks_correct_placement
                        )
                        > 1
                    ):
                        await self.build_structure(
                            unit_type_id,
                            # TODO sometimes this doesn't leave space for an add on properly
                            position=self.main_base_ramp.barracks_correct_placement,
                            worker=self.get_first_scv(),
                        )
                    else:
                        await self.build_structure(unit_type_id)

    async def rally_workers_and_mules(self):
        for cc in self.townhalls:
            if not self.LATEST_CC:
                self.LATEST_CC = cc.tag
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

    async def build_order_on_step(self, iteration: int):
        await self.rally_workers_and_mules()
        await self.build_order_step()

        # TODO: remove this when speed mining is implemented
        if self.structures(UnitTypeId.FACTORY).amount < 1:
            for refinery in self.gas_buildings.ready:
                if refinery.assigned_harvesters < 3:
                    for worker in self.workers.closest_n_units(
                        refinery.position, 3 - refinery.assigned_harvesters
                    ):
                        worker.gather(refinery)

        await super().on_step(iteration)

        if len(self.build_order) == 0:
            f = open("data/TvPStandard.txt", "a")
            f.write(
                f"Build order {self.BUILD_ORDER_NAME} ended in {self.time_formatted} with supply {self.supply_used}\n"
            )
            f.close()

            print(
                f"Build order {self.BUILD_ORDER_NAME} ended in {self.time_formatted} with supply {self.supply_used}\n"
            )
            return True
        else:
            return False
