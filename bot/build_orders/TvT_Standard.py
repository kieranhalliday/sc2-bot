from bot.macro.basic_macro_mixin import BasicMacroMixin
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


# TODO
# Scout with second scv
# Saturate gas until factory
class TvTStandardBuildOrderMixin(BasicMacroMixin):
    MIXIN_NAME: str = "TvTStandard"
    FIRST_SCV_TAG = None
    WALL_DONE = False

    structure_build_order = [
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.BARRACKS,
        UnitTypeId.REFINERY,
        UnitTypeId.REFINERY,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.FACTORY,
        UnitTypeId.COMMANDCENTER,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.STARPORT,
        UnitTypeId.BARRACKSREACTOR,
        UnitTypeId.FACTORYTECHLAB,
        UnitTypeId.STARPORTTECHLAB,
        UnitTypeId.REFINERY,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.SUPPLYDEPOT,
    ]

    unit_build_order = [
        UnitTypeId.REAPER,
        UnitTypeId.REAPER,
        UnitTypeId.HELLION,
        UnitTypeId.REAPER,
        UnitTypeId.HELLION,
        UnitTypeId.CYCLONE,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.RAVEN,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.SIEGETANK,
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
        if not self.FIRST_SCV_TAG and unit.type_id == UnitTypeId.SCV:
            self.FIRST_SCV_TAG = unit.tag
            print(f"First SCV Tag {self.FIRST_SCV_TAG}")

    async def on_building_construction_started(self, unit: Unit):
        self.structure_build_order.remove(unit.type_id)

    def get_first_scv(self):
        return self.workers.find_by_tag(self.FIRST_SCV_TAG)

    def main_base_ramp_depot_positions(self):
        return list(self.main_base_ramp.corner_depots)

    async def patrol_build_scvs(self):
        first_scv = self.get_first_scv()

        if first_scv and first_scv.is_idle and not self.WALL_DONE:
            first_scv.patrol(self.main_base_ramp_depot_positions()[1], queue=True)

    async def build_structures(self):
        print("Building structure ", len(self.structure_build_order))
        buildings_left = len(self.structure_build_order)

        # TODO Change this to use supply
        # This is super fucked up, figure out a better way
        if buildings_left == 15:
            await self.build_structure(
                self.structure_build_order[0],
                self.main_base_ramp_depot_positions()[0],
                worker=self.get_first_scv(),
            )
        if buildings_left == 14:
            await self.build_structure(
                self.structure_build_order[0],
                self.main_base_ramp.barracks_correct_placement,
                worker=self.get_first_scv(),
            )
        if buildings_left == 13 or buildings_left == 12 and self.supply_used == 17:
            for vg in self.vespene_geyser.closer_than(10, self.start_location):
                worker = self.select_build_worker(vg.position)
                if worker is None:
                    return

                worker.build(self.structure_build_order[0], vg)
                return

        if buildings_left == 11:
            self.WALL_DONE = True
            await self.build_structure(
                self.structure_build_order[0],
                self.main_base_ramp_depot_positions()[1],
                worker=self.get_first_scv(),
            )

    async def build_units(self):
        if len(self.townhalls) > 0:
            rally_point = self.townhalls.closest_to(
                self.enemy_start_locations[0]
            ).position.towards(self.game_info.map_center, 5)

        ready_production_buildings = (
            self.structures(UnitTypeId.BARRACKS).idle
            + self.structures(UnitTypeId.FACTORY).idle
            + self.structures(UnitTypeId.STARPORT).idle
        )
        for building in ready_production_buildings:
            if len(self.unit_build_order) > 0:
                unit = self.unit_build_order[0]
                building.train(unit, can_afford_check=True)
                if not building.is_idle:
                    self.unit_build_order.pop(0)

                if building.has_reactor and len(self.unit_build_order) > 0:
                    unit = self.unit_build_order[0]
                    building.train(unit, can_afford_check=True)
                    if not building.is_idle:
                        self.unit_build_order.pop(0)
            building(AbilityId.RALLY_UNITS, rally_point)

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
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        # Need to patrol them so they aren't idle when the distribute workers looks for them
        await self.patrol_build_scvs()
        await super().on_step(iteration)

        await self.rally_workers_and_mules()
        await self.build_structures()
        # await self.build_units()

        if len(self.structure_build_order) == 0 and len(self.unit_build_order) == 0:
            print(f"Build order {self.MIXIN_NAME} ended")
            return True
        else:
            return False
