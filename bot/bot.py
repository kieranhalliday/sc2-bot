import random
from bot.build_orders.TvT_Standard import TvTStandardBuildOrderMixin
from bot.macro.fallback_macro_mixin import FallbackMacroMixin
from bot.micro.micro_bot import MicroBotMixin
from bot.reactive_bot import ReactiveBotMixin
from sc2.bot_ai import Race
from sc2.data import Result


class CompetitiveBot(
    FallbackMacroMixin, MicroBotMixin, ReactiveBotMixin, TvTStandardBuildOrderMixin
):
    NAME: str = "ArchonBot"
    RACE: Race = Race.Terran
    build_order_finished = False

    tvt_build_orders = [TvTStandardBuildOrderMixin]
    tvp_build_orders = []
    tvz_build_orders = []

    chosen_build_order = None

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
        if self.enemy_race == Race.Terran:
            self.chosen_build_order = random.choice(self.tvt_build_orders)
        elif self.enemy_race == Race.Protoss:
            self.chosen_build_order = random.choice(self.tvp_build_orders)
        elif self.enemy_race == Race.Zerg:
            self.chosen_build_order = random.choice(self.tvz_build_orders)
        else:
            self.build_order_finished = True

        if self.build_order_finished or not self.chosen_build_order:
            await self.on_step_fallback_macro(iteration)
        else:
            # try:
            self.build_order_finished = await self.chosen_build_order.on_step(
                self, iteration
            )
            # except Exception as e:
            #     # Something failed, end build order
            #     print("Build order failed ", e)
            #     self.build_order_finished = True

        await self.on_step_micro(iteration)

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
        print(result)
