from typing import Dict, List, Optional, Tuple, Union
from bot.types.add_on_movement import AddOnMovementType, AddOnType
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class TvP3RaxBuildOrder(BotAI):
    def build_order(
        self,
    ) -> Dict[
        str,
        Union[
            Dict[str, str],
            List[
                Tuple[
                    Union[
                        str,
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
                "name": "TvP-3Rax-BuildOrder",
                "goal_time_sec": 396,
            },
            "build": [
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.BARRACKS],
                [UnitTypeId.REFINERY],
                [UnitTypeId.MARINE],
                [UnitTypeId.COMMANDCENTER],
                [UnitTypeId.BARRACKSREACTOR],
                [UnitTypeId.BARRACKS],
                [UnitTypeId.BARRACKS],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.BARRACKSTECHLAB],
                [UnitTypeId.BARRACKSTECHLAB],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.MARINE],
                [AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK],
                [AbilityId.RESEARCH_COMBATSHIELD],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.REFINERY],
                [UnitTypeId.MARAUDER],
                [UnitTypeId.MARAUDER],
                ["attack"],
                [UnitTypeId.ENGINEERINGBAY],
                [UnitTypeId.SUPPLYDEPOT],
                [AbilityId.RESEARCH_CONCUSSIVESHELLS],
                [UnitTypeId.FACTORY],
                [UnitTypeId.MISSILETURRET],
                [AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL1],
                [UnitTypeId.COMMANDCENTER],
                [UnitTypeId.REFINERY],
                [UnitTypeId.REFINERY],
                [UnitTypeId.STARPORT],
                [UnitTypeId.FACTORYREACTOR],
                [UnitTypeId.MARAUDER],
                [UnitTypeId.MARAUDER],
                [UnitTypeId.BARRACKS],
                [UnitTypeId.BARRACKS],
                [UnitTypeId.MARAUDER],
                [UnitTypeId.MARAUDER],
                [(UnitTypeId.STARPORT, AddOnMovementType.LIFT, AddOnType.EMPTY)],
                [(UnitTypeId.FACTORY, AddOnMovementType.LIFT, AddOnType.REACTOR)],
                [
                    (
                        UnitTypeId.STARPORTFLYING,
                        AddOnMovementType.LAND,
                        AddOnType.REACTOR,
                    )
                ],
                [(UnitTypeId.FACTORYFLYING, AddOnMovementType.LAND, AddOnType.EMPTY)],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.FACTORYREACTOR],
                [UnitTypeId.MARAUDER],
                [UnitTypeId.MARAUDER],
                [UnitTypeId.BARRACKSREACTOR],
                "defend",
            ],
        }
