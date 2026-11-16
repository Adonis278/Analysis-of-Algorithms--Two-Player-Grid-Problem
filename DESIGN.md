# Competitive Foraging — Project Design

Research question (simplified): *Does a "contest-aware" agent — one that targets only food it
can reach before the opponent — collect more food than a greedy agent that always heads to the
nearest food?*

The exact Akuna game is not published online, so the spec comes from the recovered interview
logs. We build a clean, self-contained version. Python; matplotlib for plots.

## Folder layout
```
Algorithms-Course-Project/
├─ game.py          # engine: board, BFS, moves, step logic, run_game()
├─ agents.py        # greedy_agent, contest_aware_agent, fixed rival policy
├─ boards.py        # random board generation + connectivity validation
├─ experiment.py    # runs all (density x food) combos, writes results.csv
├─ analyze.py       # aggregates CSV -> summary table + plots
├─ tests/test_game.py
├─ results.csv      # generated
├─ figures/         # generated plots
└─ report/          # the writeup (built last)
```

## 1. game.py — engine
- N = 15. walls: set of (r,c). foods: set of (r,c). pos: {YOU:(r,c), RIVAL:(r,c)}.
- ORDER = ['U','D','L','R']; DELTA = {'U':(-1,0),'D':(1,0),'L':(0,-1),'R':(0,1),'S':(0,0)}.
- bfs(start, blocked, walls, N) -> (dist, first_move): distances + first step toward each cell;
  `blocked` = the other player's current cell.
- legal_moves(pos, other_pos, walls, N): in-grid, not wall, not onto other player.
- apply_move(pos, move); collection check (stepping onto a food removes it).
- run_game(agent_fn, board, max_turns=400) -> {my_food, rival_food, turns, avg_decision_ms}.
  Alternates YOU then RIVAL. Stops on: no foods left; mutual stalemate (neither can reach any
  food) -> append one 'S'; or turn cap.

## 2. agents.py — the two strategies (only target-selection differs)
- greedy_agent: dy,_ = bfs(you, blocked={rival}); nearest reachable food; return first_move; else 'S'.
- contest_aware_agent: also dr,_ = bfs(rival, blocked={you}); W = {f: dy[f] < dr[f]} (tie '=='
  counts as a win); nearest in W; fallback to nearest reachable if W empty; return first_move.
- rival_move (FIXED for both experiments): greedy nearest-food BFS, tie-break U,D,L,R.

## 3. boards.py — controls contest level
make_board(density, n_food, seed): walls at density in {0.10,0.25,0.40}; n_food in {5,15,30};
random distinct P/O starts. Validity: flood-fill from P; keep only if P, O, and >=90% of food
are in one connected region. Seeded RNG for reproducibility.

## 4. experiment.py — paired runner
For each (density, n_food): generate N=200 valid boards. Run BOTH agents on the SAME board vs
the fixed rival. Row per (board, agent): board_id, density, n_food, agent, my_food, rival_food,
total_food, share, outcome, turns, avg_decision_ms -> results.csv.
(9 combos x 200 boards x 2 agents = 3,600 games.)

## 5. analyze.py — answers the question
Group by agent and by (density, n_food): mean food, win rate, mean share. Paired diff
(contest - greedy) per board. Plots -> figures/: win-rate vs food count; win-rate vs wall
density; decision-time distribution.

## 6. Complexity (for the report)
- BFS on 15x15 ~ O(225) = constant per call.
- greedy: 1 BFS/turn -> O(T). contest-aware: 2 BFS/turn -> O(T), same order (advantage is "free").

## 7. tests/
BFS distances on a hand-checked grid; legal-move rejection; food removed on collection; game
terminates; stalemate -> single 'S'.

## Build order
1. game.py + tests  2. agents.py  3. boards.py  4. experiment.py  5. analyze.py  6. report.
