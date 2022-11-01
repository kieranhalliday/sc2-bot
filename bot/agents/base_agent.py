import random

from pysc2.lib import actions, features, units

from bot.macro.macro_bot import MacroBotMixin
from bot.micro.micro_bot import MicroBotMixin
from sc2.bot_ai import Race


class Agent(MacroBotMixin, MicroBotMixin):
    NAME: str = "ArchonBot"
    RACE: Race = Race.Terran

    actions = (
        # "build_add_ons",
        # "build_depots",
        # "build_production",
        # "build_refineries",
        # "build_workers",
        # "distribute_workers",
        # "expand",
        "fight",
        # "finish_buildings_under_construction",
        # "train_units",
    )

    def step(self, obs):
        super(Agent, self).step(obs)

    # async def build_add_ons(self, obs):
    #     return await self._build_add_ons(obs)

    # async def build_depots(self, obs):
    #     return await self._build_depots(obs)

    # async def build_production(self, obs):
    #     return await self._build_production(obs)

    # async def build_refineries(self, obs):
    #     return await self._build_refineries(obs)

    # async def build_workers(self, obs):
    #     return await self._build_workers(obs)

    # async def distribute_workers(self, obs):
    #     return await self._distribute_workers(obs)

    # async def expand(self, obs):
    #     return await self._expand(obs)

    def fight(self, obs):
        return self._fight(obs)

    # async def finish_buildings_under_construction(self, obs):
    #     return await self._finish_buildings_under_construction(obs)

    # async def train_units(self, obs):
    #     return await self._train_units(obs)