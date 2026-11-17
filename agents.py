"""The strategies under study.

Each agent is a function agent(state, who) -> move in {U, D, L, R, S}.
Both agents share the same movement and food-collection rules (in game.py); they
differ only in which food they choose to chase. That single difference is the
independent variable of the whole experiment.

    greedy_agent          -- always head to the nearest reachable food (baseline)
    contest_aware_agent   -- head only to food you reach before the opponent

greedy_agent also serves as the fixed RIVAL policy, so both experiments face the
exact same opponent and are directly comparable.
"""

from game import bfs, ORDER, other


def _nearest(foods, dist, first_move):
    """The reachable food with the smallest (distance, tie-break) key, or None."""
    reachable = [food for food in foods if food in dist]
    if not reachable:
        return None
    return min(
        reachable,
        key=lambda food: (dist[food], ORDER.index(first_move[food]) if first_move[food] in ORDER else 99),
    )


def greedy_agent(state, who):
    """Baseline: BFS to the nearest reachable food and take the first step."""
    me = state.pos[who]
    opponent = state.pos[other(who)]
    dist, first_move = bfs(state.board, me, blocked={opponent})
    target = _nearest(state.foods, dist, first_move)
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
    my_dist, my_first = bfs(state.board, me, blocked={opponent})
    opp_dist, _ = bfs(state.board, opponent, blocked={me})

    winnable = [
        food for food in state.foods
        if food in my_dist and (food not in opp_dist or my_dist[food] <= opp_dist[food])
    ]
    pool = winnable if winnable else list(state.foods)
    target = _nearest(pool, my_dist, my_first)
    return my_first[target] if target is not None else 'S'


# The opponent both agents are measured against. Fixed on purpose.
rival_agent = greedy_agent
