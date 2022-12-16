import re
import random
import numpy as np
from typing import Dict, Tuple, Set, List

# Stateは多分本当はint
State = int
Action = str
Observation = str # モデルの出力ラベルの集合

# strategyと実システム(MDP)の組み合わせ
# (Σin × Σout)* → Dist(Σin) という型のplayer側の戦略を作る
class StrategyBridge:

    def __init__(self, strategy_path, states_path, trans_path, labels_path):
        self.initial_state : int = 0
        self.states = np.array([]) # 状態の集合 NDArray[int32]
        self.num_states = 0 # 状態数
        # 状態sにいる確率が current_state[s]
        # self.current_state: Dict[State, float] = dict()
        self.current_state = np.array([], dtype=np.float64) # State -> Probabilityのmap. NDArray[float64]
        # self.strategy: Dict[State, Action] = dict()# adv.traから得られたもの
        self.observation_map: Dict[State, Observation] = dict() # .labファイルから得られたもの
        self.observation_filter = dict() # Observation -> States filter
        self.action_map: List[Action] = list()
        self.strategy = np.array([], dtype=np.int32) # adv.traから得られたもの. State -> Action index. NDArray[int32]
        # 本当はこんなに複雑じゃなくて良いかも
        # self.next_state: Dict[Tuple[State, Action, Observation], Dict[State, float]] = dict() # adv.traから得られたもの
        self.next_state = np.array([], dtype=np.float64) # action -> transition_matrix
        self.history : List[Tuple[Action, Observation]] = []

        self.__init_state_and_observation(states_path, labels_path) # states, num_states, initial_state, observation_mapの初期化
        self.__init_strategy(strategy_path, trans_path) # strategy, next_stateの初期化

        for i in range(self.num_states):
            row_matrix = np.zeros(len(self.action_map))
            row_matrix[self.strategy[i]] = 1.0
            if i == 0:
                self.strategy_matrix = np.array([row_matrix])
            else:
                self.strategy_matrix = np.concatenate([self.strategy_matrix, [row_matrix]])
        for state, obsv in self.observation_map.items():
            if obsv in self.observation_filter:
                self.observation_filter[obsv][state] = 1
            else:
                states_filter = np.zeros(self.num_states)
                states_filter[state] = 1
                self.observation_filter[obsv] = states_filter
        self.current_state = np.zeros(self.num_states)
        self.current_state[self.initial_state] = 1.0
        self.empty_state = np.zeros(self.num_states)
        self.empty_dist = np.zeros(len(self.action_map))
        self.uniform_dist = np.full(len(self.action_map), 1.0 / len(self.action_map))

    def next_action(self) -> Action:
        # dist = self.empty_dist.copy()
        dist = np.dot(self.current_state, self.strategy_matrix)
        # for state, weight in self.current_state.items():
        #     # self.strategy[state] : strategyでstateに対応づけられているアクション
        #     if weight > 0:
        #         dist[self.strategy[state]] += weight
        # actionがsampleされる確率がdist[action]というサンプリング

        # TODO: 分岐処理は、current_stateが全て0になる場合をupdate_stateやMultiVestaで適切に処理すれば不要
        if dist.sum() == 0.0:
            action_index = random.choices(range(len(self.action_map)), self.uniform_dist, k=1)[0]
        else:
            action_index = random.choices(range(len(self.action_map)), dist, k=1)[0]

        return self.action_map[action_index]

    def update_state(self, action: Action, observation: Observation) -> bool:
        # 肝: actionはStrategy.next_actionで得られたものだが、observationはblack-boxなMDPを動かして観測されたもの
        # TODO: black-boxなMDPを動かして、想定していない出力が得られた場合に以下の処理だと困る。→ そういう状況を発見し次第aalpyにfeedbackする?
        # 1. 同様の入出力をblack-boxなMDPに与える → この出力のdistributionを得る
        # 2. それをaalpyにequivalence queryの反例として返す (これが反例になっているのは、今のobservationの発生確率が0 vs. 非ゼロなのでそう)
        # (ということはreplay用に入出力の列を覚えておかないといけない)
        self.history.append((action, observation))
        observation = StrategyBridge.__sort_observation(observation)

        action_index = self.action_map.index(action)
        new_state = np.dot(self.current_state, self.next_state[action_index])

        if observation in self.observation_filter:
            new_state = new_state * self.observation_filter[observation]
        else:
            # observationが学習されていない
            self.current_state = np.zeros(self.num_states)
            return False

        # for state, weight in self.current_state.items():
        # for state in range(self.num_states):
        #     weight = self.current_state[state]
        #     # new_state += weight * self.next_state[state, action, observation]
        #     if weight > 0:
        #         if (state, action, observation) in self.next_state:
        #             dist = self.next_state[(state, action, observation)]
        #             for s, prob in dist.items():
        #                 # これはadv.traのバグだが、状態がadv.traに書いていないのでどうしようもない
        #                 # if prob > 0 and s in new_state:
        #                 new_state[s] = new_state[s] + (weight * prob)
        #         else:
        #             # TODO: found counterexample?
        #             # if weight > 0:
        #                 # print("update_state(found_counter example?)" + str(state) + "," + action + "," + observation)
        #             pass
        # new_stateの正規化
        # regularized_new_state : Dict[State, float] = dict()
        prob_sum = new_state.sum()
        if prob_sum == 0.0:
            # observationに対応する次の状態が存在しない
            self.current_state = new_state
            return False
        new_state = new_state / prob_sum
        self.current_state = new_state
        return True

    # strategyをresetするためのmethod
    def reset(self):
        self.current_state = np.zeros(self.num_states)
        self.current_state[self.initial_state] = 1
        self.history = []

    # PRISMのモデル記述ファイルから初期状態を読み込む
    def __init_state_and_observation(self, states_path, labels_path):
        state_regex = re.compile(r"(\d+):.*")
        init_regex = re.compile(r".*?(\d+)=\"init\".*")
        label_name_regex = re.compile(r"(\d+)=\"(\w+)\"")
        label_regex = re.compile(r"(\d+):(.*)")
        label_index_regex = re.compile(r"(\d+)")
        max_state_num = 0
        with open(states_path) as f:
            for line in f:
                state_match = state_regex.match(line)
                if state_match:
                    if int(state_match[1]) > max_state_num:
                        max_state_num = int(state_match[1])
        self.num_states = max_state_num + 1
        self.states = np.arange(self.num_states, dtype=np.int32)
        labels_name = dict()
        with open(labels_path) as f:
            for line in f:
                init_match = init_regex.match(line)
                if init_match:
                    # 初期状態の読み込み
                    self.initial_state = int(init_match[1])
                    # ラベルのindexと名前の対応関係の読み込み
                    labels = label_name_regex.findall(line)
                    for label in labels:
                        labels_name[label[0]] = label[1]
                else:
                    label_match = label_regex.match(line)
                    if label_match:
                        state = label_match[1]
                        # labelを読み込んでobservationsに保存する
                        label_indices = label_index_regex.findall(label_match[2])
                        for label_idx in label_indices:
                            if label_idx in labels_name:
                                label_name = labels_name[label_idx]
                            else:
                                label_name = 'unknownobservation'
                            if int(state) in self.observation_map:
                                self.observation_map[int(state)] = self.observation_map[int(state)] + "__" + label_name
                            else:
                                self.observation_map[int(state)] = label_name
        for k in self.observation_map.keys():
            self.observation_map[k] = StrategyBridge.__sort_observation(self.observation_map[k])


    # PRISMの反例ファイルを読み込んで strategyとnext_stateを初期化する
    def __init_strategy(self, strategy_path, trans_path):
        regex = re.compile(r"(\d+) \d\.?\d* (\d+) (\d\.?\d*) (\w+)")
        # next_state_temp : Dict[Tuple[State, Action, Observation], Dict[State, float]] = dict()
        self.strategy = np.zeros(self.num_states, dtype=np.int32)
        with open(strategy_path) as f:
            for line in f:
                match = regex.match(line)
                if match:
                    current_s = int(match[1])
                    action = match[4]
                    if not action in self.action_map:
                        self.action_map.append(action)
                    action_index = self.action_map.index(action)
                    self.strategy[current_s] = action_index
                    # obsv = ""
                    # if next_s in self.observation_map:
                    #     obsv = self.observation_map[next_s]
                    # if (current_s, action, obsv) in next_state_temp:
                    #     next_state_temp[(current_s, action, obsv)][next_s] = prob
                    # else:
                    #     next_state_temp[(current_s, action, obsv)] = {next_s: prob}
                else:
                    # debug
                    # print("match error(__init_strategy):" + line)
                    pass
        self.next_state = np.zeros((len(self.action_map), self.num_states, self.num_states))
        with open(trans_path) as f:
            for line in f:
                match = regex.match(line)
                if match:
                    current_s = int(match[1])
                    next_s = int(match[2])
                    prob = float(match[3])
                    action = match[4]
                    if action in self.action_map:
                        action_index = self.action_map.index(action)
                        self.next_state[action_index][current_s][next_s] += prob
        # next_stateの要素がdistributionになるように正規化する必要がある
        for i in range(len(self.action_map)):
            self.next_state[i] = self.next_state[i] / (np.sum(self.next_state[i], axis=1).reshape(1, -1).transpose())

        # self.next_state = dict()
        # for k, prob_map in next_state_temp.items():
        #     prob_sum = sum(prob_map.values())
        #     dist : Dict[State, float] = dict()
        #     for s, prob in prob_map.items():
        #         dist[s] = prob / prob_sum
        #     self.next_state[k] = dist

    # observation (APを'__'で連結した文字列) をAPの辞書順で整列させる
    def __sort_observation(observation : str) -> Observation:
        obs_list = sorted(observation.split('__'))
        return "__".join(obs_list)
