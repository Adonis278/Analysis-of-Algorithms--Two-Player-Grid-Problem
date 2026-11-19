"""Run the experiment and write results.csv.

For every (wall density, food count) combination we generate N_BOARDS validated
boards. Each board is played twice -- once by the greedy agent, once by the
contest-aware agent -- against the SAME fixed greedy rival. Playing both agents on
the identical board is a paired design: differences cannot be blamed on luck of
the map.

Run:  python experiment.py
"""

import csv

from boards import generate_valid_board
from agents import greedy_agent, contest_aware_agent, rival_agent
from game import run_game

# The two board "knobs" we vary -- together they control how contested a game is.
DENSITIES = [0.10, 0.25, 0.40]   # fraction of cells that are walls (open -> maze)
FOOD_COUNTS = [5, 15, 30]        # food items on the board (scarce -> plentiful)
N_BOARDS = 200                   # boards per (density, food) combo. Set to 40 for a fast demo run.
# Total games = 3 densities x 3 food counts x 200 boards x 2 agents = 3,600.

AGENTS = {'greedy': greedy_agent, 'contest_aware': contest_aware_agent}

FIELDS = ['board_id', 'density', 'n_food', 'agent',
          'my_food', 'rival_food', 'total_food', 'share', 'outcome',
          'turns', 'avg_decision_ms']


def _board_seed(density, n_food, index):
    """A deterministic, well-spread seed for one board."""
    return (int(density * 100) * 1_000_003 + n_food * 10_007 + index) & 0xFFFFFFFF


def run_all(out_path='results.csv'):
    rows = []
    for density in DENSITIES:
        for n_food in FOOD_COUNTS:
            for index in range(N_BOARDS):
                board_id = f'{int(density * 100):02d}-{n_food:02d}-{index:04d}'
                setup = generate_valid_board(density, n_food, _board_seed(density, n_food, index))
                # PAIRED DESIGN: the SAME `setup` is played by BOTH agents. Any
                # difference in food collected is caused by the strategy, not the map.
                for name, agent in AGENTS.items():
                    result = run_game(setup, agent, rival_agent)
                    # share = my fraction of the food that got eaten (0.5 = even split).
                    collected = result['my_food'] + result['rival_food']
                    share = (result['my_food'] / collected) if collected else 0.0
                    rows.append({
                        'board_id': board_id,
                        'density': density,
                        'n_food': n_food,
                        'agent': name,
                        'my_food': result['my_food'],
                        'rival_food': result['rival_food'],
                        'total_food': result['total_food'],
                        'share': round(share, 4),
                        'outcome': result['outcome'],
                        'turns': result['turns'],
                        'avg_decision_ms': round(result['avg_decision_ms'], 4),
                    })
            print(f'  done density={density:.2f} n_food={n_food}')

    with open(out_path, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} rows to {out_path}')


if __name__ == '__main__':
    run_all()
