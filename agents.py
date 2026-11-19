"""The strategies under study.

Each agent is a function agent(state, who) -> move in {U, D, L, R, S}.
Both agents share the same movement and food-collection rules (in game.py); they
differ only in which food they choose to chase. That single difference is the
independent variable of the whole experiment.

    greedy_agent          -- always head to the nearest reachable food (baseline)
    contest_aware_agent   -- head only to food you reach before the opponent

greedy_agent also serves as the fixed RIVAL policy, so both experiments face the
exact same opponent and are directly comparable.

HOW TO READ THIS FILE (demo order):
    1. _nearest            -> "pick the closest food from a list"   (shared helper)
    2. greedy_agent        -> 1 BFS, then _nearest over ALL food
    3. contest_aware_agent -> 2 BFS, filter to WINNABLE food, then _nearest
   The only real difference between 2 and 3 is the `winnable` filter.
"""

from game import bfs, ORDER, other


def _nearest(foods, dist, first_move):
    """The reachable food with the smallest (distance, tie-break) key, or None.

    foods       -- the candidate food cells to choose from
    dist        -- BFS distances from our position (cells missing = unreachable)
    first_move  -- BFS first step toward each cell

    Ties: if two foods are equally far, prefer the one whose first step comes
    earliest in ORDER (U, D, L, R). This makes every run deterministic -- the same
    board always produces the same game, which the paired experiment relies on.
    """
    # Drop any food we cannot reach at all (walled off, or blocked by the opponent).
    reachable = [food for food in foods if food in dist]
    if not reachable:
        return None
    # Sort key = (steps away, tie-break rank of the first move). min() takes the
    # smallest distance; on a tie, the smaller ORDER index (U=0 ... R=3) wins.
    return min(
        reachable,
        key=lambda food: (dist[food], ORDER.index(first_move[food]) if first_move[food] in ORDER else 99),
    )


def greedy_agent(state, who):
    """Baseline: BFS to the nearest reachable food and take the first step.

    It only looks at ITS OWN distances -- it never asks "will the opponent get
    there first?". That blind spot is what the research question is about.
    """
    me = state.pos[who]
    opponent = state.pos[other(who)]

    # Step 1: one BFS from my position. The opponent's cell is blocked because
    # you cannot move onto the other player.
    dist, first_move = bfs(state.board, me, blocked={opponent})

    # Step 2: choose the closest food out of ALL remaining food.
    target = _nearest(state.foods, dist, first_move)

    # Step 3: return the first step toward it ('S' = stay if nothing is reachable).
    return first_move[target] if target is not None else 'S'


def contest_aware_agent(state, who):
    """Contest-aware: chase only food you win the race to.

    Compute your distance to every food and the opponent's distance too. Keep the
    food where you are at least as close as the opponent (a tie counts as a win,
    because on your turn you move first). Head to the nearest such food. If you win
    the race to none, fall back to the nearest reachable food rather than idling.
    """
    me = state.pos[who]
    opponent = state.pos[other(who)]

    # Step 1: BFS from MY position (same as greedy).
    my_dist, my_first = bfs(state.board, me, blocked={opponent})

    # Step 2: BFS from the OPPONENT's position -- this is the extra work greedy
    # never does. It tells us how many steps the rival needs to reach each food.
    opp_dist, _ = bfs(state.board, opponent, blocked={me})

    # Step 3 (THE KEY IDEA): keep only food I can win the race to.
    #   - `food in my_dist`              I can reach it at all
    #   - `food not in opp_dist`         the rival can't reach it -> free food
    #   - `my_dist[food] <= opp_dist[food]`  I'm no farther than the rival.
    #     Why "<=" and not "<"? It's my turn now, so I move first: with equal
    #     distances I arrive one move ahead of the rival. A tie is a win.
    winnable = [
        food for food in state.foods
        if food in my_dist and (food not in opp_dist or my_dist[food] <= opp_dist[food])
    ]

    # Step 4: fallback. If I'm losing every race, don't stand still -- go for the
    # nearest food anyway (the rival might take a different target and leave it).
    pool = winnable if winnable else list(state.foods)

    # Step 5: same "pick nearest + first step" as greedy, but over the filtered pool.
    target = _nearest(pool, my_dist, my_first)
    return my_first[target] if target is not None else 'S'


# The opponent both agents are measured against. Fixed on purpose: if the rival
# changed between runs we could not tell whether a result came from our agent or
# from a different opponent.
rival_agent = greedy_agent
