import re
import random
from typing import Dict, Tuple, Set, List

# Stateは多分本当はint
State = int
Action = str
Observation = str # モデルの出力ラベルの集合

# strategyと実システム(MDP)の組み合わせ
# (Σin × Σout)* → Dist(Σin) という型のplayer側の戦略を作る
class StrategyBridge:

    def __init__(self, strategy_path, prism_model_path):
        self.initial_state = 0
        # 状態sにいる確率が current_state[s]
        self.current_state: Dict[State, float] = dict()
        self.strategy: Dict[State, Action] = dict()# adv.traから得られたもの
        self.observation_map: Dict[State, Observation] = dict() # .prismから得られたもの
        # 本当はこんなに複雑じゃなくて良いかも
        self.next_state: Dict[Tuple[State, Action, Observation], Dict[State, float]] = dict() # adv.traから得られたもの
        self.history : List[Tuple[Action, Observation]] = []

        self.__init_state_and_observation(prism_model_path)
        self.__init_strategy(strategy_path)
        states : Set[int] = set(self.strategy.keys())
        self.current_state = dict.fromkeys(states, 0.0)
        self.current_state[self.initial_state] = 1

    def next_action(self) -> Action:
        dist : Dict[Action, float] = dict.fromkeys(set(self.strategy.values()), 0.0)
        for state, weight in self.current_state.items():
            # self.strategy[state] : strategyでstateに対応づけられているアクション
            dist[self.strategy[state]] += weight
        # actionがsampleされる確率がdist[action]というサンプリング
        actions = [a for a in dist.keys()]
        prob_dist = [p for p in dist.values()]

        # TODO: 分岐処理は、current_stateが全て0になる場合をupdate_stateやMultiVestaで適切に処理すれば不要
        action : Action = ""
        if sum(prob_dist) == 0.0:
            action = random.choices(["go1", "go2"], [0.5,0.5], k=1)[0]
        else:
            action = random.choices(actions, prob_dist, k=1)[0]

        return action

    def update_state(self, action: Action, observation: Observation) -> bool:
        # 肝: actionはStrategy.next_actionで得られたものだが、observationはblack-boxなMDPを動かして観測されたもの
        # TODO: black-boxなMDPを動かして、想定していない出力が得られた場合に以下の処理だと困る。→ そういう状況を発見し次第aalpyにfeedbackする?
        # 1. 同様の入出力をblack-boxなMDPに与える → この出力のdistributionを得る
        # 2. それをaalpyにequivalence queryの反例として返す (これが反例になっているのは、今のobservationの発生確率が0 vs. 非ゼロなのでそう)
        # (ということはreplay用に入出力の列を覚えておかないといけない)
        self.history.append((action, observation))
        states : Set[int] = set(self.strategy.keys())
        new_state: Dict[State, float] = dict.fromkeys(states, 0.0)
        observation = StrategyBridge.__sort_observation(observation)
        # うまいことadv.traを見ながら今いる状態の確率分布を得る
        for state, weight in self.current_state.items():
            # こんな書き方はできないが、上手いベクトルの足し算のつもり
            # new_state += weight * self.next_state[state, action, observation]
            if (state, action, observation) in self.next_state:
                dist = self.next_state[(state, action, observation)]
                for s, prob in dist.items():
                    # これはadv.traのバグだが、状態がadv.traに書いていないのでどうしようもない
                    if s in new_state:
                        new_state[s] = new_state[s] + (weight * prob)
            else:
                # TODO: found counterexample?
                # if weight > 0:
                    # print("update_state(found_counter example?)" + str(state) + "," + action + "," + observation)
                pass
        # new_stateの正規化
        regularized_new_state : Dict[State, float] = dict()
        prob_sum = sum(new_state.values())
        if prob_sum == 0.0:
            # observationに対応する次の状態が存在しない
            self.current_state = new_state
            return False

        for s, prob in new_state.items():
            regularized_new_state[s] = prob / prob_sum

        self.current_state = regularized_new_state
        return True

    # strategyをresetするためのmethod
    def reset(self):
        states : Set[int] = set(self.strategy.keys())
        self.current_state = dict.fromkeys(states, 0.0)
        self.current_state[self.initial_state] = 1
        self.history = []

    # PRISMのモデル記述ファイルから初期状態を読み込む
    def __init_state_and_observation(self, prism_model_path):
        init_regex = re.compile(r"loc : \[\d+\.\.\d+\] init (\d+);.*")
        label_regex = re.compile(r"label \"(\w+)\" = ([\w=|]+);.*")
        loc_regex = re.compile(r"loc=(\w+)")
        with open(prism_model_path) as f:
            for line in f:
                init_match = init_regex.match(line)
                if init_match:
                    # 初期状態の読み込み
                    self.initial_state = int(init_match[1])
                else:
                    label_match = label_regex.match(line)
                    if label_match:
                        # labelを読み込んでobservationsに保存する
                        states = loc_regex.findall(label_match[2])
                        for state in states:
                            if int(state) in self.observation_map:
                                self.observation_map[int(state)] = self.observation_map[int(state)] + "__" + label_match[1]
                            else:
                                self.observation_map[int(state)] = label_match[1]
        for k in self.observation_map.keys():
            self.observation_map[k] = StrategyBridge.__sort_observation(self.observation_map[k])


    # PRISMの反例ファイルを読み込んで strategyとnext_stateを初期化する
    def __init_strategy(self, strategy_path):
        regex = re.compile(r"(\d+) \d\.?\d* (\d+) (\d\.?\d*) (\w+)")
        next_state_temp : Dict[Tuple[State, Action, Observation], Dict[State, float]] = dict()
        with open(strategy_path) as f:
            for line in f:
                match = regex.match(line)
                if match:
                    current_s = int(match[1])
                    next_s = int(match[2])
                    prob = float(match[3])
                    action = match[4]
                    self.strategy[current_s] = action
                    obsv = ""
                    if next_s in self.observation_map:
                        obsv = self.observation_map[next_s]
                    if (current_s, action, obsv) in next_state_temp:
                        next_state_temp[(current_s, action, obsv)][next_s] = prob
                    else:
                        next_state_temp[(current_s, action, obsv)] = {next_s: prob}
                else:
                    # debug
                    # print("match error(__init_strategy):" + line)
                    pass
        # next_stateの要素がdistributionになるように正規化する必要がある
        self.next_state = dict()
        for k, prob_map in next_state_temp.items():
            prob_sum = sum(prob_map.values())
            dist : Dict[State, float] = dict()
            for s, prob in prob_map.items():
                dist[s] = prob / prob_sum
            self.next_state[k] = dist

    def __sort_observation(observation) -> Observation:
        obs_list = sorted(observation.split('__'))
        return "__".join(obs_list)
