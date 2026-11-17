"""Summarise results.csv and draw the figures that answer the question.

Prints an overall table and a breakdown by board condition, computes the paired
(contest_aware - greedy) win on identical boards, and writes three plots to
figures/. Uses only the standard library plus matplotlib.

Run:  python analyze.py   (after experiment.py has produced results.csv)
"""

import csv
import os
from collections import defaultdict
from statistics import mean

import matplotlib
matplotlib.use('Agg')          # file output, no interactive window needed
import matplotlib.pyplot as plt

RESULTS = 'results.csv'
FIG_DIR = 'figures'


def load(path=RESULTS):
    with open(path, newline='') as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row['density'] = float(row['density'])
        row['n_food'] = int(row['n_food'])
        row['my_food'] = int(row['my_food'])
        row['share'] = float(row['share'])
        row['avg_decision_ms'] = float(row['avg_decision_ms'])
        row['win'] = 1 if row['outcome'] == 'win' else 0
    return rows


def _by(rows, agent):
    return [r for r in rows if r['agent'] == agent]


def overall_table(rows):
    print('\n=== Overall (all boards) ===')
    print(f'{"agent":<15}{"win rate":>10}{"mean food":>12}{"mean share":>12}{"ms/move":>10}')
    for agent in ('greedy', 'contest_aware'):
        sub = _by(rows, agent)
        print(f'{agent:<15}{mean(r["win"] for r in sub):>10.3f}'
              f'{mean(r["my_food"] for r in sub):>12.2f}'
              f'{mean(r["share"] for r in sub):>12.3f}'
              f'{mean(r["avg_decision_ms"] for r in sub):>10.3f}')


def paired_improvement(rows):
    """Compare the two agents on the same board_id."""
    by_board = defaultdict(dict)
    for r in rows:
        by_board[r['board_id']][r['agent']] = r
    diffs = [b['contest_aware']['my_food'] - b['greedy']['my_food']
             for b in by_board.values() if 'greedy' in b and 'contest_aware' in b]
    wins = sum(1 for d in diffs if d > 0)
    ties = sum(1 for d in diffs if d == 0)
    losses = sum(1 for d in diffs if d < 0)
    print('\n=== Paired: contest_aware vs greedy on identical boards ===')
    print(f'boards: {len(diffs)}  |  contest better: {wins}  equal: {ties}  worse: {losses}')
    print(f'mean food difference (contest - greedy): {mean(diffs):+.3f}')


def _winrate_by(rows, key):
    out = {}
    for agent in ('greedy', 'contest_aware'):
        buckets = defaultdict(list)
        for r in _by(rows, agent):
            buckets[r[key]].append(r['win'])
        out[agent] = {k: mean(v) for k, v in sorted(buckets.items())}
    return out


def plot_winrate(rows, key, xlabel, fname):
    data = _winrate_by(rows, key)
    plt.figure(figsize=(6, 4))
    for agent in ('greedy', 'contest_aware'):
        xs = list(data[agent].keys())
        ys = [data[agent][x] for x in xs]
        plt.plot(xs, ys, marker='o', label=agent)
    plt.xlabel(xlabel)
    plt.ylabel('win rate vs rival')
    plt.ylim(0, 1)
    plt.title(f'Win rate by {xlabel}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, fname), dpi=120)
    plt.close()


def plot_decision_time(rows, fname='decision_time.png'):
    plt.figure(figsize=(6, 4))
    for agent in ('greedy', 'contest_aware'):
        times = [r['avg_decision_ms'] for r in _by(rows, agent)]
        plt.hist(times, bins=30, alpha=0.5, label=agent)
    plt.xlabel('avg decision time per move (ms)')
    plt.ylabel('number of games')
    plt.title('Decision-time distribution')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, fname), dpi=120)
    plt.close()


def main():
    rows = load()
    os.makedirs(FIG_DIR, exist_ok=True)
    overall_table(rows)
    paired_improvement(rows)
    plot_winrate(rows, 'n_food', 'food count', 'winrate_by_food.png')
    plot_winrate(rows, 'density', 'wall density', 'winrate_by_density.png')
    plot_decision_time(rows)
    print(f'\nFigures written to {FIG_DIR}/')


if __name__ == '__main__':
    main()
