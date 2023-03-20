from typing import List
from bot.macro.basic_macro_mixin import BasicMacroMixin
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit


class TvZStandardBuildOrderMixin(BasicMacroMixin):
    MIXIN_NAME: str = "TvZStandard"
    FIRST_SCV_TAG = None
    WALL_DONE = False
    LATEST_CC = None

    build_order: List[UnitTypeId] = [
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.BARRACKS,
        UnitTypeId.REFINERY,
        UnitTypeId.REAPER,
        UnitTypeId.COMMANDCENTER,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.MARINE,
        UnitTypeId.FACTORY,
        UnitTypeId.BARRACKSREACTOR,
        UnitTypeId.COMMANDCENTER,
        UnitTypeId.STARPORT,
        UnitTypeId.REFINERY,
        UnitTypeId.FACTORYREACTOR,
        UnitTypeId.HELLION,
        UnitTypeId.HELLION,
        UnitTypeId.BARRACKSTECHLAB,
        UnitTypeId.HELLION,
        UnitTypeId.HELLION,
        UnitTypeId.STARPORTTECHLAB,
        UnitTypeId.BANSHEE,
        UpgradeId.BANSHEECLOAK,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.HELLION,
        UnitTypeId.HELLION,
        UnitTypeId.BARRACKSTECHLAB,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.HELLION,
        UnitTypeId.HELLION,
        UnitTypeId.MARINE,
        UpgradeId.STIMPACK,
        UnitTypeId.BANSHEE,
        UnitTypeId.REFINERY,
        UnitTypeId.BARRACKS,
        UnitTypeId.BARRACKS,
        UnitTypeId.SUPPLYDEPOT,
        UnitTypeId.MARINE,
        UnitTypeId.FACTORYREACTOR,
        UnitTypeId.REFINERY,
        UnitTypeId.ENGINEERINGBAY,
        UnitTypeId.ENGINEERINGBAY,
        UnitTypeId.MARINE,
        UnitTypeId.STARPORTREACTOR,
        UnitTypeId.MARINE,
        UpgradeId.TERRANINFANTRYWEAPONSLEVEL1,
        UnitTypeId.BARRACKS,
        UnitTypeId.BARRACKS,
        UpgradeId.TERRANINFANTRYARMORSLEVEL1,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.MARINE,
        UnitTypeId.SIEGETANK,
        UnitTypeId.MEDIVAC,
        UnitTypeId.MEDIVAC,
        UpgradeId.COMBATSHIELD,
        UnitTypeId.BARRACKSREACTOR,
        UnitTypeId.BARRACKSREACTOR,
        UnitTypeId.REFINERY,
        UnitTypeId.REFINERY,
        UnitTypeId.MEDIVAC,
        UnitTypeId.MEDIVAC,
        UnitTypeId.FACTORY,
        UnitTypeId.ARMORY,
        UnitTypeId.SIEGETANK,
        UnitTypeId.FACTORYTECHLAB,
        UnitTypeId.MEDIVAC,
        UnitTypeId.MEDIVAC,
        UnitTypeId.SIEGETANK,
        UnitTypeId.SIEGETANK,
        UnitTypeId.MEDIVAC,
        UnitTypeId.MEDIVAC,
        UnitTypeId.SIEGETANK,
        UnitTypeId.MEDIVAC,
        UnitTypeId.MEDIVAC,
        UnitTypeId.COMMANDCENTER,
        UnitTypeId.SIEGETANK,
        UnitTypeId.SIEGETANK,
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

    async def on_building_construction_complete(self, unit: Unit):
        if unit.type_id == UnitTypeId.COMMANDCENTER:
            self.LATEST_CC = unit.tag

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
                        if (
                            building.has_reactor
                            and len(self.build_order) > 0
                            and self.can_afford(UnitTypeId.HELLION)
                            and self.build_order[0] == UnitTypeId.HELLION
                        ):
                            building.train(
                                self.build_order.pop(0), can_afford_check=True
                            )

                    elif self.can_afford(UnitTypeId.SIEGETANK):
                        building.train(self.build_order.pop(0))
                    (AbilityId.RALLY_UNITS, rally_point)

            elif unit_type_id in [UnitTypeId.MEDIVAC, UnitTypeId.BANSHEE]:
                for building in self.structures(UnitTypeId.STARPORT).ready.idle:
                    if unit_type_id == UnitTypeId.MEDIVAC and self.can_afford(
                        UnitTypeId.MEDIVAC
                    ):
                        building.train(self.build_order.pop(0))
                        if (
                            building.has_reactor
                            and len(self.build_order) > 0
                            and self.can_afford(UnitTypeId.MEDIVAC)
                            and self.build_order[0] == UnitTypeId.MEDIVAC
                        ):
                            building.train(
                                self.build_order.pop(0), can_afford_check=True
                            )
                    elif self.can_afford(UnitTypeId.BANSHEE):
                        building.train(self.build_order.pop(0))

                    (AbilityId.RALLY_UNITS, rally_point)
            else:
                # If next unit is a structure
                if unit_type_id == UnitTypeId.SUPPLYDEPOT:
                    depot_placement_positions = self.main_base_ramp_depot_positions()

                    finished_depots = self.structures(
                        UnitTypeId.SUPPLYDEPOT
                    ) | self.structures(UnitTypeId.SUPPLYDEPOTLOWERED)

                    if finished_depots:
                        depot_placement_positions = {
                            d
                            for d in depot_placement_positions
                            if finished_depots.closest_distance_to(d) > 1
                        }

                    if len(depot_placement_positions) > 0:
                        target_depot_location = depot_placement_positions.pop()
                        if self.structures(UnitTypeId.SUPPLYDEPOT).amount == 0:
                            worker = self.get_first_scv()
                        else:
                            worker = self.select_build_worker(target_depot_location)

                        await self.build_structure(
                            UnitTypeId.SUPPLYDEPOT,
                            target_depot_location,
                            worker=worker,
                        )
                    else:
                        self.WALL_DONE = True
                        await self.build_structure(UnitTypeId.SUPPLYDEPOT)

                elif (
                    self.structures(UnitTypeId.BARRACKS).amount == 0
                    and self.supply_used <= 16
                ):
                    await self.build_structure(
                        UnitTypeId.BARRACKS,
                        self.main_base_ramp.barracks_correct_placement,
                        worker=self.get_first_scv(),
                    )

                elif (
                    unit_type_id == UnitTypeId.REFINERY
                    and self.already_pending(UnitTypeId.REFINERY) == 0
                ):
                    for vg in self.vespene_geyser.closer_than(
                        10, self.structures.by_tag(self.LATEST_CC)
                    ):
                        worker = self.select_build_worker(vg.position)
                        if worker is None:
                            return

                        worker.build(UnitTypeId.REFINERY, vg)
                        # Only build 1 gas at a time
                        return
                elif (
                    unit_type_id == UnitTypeId.COMMANDCENTER
                    and self.already_pending(UnitTypeId.COMMANDCENTER) == 0
                    and await self.get_next_expansion() is not None
                ):
                    # TODO build 3rd cc on highground and move it after
                    await self.expand_now()

                elif unit_type_id == UnitTypeId.BARRACKSREACTOR:
                    rax = (
                        self.structures(UnitTypeId.BARRACKS)
                        .filter(lambda rax: not rax.has_add_on)
                        .first
                    )
                    if not rax.has_add_on and not await self.can_place_single(
                        UnitTypeId.SUPPLYDEPOT, rax.position.offset((2.5, -0.5))
                    ):
                        rax(AbilityId.LIFT_BARRACKS)
                    else:
                        rax(AbilityId.BUILD_REACTOR_BARRACKS)

                elif unit_type_id == UnitTypeId.BARRACKSTECHLAB:
                    rax = (
                        self.structures(UnitTypeId.BARRACKS)
                        .filter(lambda rax: not rax.has_add_on)
                        .first
                    )
                    if not rax.has_add_on and not await self.can_place_single(
                        UnitTypeId.SUPPLYDEPOT, rax.position.offset((2.5, -0.5))
                    ):
                        rax(AbilityId.LIFT_BARRACKS)
                    else:
                        rax(AbilityId.BUILD_TECHLAB_BARRACKS)

                elif (
                    unit_type_id == UnitTypeId.FACTORYREACTOR
                    and self.structures(UnitTypeId.BARRACKS).amount == 1
                    and self.structures(UnitTypeId.FACTORY).amount == 1
                ):
                    rax = self.structures(UnitTypeId.BARRACKS).first
                    factory = self.structures(UnitTypeId.FACTORY).first

                    self.swap_add_ons(rax, factory)

                elif (
                    unit_type_id == UnitTypeId.FACTORYREACTOR
                    and self.structures(UnitTypeId.BARRACKS).amount == 3
                    and self.structures(UnitTypeId.FACTORY).amount == 1
                ):
                    factory = (
                        self.structures(UnitTypeId.FACTORY)
                        .filter(lambda factory: not factory.has_add_on)
                        .first
                    )
                    if not factory.has_add_on and not await self.can_place_single(
                        UnitTypeId.SUPPLYDEPOT, rax.position.offset((2.5, -0.5))
                    ):
                        rax(AbilityId.LIFT_FACTORY)
                    else:
                        rax(AbilityId.BUILD_REACTOR_FACTORY)

                # elif unit_type_id == UnitTypeId.FACTORYTECHLAB:
                #     factory = (
                #         self.structures(UnitTypeId.FACTORY)
                #         .filter(lambda factory: not factory.has_add_on)
                #         .first
                #     )
                #     if not factory.has_add_on and not await self.can_place_single(
                #         UnitTypeId.SUPPLYDEPOT, rax.position.offset((2.5, -0.5))
                #     ):
                #         rax(AbilityId.LIFT_FACTORY)
                #     else:
                #         rax(AbilityId.BUILD_REACTOR_FACTORY)

                elif unit_type_id == UnitTypeId.STARPORTTECHLAB:
                    rax = (
                        self.structures(UnitTypeId.BARRACKS)
                        .filter(lambda rax: rax.has_tech_lab)
                        .first
                    )
                    starport = self.structures(UnitTypeId.STARPORT).first

                    self.swap_add_ons(rax, starport)

                elif unit_type_id == UnitTypeId.STARPORTREACTOR:
                    factory = (
                        self.structures(UnitTypeId.FACTORY)
                        .filter(lambda factory: factory.has_reactor)
                        .first
                    )

                    starport = self.structures(UnitTypeId.STARPORT).first

                    self.swap_add_ons(factory, starport)

                elif unit_type_id == UpgradeId.BANSHEECLOAK:
                    port_tech_lab = self.structures(UnitTypeId.STARPORTTECHLAB).first
                    port_tech_lab(AbilityId.RESEARCH_BANSHEECLOAKINGFIELD)

                elif (
                    unit_type_id == UpgradeId.STIMPACK
                    or unit_type_id == UpgradeId.COMBATSHIELD
                ):
                    rax_tech_lab = self.structures(UnitTypeId.BARRACKSTECHLAB).first
                    rax_tech_lab(unit_type_id)

                elif (
                    unit_type_id == UpgradeId.TERRANINFANTRYARMORSLEVEL1
                    or unit_type_id == UpgradeId.TERRANINFANTRYWEAPONSLEVEL1
                ):
                    ebay = self.structures(UnitTypeId.ENGINEERINGBAY).idle.first
                    ebay(unit_type_id)

                elif not self.already_pending(unit_type_id):
                    await self.build_structure(unit_type_id)

    async def rally_workers_and_mules(self):
        for cc in self.townhalls:
            if not self.LATEST_CC:
                self.LATEST_CC = cc.tag

            if not self.FIRST_SCV_TAG:
                cc(AbilityId.RALLY_WORKERS, self.main_base_ramp_depot_positions()[0])
            else:
                mfs = self.mineral_field.closer_than(10, cc)
                if mfs:
                    mf = max(mfs, key=lambda x: x.mineral_contents)
                    cc(AbilityId.RALLY_WORKERS, mf)
                    cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf, can_afford_check=True)

    async def build_order_on_step(self, iteration: int):
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

        await super().on_step(iteration)

        if len(self.build_order) == 0:
            f = open("data/TvZStandard.txt", "w")
            f.write(
                f"Build order {self.MIXIN_NAME} ended in {self.time_formatted} with supply {self.supply_used}"
            )
            f.close()

            print(
                f"Build order {self.MIXIN_NAME} ended in {self.time_formatted} with supply {self.supply_used}"
            )
            return True
        else:
            return False
