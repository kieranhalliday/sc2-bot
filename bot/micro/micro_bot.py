import random

import numpy as np
from bot.helper.helper_bot import HelperBot
from pysc2.lib import actions
from sc2.bot_ai import BotAI

## Bot to handle micro behaviors
## Desgined to be combined with the MacroBot
## and extended in the main bot class
class MicroBotMixin(HelperBot, BotAI):
    NAME: str = "MicroBot"

    def _fight(self, obs):
        army = self.get_all_my_army_units(obs)
        enemy_army = self.get_all_enemy_army_units(obs)
        if len(army) > 0 and len(enemy_army) > 0:
            random_enemy_unit = random.choice(enemy_army)
            attack_xy = (random_enemy_unit.x, random_enemy_unit.y)
            distances = self.get_distances(obs, army, attack_xy)
            army_unit = army[np.argmax(distances)]
            x_offset = random.randint(-4, 4)
            y_offset = random.randint(-4, 4)
            return actions.RAW_FUNCTIONS.Attack_pt(
                "now", army_unit.tag, (attack_xy[0] + x_offset, attack_xy[1] + y_offset)
            )
        return actions.RAW_FUNCTIONS.no_op()

