import enum
from typing import Dict, List, Optional, Tuple, Union

from bot.types.add_on_movement import AddOnMovement
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class TvZStandardBuildOrder(BotAI):
    def build_order(
        self,
    ) -> Dict[
        str,
        Union[
            Dict[str, str],
            List[
                Tuple[
                    Union[UnitTypeId, AbilityId, AddOnMovement],
                    Optional[Point2],
                    Optional[bool],
                ]
            ],
        ],
    ]:
        main_base_corner_depots = list(self.main_base_ramp.corner_depots)
        return {
            "meta": {"name": "TvZStandardBuildOrder"},
            "build": [
                # [Unit Id, position, first worker flag]
                [UnitTypeId.SUPPLYDEPOT, main_base_corner_depots[0], True],
                [
                    UnitTypeId.BARRACKS,
                    self.main_base_ramp.barracks_correct_placement,
                    True,
                ],
                [UnitTypeId.REFINERY],
                [UnitTypeId.REAPER],
                [UnitTypeId.COMMANDCENTER],
                [UnitTypeId.SUPPLYDEPOT, main_base_corner_depots[1]],
                [UnitTypeId.MARINE],
                [UnitTypeId.FACTORY],
                [UnitTypeId.BARRACKSREACTOR],
                [UnitTypeId.COMMANDCENTER],
                [UnitTypeId.STARPORT],
                [UnitTypeId.REFINERY],
                [AddOnMovement.BARRACKS_LEAVE_REACTOR],
                [AddOnMovement.FACTORY_LIFT_EMPTY],
                [AddOnMovement.FACTORY_LAND_REACTOR],
                [AddOnMovement.BARRACKS_LAND_EMPTY],
                [UnitTypeId.HELLION],
                [UnitTypeId.HELLION],
                [UnitTypeId.BARRACKSTECHLAB],
                [UnitTypeId.HELLION],
                [UnitTypeId.HELLION],
                [AddOnMovement.STARPORT_LIFT_EMPTY],
                [AddOnMovement.BARRACKS_LEAVE_TECHLAB],
                [AddOnMovement.STARPORT_LAND_TECHLAB],
                [AddOnMovement.BARRACKS_LAND_EMPTY],
                [UnitTypeId.BANSHEE],
                [AbilityId.RESEARCH_BANSHEECLOAKINGFIELD],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.HELLION],
                [UnitTypeId.HELLION],
                [UnitTypeId.BARRACKSTECHLAB],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.HELLION],
                [UnitTypeId.HELLION],
                [UnitTypeId.MARINE],
                [AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK],
                [UnitTypeId.BANSHEE],
                [UnitTypeId.REFINERY],
                [AddOnMovement.FACTORY_LEAVE_REACTOR],
                [AddOnMovement.FACTORY_LAND_EMPTY],
                [UnitTypeId.FACTORYREACTOR],
                # One rax is built on reactor that factory left
                [UnitTypeId.BARRACKS],
                [UnitTypeId.BARRACKS],
                [UnitTypeId.SUPPLYDEPOT],
                [UnitTypeId.MARINE],
                [UnitTypeId.REFINERY],
                [UnitTypeId.ENGINEERINGBAY],
                [UnitTypeId.ENGINEERINGBAY],
                [UnitTypeId.MARINE],
                [AddOnMovement.STARPORT_LEAVE_TECHLAB],
                [AddOnMovement.STARPORT_LAND_EMPTY],
                [UnitTypeId.STARPORTREACTOR],
                [AddOnMovement.FACTORY_LEAVE_REACTOR],
                [AddOnMovement.FACTORY_LAND_TECHLAB],
                [AddOnMovement.BARRACKS_LIFT_EMPTY],
                [AddOnMovement.BARRACKS_LAND_REACTOR],
                [UnitTypeId.MARINE],
                [AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL1],
                [UnitTypeId.BARRACKS],
                [UnitTypeId.BARRACKS],
                [AbilityId.ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL1],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.MARINE],
                [UnitTypeId.SIEGETANK],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.MEDIVAC],
                [AbilityId.RESEARCH_COMBATSHIELD],
                # Fourth and Fifth barracks make their own reactors
                [UnitTypeId.BARRACKSREACTOR],
                [UnitTypeId.BARRACKSREACTOR],
                [UnitTypeId.REFINERY],
                [UnitTypeId.REFINERY],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.FACTORY],
                [UnitTypeId.ARMORY],
                [UnitTypeId.SIEGETANK],
                # Second factory makes it's own tech lab
                [UnitTypeId.FACTORYTECHLAB],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.SIEGETANK],
                [UnitTypeId.SIEGETANK],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.SIEGETANK],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.MEDIVAC],
                [UnitTypeId.COMMANDCENTER],
                [UnitTypeId.SIEGETANK],
                [UnitTypeId.SIEGETANK],
            ],
        }
