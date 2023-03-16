import random

from bot.micro.marine_micro import MarineMicroMixin
from bot.micro.reaper_micro import ReaperMicroMixin
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId


## Bot to handle micro behaviors
## Desgined to be combined with the MacroBot
## and extended in the main bot class
class MicroBotMixin(ReaperMicroMixin, MarineMicroMixin):
    NAME: str = "MicroBot"

    async def fight(self):
        if self.supply_army > 50:
            for u in self.units().idle.filter(
                lambda unit: unit.type_id != UnitTypeId.SCV
                and unit.type_id != UnitTypeId.MULE
            ):

                possible_attack_locations = self.enemy_start_locations

                if self.all_enemy_units:
                    possible_attack_locations.append(self.all_enemy_units.center)

                u.attack(random.choice(possible_attack_locations))

    async def tank_micro(self):
        idle_tanks = self.units(UnitTypeId.SIEGETANK).idle
        for st in idle_tanks:
            st(AbilityId.SIEGEMODE_SIEGEMODE)

    async def on_step_micro(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        await self.reaper_micro(iteration)
        await self.marine_micro(iteration)
        await self.tank_micro()
        await self.fight()
