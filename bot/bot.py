from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit
from sc2.units import Units


class CompetitiveBot(BotAI):
    NAME: str = "CompetitiveBot"

    RACE: Race = Race.Terran
    build_type = "BIO"

    async def build_structure(self, structure_id, position=None, can_afford_check=True):
        # Addons for production buildings
        addon_place = structure_id in [
            UnitTypeId.BARRACKS,
            UnitTypeId.FACTORY,
            UnitTypeId.STARPORT,
        ]

        structure_position = position

        if structure_position == None:
            if len(self.townhalls) == 0:
                return

            structure_position = await self.find_placement(
                structure_id, self.townhalls.random.position
            )
            # No position was found
            if structure_position is None:
                return

        worker = self.select_build_worker(structure_position)
        if worker is None:
            return

        if await self.can_place_single(structure_id, structure_position):
            worker.build(
                structure_id, structure_position, can_afford_check=can_afford_check
            )

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

    async def build_depots(self):
        ## TODO: build depots that aren't in the main wall
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
            and not self.already_pending(UnitTypeId.SUPPLYDEPOT)
            and self.supply_left < 5
        ):
            if len(depot_placement_positions) > 0:
                target_depot_location = depot_placement_positions.pop()
                await self.build_structure(
                    UnitTypeId.SUPPLYDEPOT, target_depot_location
                )
            else:
                await self.build_structure(UnitTypeId.SUPPLYDEPOT)

        await self.handle_depot_height()

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

    async def build_production(self):
        # 1-1-1
        # 3-1-1
        # 5-1-1
        # 5-2-1
        # 8-2-1
        production_build_order = []
        if self.build_type == "BIO":
            production_build_order = [
                "b",
                "f",
                "s",
                "b",
                "b",
                "b",
                "b",
                "f",
                "b",
                "b",
                "b",
            ]
            production_buildings = (
                self.structures(UnitTypeId.BARRACKS)
                | self.structures(UnitTypeId.FACTORY)
                | self.structures(UnitTypeId.STARPORT)
            )

            ccs = self.townhalls.ready

            if len(ccs) <= 1 and len(production_buildings) <= 3:
                # If no buildings build barracks
                if len(production_buildings) == 0 and not self.already_pending(
                    UnitTypeId.BARRACKS
                ):
                    await self.build_structure(
                        UnitTypeId.BARRACKS,
                        self.main_base_ramp.barracks_correct_placement,
                    )
                elif len(production_buildings) == 1 and not self.already_pending(
                    UnitTypeId.FACTORY
                ):
                    await self.build_structure(UnitTypeId.FACTORY)
                elif len(production_buildings) == 2 and not self.already_pending(
                    UnitTypeId.STARPORT
                ):
                    await self.build_structure(UnitTypeId.STARPORT)

        elif self.build_type == "MECH":
            pass

    async def build_units(self):
        for rax in self.structures(UnitTypeId.BARRACKS).ready:
            if rax.is_idle and self.can_afford(UnitTypeId.MARINE):
                rax.train(UnitTypeId.MARINE)

        for factory in self.structures(UnitTypeId.FACTORY).ready:
            if factory.is_idle and self.can_afford(UnitTypeId.HELLION):
                factory.train(UnitTypeId.HELLION)

        for starport in self.structures(UnitTypeId.STARPORT).ready:
            if starport.is_idle and self.can_afford(UnitTypeId.MEDIVAC):
                starport.train(UnitTypeId.MEDIVAC)

    async def fight(self):
        if self.supply_army > 20:
            for u in self.units().filter(lambda unit: unit.type_id != UnitTypeId.SCV):
                u.attack(self.enemy_start_locations[0])

    async def finish_buildings_under_construction(self):
        structures_to_finish = self.structures_without_construction_SCVs()
        for structure in structures_to_finish:
            await self.build_structure(structure.type_id, structure.position)

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        # Macro cycle
        if iteration % 25 == 0:
            await self.distribute_workers()

        await self.build_workers()
        await self.build_depots()
        await self.build_refineries()
        await self.expand()
        await self.build_production()
        await self.finish_buildings_under_construction()
        await self.build_units()
        await self.fight()

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
