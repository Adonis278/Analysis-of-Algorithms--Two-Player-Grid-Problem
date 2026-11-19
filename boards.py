"""Random board generation with a connectivity guarantee.

A board is only useful if the two players and (most of) the food actually sit in
one connected open region -- otherwise the game is trivially unwinnable or the
comparison is noise. generate_valid_board keeps drawing random boards (advancing
the seed) until one passes that check, so experiments are both random and fair.

generate_valid_board(density, n_food, seed) -> dict(board, you, rival, foods)
"""

import random

from game import Board, N, ORDER, DELTA

MIN_FOOD_CONNECTED = 0.90   # at least this fraction of food must be reachable
MAX_ATTEMPTS = 500          # seeds to try before giving up


def _open_component(board, start):
    """All passable cells reachable from `start` (flood fill, players ignored).

    Same idea as BFS but we only need WHICH cells are reachable, not how far,
    so a simple stack (depth-first) is enough. O(N^2).
    """
    seen = {start}
    stack = [start]
    while stack:
        cur = stack.pop()
        for move in ORDER:
            drow, dcol = DELTA[move]
            nxt = (cur[0] + drow, cur[1] + dcol)
            if nxt not in seen and board.passable(nxt):
                seen.add(nxt)
                stack.append(nxt)
    return seen


def _draw_board(density, n_food, seed):
    """Draw one candidate board from `seed` (may be invalid)."""
    # Our own seeded random generator: the same seed always draws the same board,
    # so anyone re-running the experiment gets identical results.
    rng = random.Random(seed)
    cells = [(r, c) for r in range(N) for c in range(N)]

    # Each cell independently becomes a wall with probability `density`
    # (0.10 = open field, 0.40 = tight maze).
    walls = {cell for cell in cells if rng.random() < density}
    open_cells = [cell for cell in cells if cell not in walls]
    if len(open_cells) < n_food + 2:        # need room for P, O, and the food
        return None

    # Pick n_food + 2 DISTINCT open cells: first is YOU, second is RIVAL, rest are food.
    picks = rng.sample(open_cells, n_food + 2)
    you, rival = picks[0], picks[1]
    foods = set(picks[2:])
    return {'board': Board(walls), 'you': you, 'rival': rival, 'foods': foods}


def _is_valid(setup):
    """True if rival and >= MIN_FOOD_CONNECTED of the food share YOU's region."""
    region = _open_component(setup['board'], setup['you'])
    if setup['rival'] not in region:
        return False
    if not setup['foods']:
        return False
    connected = sum(1 for food in setup['foods'] if food in region)
    return connected >= MIN_FOOD_CONNECTED * len(setup['foods'])


def generate_valid_board(density, n_food, seed):
    """Return the first valid board at or after `seed`.

    Raises RuntimeError if no valid board is found within MAX_ATTEMPTS (only
    happens for impossible parameters, e.g. near-total wall density).
    """
    for attempt in range(MAX_ATTEMPTS):
        # Rejection sampling: draw, check, and if it fails try the next seed.
        # 7919 is just a prime step so retries land on well-spread seeds.
        setup = _draw_board(density, n_food, seed + attempt * 7919)
        if setup is not None and _is_valid(setup):
            # Keep only the food that is actually reachable, so scores are clean.
            region = _open_component(setup['board'], setup['you'])
            setup['foods'] = {food for food in setup['foods'] if food in region}
            return setup
    raise RuntimeError(f'no valid board for density={density}, n_food={n_food}')
