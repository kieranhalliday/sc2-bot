from typing import Literal
from bot.helpers import Helpers
from sc2.bot_ai import BotAI
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId


class TankMicroMixin(BotAI):
    NAME: str = "TankMicro"

    async def tank_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        tanks = self.units(UnitTypeId.SIEGETANK)
        if mode == "defend":
            for st in tanks.idle:
                st(AbilityId.SIEGEMODE_SIEGEMODE)
        else:
            for st in tanks:
                if not self.enemy_units.visible:
                    st(AbilityId.UNSIEGE_UNSIEGE)
                else:
                    st(AbilityId.SIEGEMODE_SIEGEMODE)
