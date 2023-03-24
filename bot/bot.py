from bot.macro.build_order_mixin import BuildOrderMixin
from bot.micro.micro_bot import MicroBotMixin
from bot.reactive_bot import ReactiveBotMixin
from sc2.bot_ai import Race
from sc2.data import Result


class CompetitiveBot(MicroBotMixin, ReactiveBotMixin, BuildOrderMixin):
    NAME: str = "Raynor's Raider"
    RACE: Race = Race.Terran
    build_order_finished = False

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")
        await self.build_order_on_start()

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """

        micro_mode = await self.build_order_on_step(iteration)
        if micro_mode in ["attack", "defend"]:
            self.set_mode(micro_mode)
        await self.on_step_micro(iteration)

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
        f = open("data/results.txt", "a")
        f.write(f"Build order: {self.BUILD_ORDER_META['name']}. Result: {result}.\n")
        f.close()

        print(result)
