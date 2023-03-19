from typing import List
from bot.macro.basic_macro_mixin import BasicMacroMixin
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


# TODO
# Scout with second scv
# Saturate gas until factory
# Pull out of gas
# Build add ons and move if space needed
class TvTStandardBuildOrderMixin(BasicMacroMixin):
    MIXIN_NAME: str = "TvTStandard"
    FIRST_SCV_TAG = None
    WALL_DONE = False
    NATURAL_TAG = None

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
        UnitTypeId.SIEGETANK,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
    ]

    async def on_unit_created(self, unit: Unit):
        print(f"{unit.name} created")
        if not self.FIRST_SCV_TAG and unit.type_id == UnitTypeId.SCV:
            self.FIRST_SCV_TAG = unit.tag
            print(f"First SCV Tag {self.FIRST_SCV_TAG}")

    async def on_building_construction_started(self, unit: Unit):
        print(f"{unit.name} started building")
        if len(self.build_order) == 0:
            # Build order is finished, nothing to remove
            return
        if unit.type_id == UnitTypeId.COMMANDCENTER:
            self.NATURAL_TAG = unit.tag

        self.build_order.remove(unit.type_id)

    def get_first_scv(self):
        return self.workers.find_by_tag(self.FIRST_SCV_TAG)

    def main_base_ramp_depot_positions(self):
        return list(self.main_base_ramp.corner_depots)

    async def patrol_build_scvs(self):
        first_scv = self.get_first_scv()

        if first_scv and not self.WALL_DONE:
            first_scv.patrol(self.main_base_ramp_depot_positions()[1], queue=True)

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
            ]:
                for building in self.structures(UnitTypeId.BARRACKS).ready.idle:
                    if unit_type_id == UnitTypeId.REAPER and self.can_afford(
                        UnitTypeId.REAPER
                    ):
                        building.train(self.build_order.pop(0))
                    elif self.can_afford(UnitTypeId.MARINE):
                        building.train(self.build_order.pop(0))

                    if (
                        building.has_reactor
                        and len(self.build_order) > 0
                        and self.can_afford(UnitTypeId.MARINE)
                        and self.build_order[0] == UnitTypeId.MARINE
                    ):
                        building.train(self.build_order.pop(0), can_afford_check=True)

                    building(AbilityId.RALLY_UNITS, rally_point)

            elif unit_type_id in [
                UnitTypeId.HELLION,
                UnitTypeId.CYCLONE,
                UnitTypeId.SIEGETANK,
            ]:
                for building in self.structures(UnitTypeId.FACTORY).ready.idle:
                    if unit_type_id == UnitTypeId.HELLION and self.can_afford(
                        UnitTypeId.HELLION
                    ):
                        building.train(self.build_order.pop(0))
                    elif self.can_afford(UnitTypeId.SIEGETANK):
                        building.train(self.build_order.pop(0))
                    (AbilityId.RALLY_UNITS, rally_point)

            elif unit_type_id == UnitTypeId.RAVEN:
                for building in self.structures(UnitTypeId.STARPORT).ready.idle:
                    if unit_type_id == UnitTypeId.RAVEN and self.can_afford(
                        UnitTypeId.RAVEN
                    ):
                        building.train(self.build_order.pop(0))
                    (AbilityId.RALLY_UNITS, rally_point)
            else:
                # If next unit is a structure
                if (
                    self.structures(UnitTypeId.SUPPLYDEPOT).amount == 0
                    and self.supply_used == 14
                ):
                    await self.build_structure(
                        UnitTypeId.SUPPLYDEPOT,
                        self.main_base_ramp_depot_positions()[0],
                        worker=self.get_first_scv(),
                    )

                if (
                    self.structures(UnitTypeId.BARRACKS).amount == 0
                    and self.supply_used <= 16
                ):
                    await self.build_structure(
                        UnitTypeId.BARRACKS,
                        self.main_base_ramp.barracks_correct_placement,
                        worker=self.get_first_scv(),
                    )

                if (
                    self.structures(UnitTypeId.REFINERY).amount == 0
                    and self.supply_used == 16
                ):
                    vg = self.vespene_geyser.closest_to(self.start_location)
                    worker = self.select_build_worker(vg.position)
                    if worker is None:
                        return

                    worker.build(UnitTypeId.REFINERY, vg)

                if (
                    self.structures(UnitTypeId.REFINERY).amount == 1
                    and self.supply_used == 17
                ):
                    vg = self.vespene_geyser.closer_than(
                        10, self.start_location
                    ).furthest_to(self.start_location)
                    worker = self.select_build_worker(vg.position)
                    if worker is None:
                        return

                    worker.build(UnitTypeId.REFINERY, vg)

                if self.structures(UnitTypeId.REFINERY).amount == 2:
                    await self.build_structure(
                        UnitTypeId.SUPPLYDEPOT,
                        self.main_base_ramp_depot_positions()[1],
                        worker=self.get_first_scv(),
                    )
                    self.WALL_DONE = True

                if (
                    self.WALL_DONE
                    and self.structures(UnitTypeId.FACTORY).amount == 0
                    and self.already_pending(UnitTypeId.FACTORY) == 0
                ):
                    await self.build_structure(UnitTypeId.FACTORY)

                if (
                    self.townhalls.amount == 1
                    and self.structures(UnitTypeId.FACTORY).amount == 1
                    and self.already_pending(UnitTypeId.COMMANDCENTER) == 0
                ):
                    await self.expand_now()

                if (
                    self.townhalls.amount == 2
                    and self.structures(UnitTypeId.FACTORY).amount == 1
                    and self.already_pending(UnitTypeId.COMMANDCENTER) == 1
                    and not self.already_pending(UnitTypeId.SUPPLYDEPOT)
                ):
                    await self.build_structure(UnitTypeId.SUPPLYDEPOT)

                if (
                    self.townhalls.amount == 2
                    and self.structures(UnitTypeId.STARPORT).amount == 0
                    and self.already_pending(UnitTypeId.STARPORT) == 0
                ):
                    await self.build_structure(UnitTypeId.STARPORT)

                if (
                    self.townhalls.amount == 2
                    and self.structures(UnitTypeId.STARPORT).amount == 1
                    and self.structures(UnitTypeId.BARRACKS)
                ):
                    rax = self.structures(UnitTypeId.BARRACKS).first
                    if not rax.has_add_on and not await self.can_place_single(
                        UnitTypeId.SUPPLYDEPOT, rax.position.offset((2.5, -0.5))
                    ):
                        rax(AbilityId.LIFT_BARRACKS)
                    else:
                        rax(AbilityId.BUILD_REACTOR, queue=True)

                if self.structures(UnitTypeId.BARRACKSREACTOR).amount == 1:
                    vg = self.vespene_geyser.closest_to(
                        self.structures.by_tag(self.NATURAL_TAG)
                    )
                    worker = self.select_build_worker(vg.position)
                    if worker is None:
                        return

                    worker.build(UnitTypeId.REFINERY, vg)

                if self.structures(UnitTypeId.REFINERY).amount == 3 and self.structures(
                    UnitTypeId.FACTORY
                ):
                    factory = self.structures(UnitTypeId.FACTORY).first
                    if not factory.has_add_on and not await self.can_place_single(
                        UnitTypeId.SUPPLYDEPOT, factory.position.offset((2.5, -0.5))
                    ):
                        factory(AbilityId.LIFT_FACTORY)
                    else:
                        factory(AbilityId.BUILD_TECHLAB, queue=True)

                if self.structures(
                    UnitTypeId.FACTORYTECHLAB
                ).amount == 1 and self.structures(UnitTypeId.STARPORT):
                    starport = self.structures(UnitTypeId.STARPORT).first
                    if not factory.has_add_on and not await self.can_place_single(
                        UnitTypeId.SUPPLYDEPOT, starport.position.offset((2.5, -0.5))
                    ):
                        starport(AbilityId.LIFT_STARPORT)
                    else:
                        starport(AbilityId.BUILD_TECHLAB, queue=True)

                if (
                    self.structures(UnitTypeId.STARPORTTECHLAB).amount == 1
                    and self.supply_left < 4
                    and self.structures(UnitTypeId.SUPPLYDEPOT).amount < 5
                ):
                    await self.build_structure(UnitTypeId.SUPPLYDEPOT)

    async def rally_workers_and_mules(self):
        for cc in self.townhalls:
            if not self.FIRST_SCV_TAG:
                cc(AbilityId.RALLY_WORKERS, self.main_base_ramp_depot_positions()[0])
            else:
                mfs = self.mineral_field.closer_than(10, cc)
                if mfs:
                    mf = max(mfs, key=lambda x: x.mineral_contents)
                    cc(AbilityId.RALLY_WORKERS, mf)

                cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf, can_afford_check=True)

    async def land_flying_buildings_with_add_on_space(self):
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

    async def on_step(self, iteration: int):
        # Need to patrol them so they aren't idle when the distribute workers looks for them
        await self.patrol_build_scvs()

        await self.rally_workers_and_mules()
        await self.build_order_step()
        await self.land_flying_buildings_with_add_on_space()

        if self.structures(UnitTypeId.FACTORY).amount < 1:
            for refinery in self.gas_buildings.ready:
                if refinery.assigned_harvesters < 3:
                    for worker in self.workers.closest_n_units(
                        refinery.position, 3 - refinery.assigned_harvesters
                    ):
                        worker.gather(refinery)

        await super().on_step(iteration)

        if len(self.build_order) == 0:
            print(
                f"Build order {self.MIXIN_NAME} ended in {self.time_formatted} with supply {self.supply_used}"
            )
            # Last thing to do, switch starport onto reactor
            return True
        else:
            return False
