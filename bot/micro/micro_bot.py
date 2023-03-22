import random
from typing import Literal
from bot.micro.banshee_micro import BansheeMicroMixin
from bot.micro.hellion_micro import HellionMicroMixin

from bot.micro.marine_micro import MarineMicroMixin
from bot.micro.medivac_micro import MedivacMicroMixin
from bot.micro.raven_micro import RavenMicroMixin
from bot.micro.reaper_micro import ReaperMicroMixin
from bot.micro.tank_micro import TankMicroMixin
from bot.micro.viking_micro import VikingMicroMixin
from sc2.ids.unit_typeid import UnitTypeId


## Bot to handle micro behaviors
## Desgined to be combined with the MacroBot
## and extended in the main bot class
class MicroBotMixin(
    ReaperMicroMixin,
    MarineMicroMixin,
    TankMicroMixin,
    VikingMicroMixin,
    RavenMicroMixin,
    MedivacMicroMixin,
    BansheeMicroMixin,
    HellionMicroMixin,
):
    MODE: Literal["attack", "defend"] = "defend"

    async def fight(self):
        if self.supply_army > 100:
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
        await self.raven_micro(iteration, self.MODE)
        await self.reaper_micro(iteration, self.MODE)
        await self.marine_micro(iteration, self.MODE)
        await self.tank_micro(iteration, self.MODE)
        await self.viking_micro(iteration, self.MODE)
        await self.medivac_micro(iteration, self.MODE)
        await self.banshee_micro(iteration, self.MODE)
        await self.hellion_micro(iteration, self.MODE)
        await self.fight()
