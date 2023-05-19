# `grid_world.py`

`grid_world.py` is a Python script that generates a grid world environment.

The grid world consists of 'concrete' cells, 'hole' cells (which terminate movement), 'goal' cells (which are the targets of the agent), and different terrain cells like 'mud', 'grass', and 'sand'. Each cell in the grid world is associated with an observation type: `Concrete`, `Hole`, `Wall`, `Goal`, `Mud`, `Grass`, or `Sand`. The agent can take actions in four directions: `North`, `South`, `East`, and `West`.

The generated grid world is output in the PRISM language, a probabilistic model checking language, which can be used for the verification and analysis of systems that exhibit random or probabilistic behavior.

## Options of `grid_world.py`

`grid_world.py` accepts several command-line arguments to customize the generated grid world:

- `--x_size`: The number of columns in the grid world (default: 10).
- `--y_size`: The number of rows in the grid world (default: 10).
- `--hole_ratio`: The ratio of the number of hole cells to the total number of cells in the grid world (default: 0.1).
- `--num_goal`: The number of goals in the grid world (default: 1).
- `--mud_ratio`: The ratio of the number of mud cells to the total number of cells in the grid world (default: 0.2).
- `--grass_ratio`: The ratio of the number of grass cells to the total number of cells in the grid world (default: 0.2).
- `--sand_ratio`: The ratio of the number of sand cells to the total number of cells in the grid world (default: 0.2).
- `--seed`: Seed for the random number generator to ensure reproducibility (default: None).

## Example Usage

To run `grid_world.py`, you can use the following command in a terminal:

```bash
python3 grid_world.py --x_size 10 --y_size 10 --hole_ratio 0.1 --num_goal 1 --mud_ratio 0.2 --grass_ratio 0.2 --sand_ratio 0.2 --seed 42
```

This will generate a 10x10 grid world with one goal, a hole-to-cell ratio of 0.1, mud-to-cell ratio of 0.2, grass-to-cell ratio of 0.2, sand-to-cell ratio of 0.2, and a random seed of 42 to ensure reproducibility. The output will be the PRISM representation of the generated grid world.
