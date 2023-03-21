import random
from bot.build_orders.TvP_Standard import TvPStandardBuildOrderMixin
from bot.build_orders.TvT_Standard import TvTStandardBuildOrderMixin
from bot.build_orders.TvZ_Standard import TvZStandardBuildOrderMixin
from bot.macro.fallback_macro_mixin import FallbackMacroMixin
from bot.micro.micro_bot import MicroBotMixin
from bot.reactive_bot import ReactiveBotMixin
from sc2.bot_ai import Race
from sc2.data import Result


class CompetitiveBot(
    FallbackMacroMixin,
    MicroBotMixin,
    ReactiveBotMixin,
):
    NAME: str = "Reynor's Raider"
    RACE: Race = Race.Terran
    build_order_finished = False

    tvt_build_orders = [TvTStandardBuildOrderMixin]
    tvp_build_orders = [TvPStandardBuildOrderMixin]
    tvz_build_orders = [TvZStandardBuildOrderMixin]

    chosen_build_order = None

    def extend_bot_with_chosen_build_order_mixin(self):
        """Apply mixins to a class instance after creation"""
        base_cls = self.__class__
        base_cls_name = self.__class__.__name__
        self.__class__ = type(base_cls_name, (base_cls, self.chosen_build_order), {})

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")
        if self.enemy_race == Race.Terran:
            self.chosen_build_order = random.choice(self.tvt_build_orders)
        elif self.enemy_race == Race.Protoss:
            self.chosen_build_order = random.choice(self.tvp_build_orders)
        elif self.enemy_race == Race.Zerg:
            self.chosen_build_order = random.choice(self.tvz_build_orders)
        elif self.enemy_race == Race.Random:
            self.chosen_build_order = random.choice(
                self.tvt_build_orders + self.tvp_build_orders + self.tvz_build_orders
            )
        else:
            self.build_order_finished = True

        print(f"Chosen bot {self.chosen_build_order.BUILD_ORDER_NAME}")
        self.extend_bot_with_chosen_build_order_mixin()

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """

        if self.build_order_finished or not self.chosen_build_order:
            await self.on_step_fallback_macro(iteration)
        else:
            # try:
            self.build_order_finished = (
                await self.chosen_build_order.build_order_on_step(self, iteration)
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
        f = open("data/results.txt", "a")
        f.write(
            f"Build order: {self.chosen_build_order.BUILD_ORDER_NAME}. Result: {result}."
        )
        f.close()

        print(result)
