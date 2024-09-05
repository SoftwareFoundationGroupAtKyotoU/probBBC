import re
import random
import numpy as np
from typing import Dict, Tuple, Set, List

# Stateは多分本当はint
State = int
Action = str
Observation = str  # モデルの出力ラベルの集合


# strategyと実システム(MDP)の組み合わせ
# (Σin × Σout)* → Dist(Σin) という型のplayer側の戦略を作る
class StrategyBridge:
    def __init__(self, strategy_path, states_path, trans_path, labels_path):
        self.initial_state = 0
        # 状態sにいる確率が current_state[s]
        self.current_state: Dict[State, float] = dict()
        self.strategy: Dict[State, Action] = dict()  # adv.traから得られたもの
        self.observation_map: Dict[State, Observation] = (
            dict()
        )  # .prismから得られたもの
        # 本当はこんなに複雑じゃなくて良いかも
        self.next_state: Dict[Tuple[State, Action, Observation], Dict[State, float]] = (
            dict()
        )  # adv.traから得られたもの
        # self.history : List[Tuple[Action, Observation]] = []

        self.__init_state_and_observation(labels_path)
        self.__init_strategy(strategy_path, trans_path)
        self.states = set(self.strategy.keys())
        self.actions = set(self.strategy.values())
        self.current_state = {self.initial_state: 1.0}
        self.empty_dist: Dict[Action, float] = dict.fromkeys(self.actions, 0.0)
        self.actions_list: List[Action] = list(self.empty_dist.keys())

    def next_action(self) -> Action:
        dist: Dict[Action, float] = self.empty_dist.copy()
        is_empty_dist = True
        for state, weight in self.current_state.items():
            # self.strategy[state] : strategyでstateに対応づけられているアクション
            if weight > 0 and state in self.strategy:
                is_empty_dist = False
                dist[self.strategy[state]] += weight
        # actionがsampleされる確率がdist[action]というサンプリング
        prob_dist = list(dist.values())

        action: Action = ""
        if is_empty_dist:
            action = random.choice(self.actions_list)
        else:
            action = random.choices(self.actions_list, prob_dist, k=1)[0]

        return action

    def update_state(self, action: Action, observation_aps: List[str]) -> bool:
        # 肝: actionはStrategy.next_actionで得られたものだが、observationはblack-boxなMDPを動かして観測されたもの
        # TODO: black-boxなMDPを動かして、想定していない出力が得られた場合に以下の処理だと困る。→ そういう状況を発見し次第aalpyにfeedbackする?
        # 1. 同様の入出力をblack-boxなMDPに与える → この出力のdistributionを得る
        # 2. それをaalpyにequivalence queryの反例として返す (これが反例になっているのは、今のobservationの発生確率が0 vs. 非ゼロなのでそう)
        # (ということはreplay用に入出力の列を覚えておかないといけない)
        # self.history.append((action, observation))
        new_state: Dict[State, float] = dict()
        observation = StrategyBridge.__sort_observation(observation_aps)

        for state, weight in self.current_state.items():
            # new_state += weight * self.next_state[state, action, observation]
            if weight > 0:
                if (state, action, observation) in self.next_state:
                    dist = self.next_state[(state, action, observation)]
                    for s, prob in dist.items():
                        if prob > 0:
                            if s in new_state:
                                new_state[s] = new_state[s] + (weight * prob)
                            else:
                                new_state[s] = weight * prob
                else:
                    # TODO: found counterexample?
                    # if weight > 0:
                    # print("update_state(found_counter example?)" + str(state) + "," + action + "," + observation)
                    pass
        # new_stateの正規化
        prob_sum = sum(new_state.values())
        if prob_sum == 0.0:
            # observationに対応する次の状態が存在しない
            self.current_state = new_state
            return False

        for s in new_state:
            new_state[s] = new_state[s] / prob_sum

        self.current_state = new_state
        return True

    # strategyをresetするためのmethod
    def reset(self):
        self.current_state = {self.initial_state: 1.0}
        # self.history = []

    # PRISMのモデル記述ファイルから初期状態を読み込む
    def __init_state_and_observation(self, labels_path):
        init_regex = re.compile(r".*?(\d+)=\"init\".*")
        label_name_regex = re.compile(r"(\d+)=\"(\w+)\"")
        label_regex = re.compile(r"(\d+):(.*)")
        label_index_regex = re.compile(r"(\d+)")
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
                                label_name = "unknownobservation"
                            if int(state) in self.observation_map:
                                self.observation_map[int(state)].append(label_name)
                            else:
                                self.observation_map[int(state)] = [label_name]
        for k in self.observation_map.keys():
            self.observation_map[k] = StrategyBridge.__sort_observation(
                self.observation_map[k]
            )

    # PRISMの反例ファイルを読み込んで strategyとnext_stateを初期化する
    def __init_strategy(self, strategy_path, trans_path):
        regex = re.compile(r"(\d+) \d\.?\d* (\d+) (\d\.?\d*) (\w+)")
        next_state_temp: Dict[Tuple[State, Action, Observation], Dict[State, float]] = (
            dict()
        )
        with open(strategy_path) as f:
            for line in f:
                match = regex.match(line)
                if match:
                    current_s = int(match[1])
                    next_s = int(match[2])
                    prob = float(match[3])
                    action = match[4]
                    self.strategy[current_s] = action
                else:
                    # debug
                    # print("match error(__init_strategy):" + line)
                    pass
        with open(trans_path) as f:
            for line in f:
                match = regex.match(line)
                if match:
                    current_s = int(match[1])
                    next_s = int(match[2])
                    prob = float(match[3])
                    action = match[4]
                    obsv = ""
                    if next_s in self.observation_map:
                        obsv = self.observation_map[next_s]
                    if (current_s, action, obsv) in next_state_temp:
                        next_state_temp[(current_s, action, obsv)][next_s] = prob
                    else:
                        next_state_temp[(current_s, action, obsv)] = {next_s: prob}
        # next_stateの要素がdistributionになるように正規化する必要がある
        self.next_state = dict()
        for k, prob_map in next_state_temp.items():
            prob_sum = sum(prob_map.values())
            dist: Dict[State, float] = dict()
            for s, prob in prob_map.items():
                dist[s] = prob / prob_sum
            self.next_state[k] = dist

    # observation_aps (APの集合) をAPの辞書順で整列させ、"__"で連結した文字列として返す
    def __sort_observation(observation_aps: List[str]) -> Observation:
        return "__".join(sorted(observation_aps))
