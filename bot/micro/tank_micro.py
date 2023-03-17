from typing import Literal
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


class TankMicroMixin(BotAI):
    NAME: str = "TankMicro"

    async def tank_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        tanks = self.units(UnitTypeId.SIEGETANK)
        if mode == "defend":
            for tank in tanks.idle:
                tank(AbilityId.SIEGEMODE_SIEGEMODE)
        else:
            for tank in tanks.idle:
                if (
                    len(self.enemy_units) > 0
                    and self.enemy_units.closest_distance_to(tank.position) < 14
                ):
                    tank(AbilityId.SIEGEMODE_SIEGEMODE)
                else:
                    print("unseiging tank")
                    tank(AbilityId.UNSIEGE_UNSIEGE)
