from sc2.position import Point2, Point3
from sc2.unit import Unit


class Helpers:

    # this checks if a ground unit can walk on a Point2 position
    def inPathingGrid(pos, pathing_grid):
        # returns True if it is possible for a ground unit to move to pos - doesnt seem to work on ramps or near edges
        assert isinstance(pos, (Point2, Point3, Unit))
        pos = pos.position.to2.rounded
        return pathing_grid[(pos)] != 0

    @staticmethod
    def neighbors4(position, distance=1):
        p = position
        d = distance
        return {
            Point2((p.x - d, p.y)),
            Point2((p.x + d, p.y)),
            Point2((p.x, p.y - d)),
            Point2((p.x, p.y + d)),
        }

    @staticmethod
    def neighbors8(position, distance=1):
        p = position
        d = distance
        return Helpers.neighbors4(position, distance) | {
            Point2((p.x - d, p.y - d)),
            Point2((p.x - d, p.y + d)),
            Point2((p.x + d, p.y - d)),
            Point2((p.x + d, p.y + d)),
        }