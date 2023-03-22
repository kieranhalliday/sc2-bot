import random
from typing import Optional, Union
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class MacroHelpersMixin(BotAI):
    army_unit_type_ids = [
        UnitTypeId.REAPER,
        UnitTypeId.MARINE,
        UnitTypeId.MARAUDER,
        UnitTypeId.GHOST,
        UnitTypeId.HELLION,
        UnitTypeId.WIDOWMINE,
        UnitTypeId.CYCLONE,
        UnitTypeId.SIEGETANK,
        UnitTypeId.THOR,
        UnitTypeId.VIKING,
        UnitTypeId.MEDIVAC,
        UnitTypeId.LIBERATOR,
        UnitTypeId.RAVEN,
        UnitTypeId.BANSHEE,
        UnitTypeId.BATTLECRUISER,
    ]
    """Holds functions that are not specifically used
    in the on step function"""

    def already_pending(self, unit_type, structures=None):
        """Checks if a unit type is already pending
        If a list of structures is provided, it only checks if a unit is building from those structures
        Example::

        if self.townhalls:
            cc = self.townhalls[0]
            already_pending_result = self.already_pending(UnitTypeId.SCV, [cc])
        """
        ability = self.game_data.units[unit_type.value].creation_ability
        unitAttributes = self.game_data.units[unit_type.value].attributes
        structures_to_check = structures or self.structures

        if 8 not in unitAttributes and any(
            o.ability == ability for w in (self.units.not_structure) for o in w.orders
        ):
            return sum(
                [
                    o.ability == ability
                    for w in (self.units - self.workers)
                    for o in w.orders
                ]
            )
        # following checks for unit production in a building queue, like queen, also checks if hatch is morphing to LAIR
        elif any(
            o.ability.id == ability.id for w in (structures_to_check) for o in w.orders
        ):
            return sum(
                [
                    o.ability.id == ability.id
                    for w in (structures_to_check)
                    for o in w.orders
                ]
            )
        elif any(o.ability == ability for w in self.workers for o in w.orders):
            return sum([o.ability == ability for w in self.workers for o in w.orders])
        return 0

    async def build_structure(
        self, structure_id, position=None, can_afford_check=True, worker=None
    ):
        army_building = structure_id in [
            UnitTypeId.BARRACKS,
            UnitTypeId.FACTORY,
            UnitTypeId.STARPORT,
        ]

        if position == None:
            # if army_building:
            #     near = self.main_base_ramp.barracks_correct_placement.to2
            # elif:
            if len(self.townhalls) > 0:
                near = self.start_location.towards(
                    self.game_info.map_center, 3
                ).random_on_distance(3)
            else:
                near = self.all_own_units.random.position

            position = await self.find_placement(
                structure_id,
                near,
                placement_step=4,
                max_distance=20,
                addon_place=army_building,
            )
            if position is None:
                print("No position found for ", structure_id)
                return

        if worker is None:
            # If no worker is supplied, select closest worker
            worker = self.select_build_worker(position)
            if worker is None:
                return

        if await self.can_place_single(structure_id, position):
            worker.build(structure_id, position, can_afford_check=can_afford_check)

    async def find_placement(
        self,
        building: Union[UnitTypeId, AbilityId],
        near: Point2,
        max_distance: int = 20,
        random_alternative: bool = True,
        placement_step: int = 2,
        addon_place: bool = False,
    ) -> Optional[Point2]:
        """Finds a placement location for building.

        Example::

            if self.townhalls:
                cc = self.townhalls[0]
                depot_position = await self.find_placement(UnitTypeId.SUPPLYDEPOT, near=cc)

        :param building:
        :param near:
        :param max_distance:
        :param random_alternative:
        :param placement_step:
        :param addon_place:"""

        assert isinstance(building, (AbilityId, UnitTypeId))
        assert isinstance(near, Point2), f"{near} is no Point2 object"

        if isinstance(building, UnitTypeId):
            building = self.game_data.units[building.value].creation_ability.id

        if await self.can_place_single(building, near) and (
            not addon_place
            or await self.can_place_single(
                UnitTypeId.SUPPLYDEPOT, near.offset((2.5, -0.5))
            )
        ):
            return near

        if max_distance == 0:
            return None

        for distance in range(placement_step, max_distance, placement_step):
            possible_positions = [
                Point2(p).offset(near).to2
                for p in (
                    [
                        (dx, -distance)
                        for dx in range(-distance, distance + 1, placement_step)
                    ]
                    + [
                        (dx, distance)
                        for dx in range(-distance, distance + 1, placement_step)
                    ]
                    + [
                        (-distance, dy)
                        for dy in range(-distance, distance + 1, placement_step)
                    ]
                    + [
                        (distance, dy)
                        for dy in range(-distance, distance + 1, placement_step)
                    ]
                )
            ]
            res = await self.client._query_building_placement_fast(
                building, possible_positions
            )
            # Filter all positions if building can be placed
            possible = [p for r, p in zip(res, possible_positions) if r]

            # The find add on place logic did not work in the sc2 version of this function
            if addon_place:
                # Filter remaining positions if addon can be placed
                res = []

                for p in possible:
                    res.append(
                        await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, p.offset((2.5, -0.5))
                        )
                    )
                possible = [p for r, p in zip(res, possible) if r]

            if not possible:
                continue

            if random_alternative:
                return random.choice(possible)
            return min(possible, key=lambda p: p.distance_to_point2(near))
        return None

    def unit_build_progress(self, structure_building_unit, unit_type_id):
        """Finds build progress of specific type of unit from specific building.
        :param structure_building_unit structure building the unit:
        :param unit_type_id unit type id being produced:
        """
        creationAbilityID = self.game_data.units[
            unit_type_id.value
        ].creation_ability.exact_id
        for order in structure_building_unit.orders:
            if order.ability.exact_id == creationAbilityID:
                return order.progress
        return 0
