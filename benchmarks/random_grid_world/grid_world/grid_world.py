from enum import IntEnum
from typing import Tuple, List, Optional
import random
import argparse


class Actions(IntEnum):
    North = 0,  # Moving up on the grid
    South = 1,  # Moving down on the grid
    West = 2,  # Moving left on the grid
    East = 3  # Moving right on the grid


class Observations(IntEnum):
    Concrete = 0,  # Represents a normal, navigable cell
    Hole = 1,  # Represents a hole cell where movement stops
    Wall = 2,  # Represents an encountered wall, i.e., a border of the grid
    Goal = 3,  # Represents a goal cell
    Mud = 4,
    Grass = 5,
    Sand = 6


def label_assignments() -> str:
    """
    Function to generate PRISM code to assign labels to output values.
    It assigns labels for different types of cells in the grid.
    """
    result = 'label "Concrete" = output=0;\n'
    result += 'label "Hole" = output=1;\n'
    result += 'label "Wall" = output=2;\n'
    result += 'label "Goal" = output=3;\n'
    result += 'label "Mud" = output=4;\n'
    result += 'label "Grass" = output=5;\n'
    result += 'label "Sand" = output=6;\n'
    return result


def next_str(probability: float, next_x: int, next_y: int, observation: Observations):
    """
    Print the transition corresponding to the inputs. The following shows examples.

    It returns the following if probability == 1, next_x ==0, next_y == 0, and observation == Observations.Wall.
    (x'=0) & (y'=0) & (output'=2)

    It returns the following if probability == 0.75, next_x ==0, next_y == 2, and observation == Observations.Normal
    0.750 : (x'=0) & (y'=2) & (output'=0)

    :param probability: The probability of transitioning to the next state, as a float from 0 to 1.
                        If probability is 1, it does not appear in the result.
    :param next_x: The x-coordinate of the next state. It should be an integer within the grid boundaries.
    :param next_y: The y-coordinate of the next state. It should be an integer within the grid boundaries.
    :param observation: The observation of the next state. It should be a member of the Observations enum.
    :return: A string representing the transition in the PRISM language.
    """
    probability_str = f"{probability:.3f} :" if probability != 1 else ""
    next_state_str = f"(x'={next_x}) & (y'={next_y}) & (output'={observation.value})"
    return f"{probability_str} {next_state_str}"


class GridWorld:
    """
    Class to represent a grid world environment
    """

    def __init__(self, x_size: int, y_size: int, hole_ratio: float = 0.1, num_goal: int = 1, mud_ratio: float = 0.2,
                 grass_ratio: float = 0.2, sand_ratio: float = 0.2, seed: Optional[int] = None):
        """
        Randomly construct a grid world.

        At normal states, the intended action is used with probability 1 - noize_probability and another action is
        used with probability noize_probability.
        The hole states are the dead state and the agent does not move from it.
        At the goal states, the agent does not move anymore, too.

        :param x_size: The number of columns in the grid world
        :param y_size: The number of rows in the grid world
        :param seed: The random seed to ensure the reproducibility of the grid world
        :param num_goal: The number of goals in the constructed grid world
        :param hole_ratio: The ratio of the number of hole cells to the total number of cells in the grid world
        """
        self.x_size = x_size
        self.y_size = y_size
        random.seed(seed)
        self.x_init, self.y_init = 0, 0
        self.noise_probability = {
            Observations.Concrete: 1.0,
            Observations.Hole: 1.0,
            Observations.Wall: 1.0,
            Observations.Goal: 1.0,
            Observations.Mud: 0.6,
            Observations.Grass: 0.8,
            Observations.Sand: 0.75
        }

        # Randomly decide holes. The initial state should not be a hole
        self.holes = []
        for _ in range(int(x_size * y_size * hole_ratio)):
            x_hole, y_hole = random.randint(0, x_size - 1), random.randint(0, y_size - 1)
            if (x_hole, y_hole) not in self.holes and (x_hole, y_hole) != (self.x_init, self.y_init):
                self.holes.append((x_hole, y_hole))

        # Randomly decide goals. Any goal must not be a hole. The initial state should not be a hole, either.
        self.goals = []
        while len(self.goals) < num_goal:
            while True:
                x_goal, y_goal = random.randint(0, x_size - 1), random.randint(0, y_size - 1)
                if (x_goal, y_goal) not in self.goals and (x_goal, y_goal) not in self.holes and (x_goal, y_goal) != (
                        self.x_init, self.y_init):
                    self.goals.append((x_goal, y_goal))
                    break

        # Randomly sample mud states. Any mud must not be a hole nor a goal. The initial state should not be mud,
        # either. A state next to a mud state should not be a mud state
        self.mud = []
        for _ in range(int(x_size * y_size * mud_ratio)):
            while True:
                x_mud, y_mud = random.randint(0, x_size - 1), random.randint(0, y_size - 1)
                if (x_mud, y_mud) not in self.holes and (x_mud, y_mud) not in self.goals and (x_mud, y_mud) != (
                        self.x_init, self.y_init):
                    if (x_mud, y_mud) not in self.mud and (x_mud - 1, y_mud) not in self.mud and (
                            x_mud + 1, y_mud) not in self.mud and (x_mud, y_mud - 1) not in self.mud and (
                            x_mud, y_mud + 1) not in self.mud:
                        self.mud.append((x_mud, y_mud))
                    break

        # Randomly sample grass states. Any grass must not be a hole nor a goal. The initial state should not be grass,
        # either. A state next to a grass state should not be a grass state
        self.grass = []
        for _ in range(int(x_size * y_size * grass_ratio)):
            while True:
                x_grass, y_grass = random.randint(0, x_size - 1), random.randint(0, y_size - 1)
                if (x_grass, y_grass) not in self.holes and (x_grass, y_grass) not in self.goals and (
                        x_grass, y_grass) != (self.x_init, self.y_init):
                    if (x_grass, y_grass) not in self.grass and (x_grass - 1, y_grass) not in self.grass and (
                            x_grass + 1, y_grass) not in self.grass and (x_grass, y_grass - 1) not in self.grass and (
                            x_grass, y_grass + 1) not in self.grass:
                        self.grass.append((x_grass, y_grass))
                    break

        # Randomly sample sand states. Any sand must not be a hole nor a goal. The initial state should not be sand,
        # either. A state next to a sand state should not be a sand state
        self.sand = []
        for _ in range(int(x_size * y_size * sand_ratio)):
            while True:
                x_sand, y_sand = random.randint(0, x_size - 1), random.randint(0, y_size - 1)
                if (x_sand, y_sand) not in self.holes and (x_sand, y_sand) not in self.goals and (x_sand, y_sand) != (
                        self.x_init, self.y_init):
                    if (x_sand, y_sand) not in self.sand and (x_sand - 1, y_sand) not in self.sand and (
                            x_sand + 1, y_sand) not in self.sand and (x_sand, y_sand - 1) not in self.sand and (
                            x_sand, y_sand + 1) not in self.sand:
                        self.sand.append((x_sand, y_sand))
                    break

    def to_prism(self) -> str:
        # Function to generate the PRISM representation of the whole grid
        result = self.to_header()
        for x in range(self.x_size):
            for y in range(self.y_size):
                result += self.to_state(x, y)
        result += self.footer
        result += label_assignments()
        return result

    def to_header(self) -> str:
        # Function to generate the PRISM code header, which includes state variables and their initialization
        result = 'mdp\n'
        result += 'module random_grid_world\n'
        result += f'  x : [0..{self.x_size}] init {self.x_init};\n'
        result += f'  y : [0..{self.y_size}] init {self.y_init};\n'
        result += '  output : [0..6] init 0;\n'
        return result

    def to_state(self, x: int, y: int) -> str:
        """
        Return lines corresponding to a state

        Example of lines are as follows
        [North] (x=0) & (y=0) -> (x'=0) & (y'=0) & (output'=2);
        [South] (x=0) & (y=1) -> 0.750 : (x'=0) & (y'=2) & (output'=7) + 0.250 : (x'=1) & (y'=2) & (output'=4);
        """
        lines = []
        for action in Actions:
            transitions = self.make_next(x, y, action)
            transitions_str = " + ".join(
                [next_str(prob, next_x, next_y, obs) for prob, next_x, next_y, obs in transitions])
            lines.append(f"  [{action.name}] (x={x}) & (y={y}) -> {transitions_str};")
        return "\n".join(lines) + '\n\n'

    def to_observation(self, x: int, y: int) -> Observations:
        if (x, y) in self.holes:
            observation = Observations.Hole
        elif (x, y) in self.goals:
            observation = Observations.Goal
        elif (x, y) in self.mud:
            observation = Observations.Mud
        elif (x, y) in self.grass:
            observation = Observations.Grass
        elif (x, y) in self.sand:
            observation = Observations.Sand
        else:
            observation = Observations.Concrete
        return observation

    def make_next(self, x: int, y: int, action: Actions) -> List[Tuple[float, int, int, Observations]]:
        """
        Generate the possible next states given current position (x, y) and action.

        The hole states are the dead state and the agent does not move from it.
        At the goal states, the agent does not move anymore, too.
        If the intended direction is our of the arena, it does not move and outputs "Wall"

        Otherwise, the target is decided depending on the observation of the intended target state.
        It moves to the intended target state with probability self.noise_probability[target_observation] and moves to
        one the states next to the intended one with the remaining probability.
        For example, if the intended move is from (x, y) to (x, y + 1), we move to (x, y + 1) with probability
        self.noise_probability[target_observation], (x - 1, y + 1) with probability
        (1 - self.noise_probability[target_observation]) / 2, and (x + 1, y + 1) with probability
        (1 - self.noise_probability[target_observation]) / 2 if none of the above states are not wall.
        If one of the target states are wall, we do not move there. For instance, if (x + 1, y + 1) is a wall state,
        we move to (x - 1, y + 1) with probability 1 - self.noise_probability[target_observation].

        :param x: current x position of the agent
        :param y: current y position of the agent
        :param action: intended action of the agent
        :return: A list of tuples. Each tuple represents a potential state and contains
                 the transition probability, next_x, next_y, and the corresponding observation
        """
        if (x, y) in self.holes or (x, y) in self.goals:
            return [(1.0, x, y, Observations.Hole if (x, y) in self.holes else Observations.Goal)]

        next_states = []
        action_to_delta = {Actions.North: (0, -1), Actions.South: (0, 1), Actions.West: (-1, 0), Actions.East: (1, 0)}

        dx, dy = action_to_delta[action]
        target_x, target_y = x + dx, y + dy

        # If the target state is a wall, stay in the current state
        if target_x < 0 or target_x >= self.x_size or target_y < 0 or target_y >= self.y_size:
            next_states.append((1.0, x, y, Observations.Wall))
            return next_states

        target_observation = self.to_observation(target_x, target_y)

        # Define the list of target states and their corresponding observations
        targets = [(target_x, target_y)]
        if (target_x, target_y) not in self.holes and (target_x, target_y) not in self.goals and\
                self.noise_probability[target_observation] < 1.0:
            targets.extend([(target_x - dx, target_y - dy), (target_x + dx, target_y + dy)])

        # Filter out wall states from the list of targets
        targets = [(tx, ty) for tx, ty in targets if 0 <= tx < self.x_size and 0 <= ty < self.y_size]

        for tx, ty in targets:
            # Determine the observation of the target state
            observation = self.to_observation(tx, ty)

            # Determine the transition probability to the target state
            if (tx, ty) == (target_x, target_y):
                probability = self.noise_probability[target_observation]
            else:
                probability = (1.0 - self.noise_probability[target_observation]) / (len(targets) - 1)

            next_states.append((probability, tx, ty, observation))

        return next_states

    footer = 'endmodule\n'
    # The positions of holes
    holes: List[Tuple[int, int]]
    # The positions of goals
    goals: List[Tuple[int, int]]


def main():
    """
    The entry point for grid world generation. It prints the resulting grid world generated by the parameters given
    as arguments.
    """
    parser = argparse.ArgumentParser(description='Generate a grid world.')
    parser.add_argument('--x_size', type=int, required=True, help='Number of columns in the grid world')
    parser.add_argument('--y_size', type=int, required=True, help='Number of rows in the grid world')
    parser.add_argument('--num_goal', type=int, default=1, help='Number of goals in the grid world')
    parser.add_argument('--hole_ratio', type=float, default=0.1,
                        help='Ratio of the number of hole cells to the total number of cells in the grid world')
    parser.add_argument('--mud_ratio', type=float, default=0.2, help='The ratio of the number of mud cells')
    parser.add_argument('--grass_ratio', type=float, default=0.2, help='The ratio of the number of grass cells')
    parser.add_argument('--sand_ratio', type=float, default=0.2, help='The ratio of the number of sand cells')
    parser.add_argument('--seed', type=int, default=None, help='Random seed to ensure reproducibility')
    args = parser.parse_args()

    grid_world = GridWorld(args.x_size, args.y_size, args.hole_ratio, args.num_goal, args.mud_ratio, args.grass_ratio,
                           args.sand_ratio, args.seed)
    print(grid_world.to_prism())


if __name__ == "__main__":
    main()
