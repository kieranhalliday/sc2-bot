from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId


## Bot to handle micro behaviors
## Desgined to be combined with the MacroBot
## and extended in the main bot class
class MicroBotMixin(BotAI):
    NAME: str = "MicroBot"

    async def fight(self):
        if self.supply_army > 50:
            for u in self.units().filter(lambda unit: unit.type_id != UnitTypeId.SCV):
                u.attack(self.enemy_start_locations[0])

    async def on_step_micro(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        await self.fight()