import random
from typing import Literal

from bot.micro.marine_micro import MarineMicroMixin
from bot.micro.reaper_micro import ReaperMicroMixin
from bot.micro.tank_micro import TankMicroMixin
from bot.micro.viking_micro import VikingMicroMixin
from sc2.ids.unit_typeid import UnitTypeId


## Bot to handle micro behaviors
## Desgined to be combined with the MacroBot
## and extended in the main bot class
class MicroBotMixin(
    ReaperMicroMixin, MarineMicroMixin, TankMicroMixin, VikingMicroMixin
):
    MIXIN_NAME: str = "MicroBot"
    MODE: Literal["attack", "defend"] = "defend"

    async def fight(self):
        if self.supply_army > 50:
            self.MODE = "attack"
            for u in self.units().idle.filter(
                lambda unit: unit.type_id != UnitTypeId.SCV
                and unit.type_id != UnitTypeId.MULE
            ):
                possible_attack_locations = self.enemy_start_locations

                if self.all_enemy_units:
                    possible_attack_locations.append(self.all_enemy_units.center)

                u.attack(random.choice(possible_attack_locations))
        else:
            self.MODE = "defend"

    async def on_step_micro(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        await self.reaper_micro(iteration, self.MODE)
        await self.marine_micro(iteration, self.MODE)
        await self.tank_micro(iteration, self.MODE)
        await self.viking_micro(iteration, self.MODE)
        await self.fight()
