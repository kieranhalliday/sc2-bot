import numpy as np
from pysc2.agents import base_agent
from pysc2.lib import features, units
import sc2.game_info
from sc2.game_info import *

class HelperBot(base_agent.BaseAgent):

    def get_all_my_army_units(self, obs):
        return [
            unit
            for unit in obs.observation.raw_units
            if unit.unit_type != units.Terran.SCV
            and unit.unit_type != units.Terran.MULE
            and unit.alliance == features.PlayerRelative.SELF
        ]

    def get_all_enemy_army_units(self, obs):
        return [
            unit
            for unit in obs.observation.raw_units
            if unit.unit_type != units.Terran.SCV
            and unit.unit_type != units.Terran.MULE
            and unit.alliance == features.PlayerRelative.ENEMY
        ]

    def get_my_units_by_type(self, obs, unit_type):
        return [
            unit
            for unit in obs.observation.raw_units
            if unit.unit_type == unit_type
            and unit.alliance == features.PlayerRelative.SELF
        ]

    def get_enemy_units_by_type(self, obs, unit_type):
        return [
            unit
            for unit in obs.observation.raw_units
            if unit.unit_type == unit_type
            and unit.alliance == features.PlayerRelative.ENEMY
        ]

    def get_my_completed_units_by_type(self, obs, unit_type):
        return [
            unit
            for unit in obs.observation.raw_units
            if unit.unit_type == unit_type
            and unit.build_progress == 100
            and unit.alliance == features.PlayerRelative.SELF
        ]

    def get_enemy_completed_units_by_type(self, obs, unit_type):
        return [
            unit
            for unit in obs.observation.raw_units
            if unit.unit_type == unit_type
            and unit.build_progress == 100
            and unit.alliance == features.PlayerRelative.ENEMY
        ]

    def get_distances(self, obs, units, xy):
        units_xy = [(unit.x, unit.y) for unit in units]
        return np.linalg.norm(np.array(units_xy) - np.array(xy), axis=1)
