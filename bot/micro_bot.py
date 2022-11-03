import random
from bot.micro.reaper_micro import ReaperMicroMixin
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


## Bot to handle micro behaviors
## Desgined to be combined with the MacroBot
## and extended in the main bot class
class MicroBotMixin(ReaperMicroMixin):
    NAME: str = "MicroBot"

    async def fight(self):
        if self.supply_army > 50:
            for u in self.units().filter(
                lambda unit: unit.type_id != UnitTypeId.SCV
                and unit.type_id != UnitTypeId.MULE
            ):

                possible_attack_locations = self.enemy_start_locations

                if self.all_enemy_units:
                    possible_attack_locations.append(self.all_enemy_units.center)

                u.attack(random.choice(possible_attack_locations))

    async def tank_micro(self):
        siege_tanks = self.units(UnitTypeId.SIEGETANK) | self.units(
            UnitTypeId.SIEGETANKSIEGED
        )
        for st in siege_tanks.idle:
            st(AbilityId.SIEGEMODE_SIEGEMODE)

    async def on_step_micro(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        await self.tank_micro()
        await self.reaper_micro(iteration)
        await self.fight()
