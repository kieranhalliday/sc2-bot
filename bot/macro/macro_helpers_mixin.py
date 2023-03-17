import random
from typing import Optional, Union

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class MacroHelpersMixin(BotAI):
    NAME: str = "MacroHelpers"

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

    def select_build_worker(self, pos, force=False, excludeTags=[]):
        for worker in self.workers:
            if (
                not worker.orders
                or len(worker.orders) == 1
                and worker.orders[0].ability.id
                in [AbilityId.MOVE, AbilityId.HARVEST_GATHER, AbilityId.HARVEST_RETURN]
                and worker.tag not in excludeTags
            ):
                return worker
        return self.workers.random if force else None

    async def build_structure(self, structure_id, position=None, can_afford_check=True):
        army_building = structure_id in [
            UnitTypeId.BARRACKS,
            UnitTypeId.FACTORY,
            UnitTypeId.STARPORT,
        ]

        if position == None:
            if army_building:
                near = self.main_base_ramp.barracks_correct_placement.to2
            elif len(self.townhalls) > 0:
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

        worker = self.select_build_worker(position)
        if worker is None:
            return

        if await self.can_place_single(structure_id, position):
            worker.build(structure_id, position, can_afford_check=can_afford_check)

    def already_pending(self, unit_type):
        ability = self.game_data.units[unit_type.value].creation_ability
        unitAttributes = self.game_data.units[unit_type.value].attributes

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
            o.ability.id == ability.id for w in (self.units.structure) for o in w.orders
        ):
            return sum(
                [
                    o.ability.id == ability.id
                    for w in (self.units.structure)
                    for o in w.orders
                ]
            )
        elif any(o.ability == ability for w in self.workers for o in w.orders):
            return sum([o.ability == ability for w in self.workers for o in w.orders])
        return 0
