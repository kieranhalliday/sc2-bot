from bot.agents.base_agent import Agent
from pysc2.lib import units

from bot.q_learning_table import QLearningTable


## TODO: In order to learn with an agent, replace
## these functions with the new agent's function
## and update the interface agent class
## so the random agent has the same functionality
##
class SmartAgent(Agent):
    def __init__(self):
        super(SmartAgent, self).__init__()
        self.qtable = QLearningTable(self.actions)
        self.new_game()        

    def reset(self):
        super(SmartAgent, self).reset()
        self.new_game()

    def new_game(self):
        self.base_top_left = None
        self.previous_state = None
        self.previous_action = None

    def get_state(self, obs):
        scvs = self.get_my_units_by_type(obs, units.Terran.SCV)
        idle_scvs = [scv for scv in scvs if scv.order_length == 0]
        command_centers = self.get_my_units_by_type(obs, units.Terran.CommandCenter)
        supply_depots = self.get_my_units_by_type(obs, units.Terran.SupplyDepot)
        completed_supply_depots = self.get_my_completed_units_by_type(
            obs, units.Terran.SupplyDepot
        )
        barrackses = self.get_my_units_by_type(obs, units.Terran.Barracks)
        completed_barrackses = self.get_my_completed_units_by_type(
            obs, units.Terran.Barracks
        )
        marines = self.get_my_units_by_type(obs, units.Terran.Marine)

        queued_marines = (
            completed_barrackses[0].order_length if len(completed_barrackses) > 0 else 0
        )

        free_supply = obs.observation.player.food_cap - obs.observation.player.food_used
        can_afford_supply_depot = obs.observation.player.minerals >= 100
        can_afford_barracks = obs.observation.player.minerals >= 150
        can_afford_marine = obs.observation.player.minerals >= 100

        enemy_scvs = self.get_enemy_units_by_type(obs, units.Terran.SCV)
        enemy_idle_scvs = [scv for scv in enemy_scvs if scv.order_length == 0]
        enemy_command_centers = self.get_enemy_units_by_type(
            obs, units.Terran.CommandCenter
        )
        enemy_supply_depots = self.get_enemy_units_by_type(
            obs, units.Terran.SupplyDepot
        )
        enemy_completed_supply_depots = self.get_enemy_completed_units_by_type(
            obs, units.Terran.SupplyDepot
        )
        enemy_barrackses = self.get_enemy_units_by_type(obs, units.Terran.Barracks)
        enemy_completed_barrackses = self.get_enemy_completed_units_by_type(
            obs, units.Terran.Barracks
        )
        enemy_marines = self.get_enemy_units_by_type(obs, units.Terran.Marine)

        enemy_race = "R"
        if (len(self.get_enemy_units_by_type(obs, units.Terran.CommandCenter))):
            enemy_race = "T"
        elif (len(self.get_enemy_units_by_type(obs, units.Protoss.Nexus))):
            enemy_race = "P"
        elif (len(self.get_enemy_units_by_type(obs, units.Zerg.Hatchery))):
            enemy_race =  "Z"
            
        return (
            len(command_centers),
            len(scvs),
            len(idle_scvs),
            len(supply_depots),
            len(completed_supply_depots),
            len(barrackses),
            len(completed_barrackses),
            len(marines),
            queued_marines,
            free_supply,
            can_afford_supply_depot,
            can_afford_barracks,
            can_afford_marine,
            enemy_race,
            len(enemy_command_centers),
            len(enemy_scvs),
            len(enemy_idle_scvs),
            len(enemy_supply_depots),
            len(enemy_completed_supply_depots),
            len(enemy_barrackses),
            len(enemy_completed_barrackses),
            len(enemy_marines),
        )

    def step(self, obs):
        super(SmartAgent, self).step(obs)
        state = str(self.get_state(obs))
        action = self.qtable.choose_action(state)
        if self.previous_action is not None:
            self.qtable.learn(
                self.previous_state,
                self.previous_action,
                obs.reward,
                "terminal" if obs.last() else state,
            )
        self.previous_state = state
        self.previous_action = action
        return getattr(self, action)(obs)
