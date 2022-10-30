from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId


class CompetitiveBot(BotAI):
    NAME: str = "CompetitiveBot"
    """This bot's name"""

    RACE: Race = Race.Terran
    """This bot's Starcraft 2 race.
    Options are:
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """

    async def build_depots(self):
        depot_placement_positions = self.main_base_ramp.corner_depots | {
            self.main_base_ramp.depot_in_middle
        }

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
            # and self.supply_left < 3
        ):
            if len(depot_placement_positions) == 0:
                return
            # Choose any depot location
            target_depot_location = depot_placement_positions.pop()
            ws = self.workers.gathering
            if ws:  # if workers were found
                w = ws.random
                w.build(UnitTypeId.SUPPLYDEPOT, target_depot_location)

    async def build_workers(self):
        for cc in self.townhalls.ready:
            if (
                self.units(UnitTypeId.SCV).amount < self.townhalls.amount * 22
                and cc.is_idle
            ):
                cc.train(UnitTypeId.SCV)

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
        await self.distribute_workers()
        await self.build_workers()
        await self.build_depots()

    # #Out bot builds pylons :
    # await self.build_pylons()
    # #Out bot builds Assimilators :
    # await self.build_assimilators()
    # #Out bot expands
    # await self.expand()
    # #Out bot builds production buildings
    # await self.build_production_build()
    # #Out bot builds units
    # await self.build_units()
    # #Out bot fights
    # await self.fight()

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
