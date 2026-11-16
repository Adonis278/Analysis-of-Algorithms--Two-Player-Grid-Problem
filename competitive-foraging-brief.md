# Competitive Foraging — Problem Statement & Research-Question Brief

Source: Akuna technical-interview problem ("Competitive Foraging"), recovered from cue
interview logs (session 2026-10-29). Framed to fit the Algorithms Course Project rubric
(proposal due Nov 10, 2026; final due Nov 19, 2026).

---

## 1. The problem (as posed)

**Board.** A 15×15 grid of characters:
- `.` empty · `#` wall · `P` = you · `O`/`Q` = rival · `F` = food.
- Exactly one `P`, one rival; zero or more `F`.

**Rules.**
- Two agents alternate turns: **you move, then the rival moves.**
- Moves: `U/D/L/R/S` (S = stay). Illegal if it leaves the grid, enters `#`, or steps onto
  the other player's current cell.
- Stepping onto an `F` **collects** it (then it's gone). Your score = foods you collect.
- The **rival policy is fixed and known**: BFS to its nearest *reachable* food, tie-break
  move order `U, D, L, R`. Provided as `board.rival_move(state)`.
- Game ends when no food remains, or neither agent can reach any remaining food.
- You must **terminate within a time limit** — aimless wandering causes a timeout.

**Return.** Your full move string over `U/D/L/R/S`.

**Given interface.** `Board(grid)`; `state.foods`;
`state.player_positions[Player.YOU | Player.RIVAL]`;
`board.bfs(start, blocked=...) -> (dist, first_move)`;
`board.make_player_move(state, move, player)`; `board.rival_move(state)`; `ORDER`; `DELTA`.

**True objective.** Beyond "collect food": **collect more than the rival** — go for food you
reach *before* it (compare `d_you[f]` vs `d_rival[f]`), and sometimes deny it.

---

## 2. Why it's a good algorithms project

Adversarial, multi-agent, resource-collection on a graph — the intersection of:
1. BFS / shortest paths (primitive),
2. greedy heuristics (baseline),
3. adversarial game-tree search (minimax / expectimax vs a known opponent),
4. competitive orienteering (maximize collected reward while a competitor races you).

Non-trivial because "go to nearest food" is wrong: a second agent contests the food, so the
key quantity is the **distance race** `d_you[f]` vs `d_rival[f]`.

---

## 3. Research question

**Primary (recommended):**
> In a two-player competitive food-collection game on a grid against a fixed greedy
> (nearest-food BFS) opponent, how does the depth of adversarial lookahead affect the agent's
> food share and win rate — and at what depth do the gains stop justifying the added
> computation?

Fits the 35-pt "question" criterion: compares algorithms (depth-0 vs 1-ply vs k-ply), ties to
complexity (`5^k` states × BFS), clear metrics (food share, win rate, time/move), real
motivation (cheap greedy vs expensive search).

**Alternatives (pick one as primary if preferred):**
- **B — Contest-aware heuristic:** does scoring only food you win the race to
  (`d_you[f] < d_rival[f]`) beat plain nearest-food greedy, and by how much?
- **C — Denial/blocking:** does ever choosing a move that increases the rival's distance to
  food beat a purely food-seeking policy?
- **D — Map structure:** how do wall density / food count decide which strategy wins?

---

## 4. Algorithms to compare (all share BFS)

- **B0 Greedy:** BFS to nearest reachable food, step once (the starter).
- **A1 1-ply lookahead:** for each legal move, simulate your move then the rival's reply;
  score `(ate_now, block_rival, win_count, -nearest_dist)` (the Oct-29 version).
- **Ak k-ply search:** expand the ≤5 moves to depth k. Opponent is deterministic
  (`rival_move`), so it's forward simulation / minimax; evaluate leaves by "foods you'll win
  the race to." This exposes the `5^k` wall → motivates a depth cap / pruning.

---

## 5. Complexity

- BFS on 15×15 ≈ **O(225) = constant** per call.
- Greedy: one BFS/turn ⇒ **O(T)** over T moves.
- 1-ply: ≤5 candidates × a few BFS ⇒ constant × BFS per turn.
- k-ply: **O(5^k · 225)** per turn — the exponential that makes depth-vs-cost the whole story.

---

## 6. Evaluation plan

- Generate N random **connected** boards: wall density 10–40%, food 5–40, random `P`/`O` starts.
- Run each strategy vs the fixed greedy rival. Record: your food vs rival's, win/tie/loss,
  avg decision time, total turns.
- Plots: food-share & win-rate vs depth; time/move vs depth; win-rate vs wall density per strategy.
- Hypothesis: 1-ply captures most of the benefit; k≥3 adds little for the cost; contest-aware
  wins most in dense mazes/high-food-density.

---

## 7. Walk-through (talking track)

1. Restate the game + interface.
2. Frame as graph search + adversarial game.
3. Show B0 greedy's failure mode: walks to food the rival reaches first → wasted moves → timeout.
4. Introduce the distance race (`d_you` vs `d_rival`).
5. Build 1-ply, generalize to k-ply, hit the `5^k` wall → cap/prune.
6. Present metrics + expected results, each tied back to the question.

---

## 8. Ready-to-send proposal (the PDF's 5 required bullets)

1. **Title:** *Lookahead vs. Greed: How Search Depth Affects an Agent in a Competitive
   Grid-Foraging Game.*
2. **Research question:** How does adversarial lookahead depth affect an agent's food share and
   win rate against a fixed greedy opponent, and where do gains stop justifying the compute cost?
3. **Why it matters:** Isolates when cheap greedy heuristics suffice vs when adversarial search
   pays off — a core trade-off in real-time game AI and multi-agent planning under a time budget.
4. **Algorithms investigated:** BFS shortest paths; greedy nearest-food; 1-ply lookahead;
   k-ply minimax/expectimax against a known opponent; distance-race and denial heuristics.
5. **Evaluation:** Simulate all strategies on many randomized connected boards against the fixed
   greedy rival; measure food share, win rate, and decision time; plot performance and cost vs
   depth and vs wall density.

> Note: proposal was due Nov 10; final Nov 19. If the proposal isn't submitted, email it now.
