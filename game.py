"""Core engine for the two-player competitive foraging game.

A board is an N x N grid. Two players, YOU and RIVAL, start on separate cells.
They alternate turns (YOU first, then RIVAL). On a turn a player makes one move:
    U = up, D = down, L = left, R = right, S = stay.
Moving onto a food cell collects that food. A player's score is the number of
foods it has collected. The game ends when all food is gone, when neither player
can reach any remaining food, or when a turn cap is hit.

This module is pure game logic: it has no strategy in it. Strategies live in
agents.py. An "agent" is just a function agent(state, who) -> move.

HOW TO READ THIS FILE (demo order):
    Board        -> the walls and grid size (never changes during a game)
    bfs          -> shortest distances + "which way do I step first" (the core algorithm)
    GameState    -> what changes: positions, remaining food, scores
    apply_move   -> one player takes one step, collects food if they land on it
    run_game     -> the turn loop: YOU, then RIVAL, until the game ends

Coordinates are (row, col) with (0, 0) the TOP-LEFT corner, so 'U' is row - 1.
"""

from collections import deque
import time

N = 15                                   # board side length
ORDER = ['U', 'D', 'L', 'R']             # neighbour / tie-break order
DELTA = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1), 'S': (0, 0)}

YOU, RIVAL = 'YOU', 'RIVAL'


def other(who):
    """The opponent of `who`."""
    return RIVAL if who == YOU else YOU


class Board:
    """The static arena: its size and the set of wall cells."""

    def __init__(self, walls, size=N):
        self.walls = set(walls)
        self.size = size

    def in_bounds(self, cell):
        row, col = cell
        return 0 <= row < self.size and 0 <= col < self.size

    def passable(self, cell):
        """A cell a player may stand on: on the board and not a wall."""
        return self.in_bounds(cell) and cell not in self.walls


def bfs(board, start, blocked=frozenset()):
    """Breadth-first search from `start` over passable cells.

    `blocked` is a set of extra cells that may not be entered (pass the other
    player's current cell here, since you cannot move onto it).

    Returns (dist, first_move):
        dist[cell]       shortest number of steps from start to cell
        first_move[cell] the first move (U/D/L/R) to start heading toward cell
    Neighbours are explored in ORDER, so equal-distance ties resolve U, D, L, R.

    Why BFS (and not Dijkstra / A*)? Every move costs exactly 1 step, so BFS
    already finds shortest paths: it visits cells in order of distance 0, 1, 2...
    The first time a cell is reached is therefore via a shortest path.
    Cost: each of the N*N cells is enqueued at most once and checks 4 neighbours
    -> O(N^2) per call.
    """
    dist = {start: 0}            # doubles as the "visited" set
    first_move = {start: 'S'}
    queue = deque([start])       # FIFO queue -> cells come out in distance order
    while queue:
        cur = queue.popleft()
        for move in ORDER:
            drow, dcol = DELTA[move]
            nxt = (cur[0] + drow, cur[1] + dcol)
            if nxt in dist:                                  # already found (at <= distance)
                continue
            if not board.passable(nxt) or nxt in blocked:    # wall, off-grid, or the other player
                continue
            dist[nxt] = dist[cur] + 1
            # A direct neighbour of start commits to `move`; deeper cells inherit
            # the first step that led to their parent.
            first_move[nxt] = move if cur == start else first_move[cur]
            queue.append(nxt)
    return dist, first_move


def legal_moves(board, pos, other_pos):
    """Every move that keeps a player on a passable cell and off the opponent."""
    moves = ['S']
    for move in ORDER:
        drow, dcol = DELTA[move]
        nxt = (pos[0] + drow, pos[1] + dcol)
        if board.passable(nxt) and nxt != other_pos:
            moves.append(move)
    return moves


class GameState:
    """The changing part of a game: positions, remaining food, and scores."""

    def __init__(self, board, you, rival, foods):
        self.board = board
        self.pos = {YOU: you, RIVAL: rival}
        self.foods = set(foods)
        self.score = {YOU: 0, RIVAL: 0}

    def copy(self):
        twin = GameState(self.board, self.pos[YOU], self.pos[RIVAL], self.foods)
        twin.score = dict(self.score)
        return twin


def apply_move(state, who, move):
    """Move `who` by `move` (ignored if illegal) and collect food if landed on."""
    drow, dcol = DELTA[move]
    row, col = state.pos[who]
    nxt = (row + drow, col + dcol)
    # Only move if the target cell is legal: on the board, not a wall, not the opponent.
    # An illegal move is treated as 'S' (stay) instead of crashing the game.
    if move != 'S' and state.board.passable(nxt) and nxt != state.pos[other(who)]:
        state.pos[who] = nxt
    # Collection: standing on food eats it -- it disappears and the score goes up.
    here = state.pos[who]
    if here in state.foods:
        state.foods.discard(here)
        state.score[who] += 1


def can_reach_any_food(state, who):
    """True if `who` can reach at least one remaining food (opponent blocking)."""
    dist, _ = bfs(state.board, state.pos[who], blocked={state.pos[other(who)]})
    return any(food in dist for food in state.foods)


def run_game(setup, you_agent, rival_agent, max_turns=400):
    """Play one full game and return its result.

    `setup` is a dict with keys board, you, rival, foods (see boards.py).
    Returns a dict: my_food, rival_food, total_food, turns, avg_decision_ms,
    outcome ('win' / 'loss' / 'tie', from YOU's point of view).
    """
    state = GameState(setup['board'], setup['you'], setup['rival'], setup['foods'])
    total_food = len(state.foods)
    you_time = 0.0
    you_decisions = 0
    turns = 0

    for _ in range(max_turns):                       # safety cap: a game can never run forever
        # End condition 1: all food is gone.
        if not state.foods:
            break
        # End condition 2: stalemate -- neither player can reach any food that's left.
        if not can_reach_any_food(state, YOU) and not can_reach_any_food(state, RIVAL):
            break
        turns += 1

        # YOU moves first. We time only YOUR decision -- that is the
        # "ms per move" cost we compare between greedy and contest-aware.
        start = time.perf_counter()
        move = you_agent(state, YOU)
        you_time += time.perf_counter() - start
        you_decisions += 1
        apply_move(state, YOU, move)

        # YOU may have taken the last food; if so the rival doesn't move.
        if not state.foods:
            break
        # Then the RIVAL moves (always the fixed greedy policy).
        apply_move(state, RIVAL, rival_agent(state, RIVAL))

    my_food = state.score[YOU]
    rival_food = state.score[RIVAL]
    outcome = 'win' if my_food > rival_food else 'loss' if my_food < rival_food else 'tie'
    avg_ms = (you_time / you_decisions * 1000.0) if you_decisions else 0.0
    return {
        'my_food': my_food,
        'rival_food': rival_food,
        'total_food': total_food,
        'turns': turns,
        'avg_decision_ms': avg_ms,
        'outcome': outcome,
    }
