# Analysis of Algorithms — Two-Player Grid Problem

An algorithmic study of a competitive, two-player food-collection game on a grid.

## Research question
Does a **contest-aware** agent — one that targets only food it can reach *before* the
opponent — collect more food than a **greedy** agent that always heads to the nearest food?

## Why it matters
"Always go to the nearest item" is intuitive but suboptimal when a second agent competes for
the same items: you waste moves racing to food the opponent reaches first. This project tests
whether reasoning about the opponent's reach (via BFS distance comparison) beats a purely
self-centered heuristic — and whether that advantage grows as the board becomes more contested.

## The game
A 15x15 grid: empty, walls, your start, a rival start, and food. Players alternate turns
(you, then rival); each moves one cell `U/D/L/R` or stays `S`. Stepping onto food collects it.
The rival follows a fixed greedy nearest-food policy. Score = food collected.

## Approach
- **BFS** for shortest-path distances on the grid.
- **Greedy agent** (baseline): nearest reachable food.
- **Contest-aware agent**: target only food where `dist_you[f] < dist_rival[f]`.
- Both play identical, randomly generated, connectivity-validated boards against the same fixed
  rival (paired design). Metrics: food collected, win rate, decision time.

## Layout
See [DESIGN.md](DESIGN.md) for the full module design and build order.

```
game.py        engine: board, BFS, moves, run_game()
agents.py      greedy + contest-aware agents, fixed rival
boards.py      random board generation + validation
experiment.py  runs all density x food combos -> results.csv
analyze.py     aggregates results -> summary + figures/
tests/         correctness tests
```

## Run
```
python experiment.py      # generates results.csv
python analyze.py         # writes summary + figures/
python -m pytest          # tests
```

Course project — Analysis of Algorithms. Final submission: Nov 19, 2026.
