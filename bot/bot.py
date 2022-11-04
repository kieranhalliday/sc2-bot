from bot.macro_bot import MacroBotMixin
from bot.micro_bot import MicroBotMixin
from sc2.bot_ai import Race
from sc2.data import Result


class CompetitiveBot(MacroBotMixin, MicroBotMixin):
    NAME: str = "ArchonBot"
    RACE: Race = Race.Terran

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
        await self.on_step_macro(iteration)
        await self.on_step_micro(iteration)

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
        print(result)
