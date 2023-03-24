from typing import Dict, List, Optional, Tuple, Union
from bot.types.add_on_movement import AddOnMovementType, AddOnType
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


# TODO
# Scout with second scv
# Saturate gas until factory
# Pull out of gas
class TvTStandardBuildOrder(BotAI):
    def build_order(
        self,
    ) -> Dict[
        str,
        Union[
            Dict[str, str],
            List[
                Tuple[
                    Union[
                        UnitTypeId,
                        AbilityId,
                        Tuple[UnitTypeId, AddOnMovementType, AddOnType],
                    ],
                    Optional[Point2],
                    Optional[bool],
                ]
            ],
        ],
    ]:
        main_base_corner_depots = list(self.main_base_ramp.corner_depots)
        return {
            "meta": {
                "name": "TvTStandardBuildOrder",
                "goal_time_sec": 297,
            },
            "build": [
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.BARRACKS],
                [UnitTypeId.REFINERY],
                [UnitTypeId.REFINERY],
                [UnitTypeId.REAPER],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.FACTORY],
                [UnitTypeId.REAPER],
                [UnitTypeId.COMMANDCENTER],
                [UnitTypeId.HELLION],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.REAPER],
                [UnitTypeId.STARPORT],
                [UnitTypeId.HELLION],
                [UnitTypeId.BARRACKSREACTOR],
                [UnitTypeId.REFINERY],
                [UnitTypeId.FACTORYTECHLAB],
                [UnitTypeId.STARPORTTECHLAB],
                [UnitTypeId.CYCLONE],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.RAVEN],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.SIEGETANK],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.RAVEN],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.SIEGETANK],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
            ],
        }
