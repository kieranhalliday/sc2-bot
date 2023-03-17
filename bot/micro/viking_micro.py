from typing import Literal
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.units import Units


class VikingMicroMixin(BotAI):
    NAME: str = "VikingMicro"

    async def viking_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        vikings: Units = self.units(UnitTypeId.VIKINGFIGHTER) + self.units(
            UnitTypeId.VIKINGASSAULT
        )

        if mode == "defend":
            for v in vikings.idle:
                v.patrol(self.townhalls.first)
        else:
            for v in vikings.idle:
                flying_units = self.enemy_units.filter(lambda unit: unit.is_flying)
                if (
                    len(flying_units) > 0
                    and flying_units.closest_distance_to(v.position) < 15
                ):
                    v(AbilityId.MORPH_VIKINGFIGHTERMODE)
                else:
                    v(AbilityId.MORPH_VIKINGASSAULTMODE)
