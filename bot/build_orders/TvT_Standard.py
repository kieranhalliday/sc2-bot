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
# Build add ons and move if space needed
class TvTStandardBuildOrderMixin(BasicMacroMixin):
    MIXIN_NAME: str = "TvTStandard"
    FIRST_SCV_TAG = None
    WALL_DONE = False

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

    async def on_step(self, iteration: int):
        # Need to patrol them so they aren't idle when the distribute workers looks for them
        await self.patrol_build_scvs()

        await self.rally_workers_and_mules()
        await self.build_order_step()

        if self.structures(UnitTypeId.FACTORY).amount < 1:
            for refinery in self.gas_buildings.ready:
                if refinery.assigned_harvesters < 3:
                    for worker in self.workers.closest_n_units(
                        refinery.position, 3 - refinery.assigned_harvesters
                    ):
                        worker.gather(refinery)
        else:
            for refinery in self.gas_buildings.ready:
                if refinery.assigned_harvesters == 3:
                    for worker in self.workers.closest_n_units(refinery.position, 2):
                        worker.gather(self.mineral_field.closest_to(worker))

        await super().on_step(iteration)

        if len(self.build_order) == 0:
            print(f"Build order {self.MIXIN_NAME} ended")
            # Last thing to do, switch starport onto reactor
            return True
        else:
            return False
