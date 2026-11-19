"""Turn-by-turn demo: watch greedy and contest-aware play the SAME small board.

This is the "walk it through by hand" script for the presentation. It uses a tiny
5x5 board (small enough to trace on paper), playing the SAME fixed greedy rival,
where the two strategies end with opposite results:

    greedy        loses 0-3   (it chases food the rival is closer to)
    contest-aware wins  2-1   (it skips that food and takes the two it can win)

Run:  python demo.py

Legend in the printed boards:
    P = YOU (the agent being tested)    O = RIVAL (fixed greedy opponent)
    F = food                            # = wall          . = empty
"""

from game import Board, GameState, apply_move, bfs, can_reach_any_food, YOU, RIVAL, other
from agents import greedy_agent, contest_aware_agent, rival_agent

# ---------------------------------------------------------------------------
# The demo board (coordinates are (row, col); row 0 is the top).
#
#        col: 0 1 2 3 4
#     row 0   . . . F F
#     row 1   # . . . .
#     row 2   . . P . .
#     row 3   . . . F O
#     row 4   . . . . .
#
# Chosen so that no two foods are ever tied in distance during either game:
# every decision below is explained by distances alone, never by tie-breaking.
# ---------------------------------------------------------------------------
DEMO_SIZE = 5
DEMO_WALLS = {(1, 0)}
DEMO_YOU = (2, 2)
DEMO_RIVAL = (3, 4)
DEMO_FOODS = {(0, 3), (0, 4), (3, 3)}


def demo_setup():
    """A fresh copy of the demo board in the same dict shape boards.py produces."""
    return {'board': Board(DEMO_WALLS, size=DEMO_SIZE), 'you': DEMO_YOU,
            'rival': DEMO_RIVAL, 'foods': set(DEMO_FOODS)}


def render(state):
    """Return the board as a list of text rows (P, O, F, #, .)."""
    rows = []
    for r in range(state.board.size):
        line = []
        for c in range(state.board.size):
            cell = (r, c)
            if cell == state.pos[YOU]:
                line.append('P')
            elif cell == state.pos[RIVAL]:
                line.append('O')
            elif cell in state.board.walls:
                line.append('#')
            elif cell in state.foods:
                line.append('F')
            else:
                line.append('.')
        rows.append(' '.join(line))
    return rows


def race_table(state):
    """For each food: YOUR distance, RIVAL's distance, and who wins the race.

    This is exactly the comparison contest_aware_agent makes on every turn.
    """
    my_dist, _ = bfs(state.board, state.pos[YOU], blocked={state.pos[RIVAL]})
    opp_dist, _ = bfs(state.board, state.pos[RIVAL], blocked={state.pos[YOU]})
    lines = ['    food     you  rival  race']
    for food in sorted(state.foods):
        mine = my_dist.get(food)
        theirs = opp_dist.get(food)
        if mine is None:
            verdict = 'unreachable'
        elif theirs is None or mine <= theirs:
            verdict = 'WIN (you <= rival)'
        else:
            verdict = 'LOSE (rival closer)'
        lines.append(f'    {str(food):<8} {str(mine):>3}  {str(theirs):>5}  {verdict}')
    return lines


def play_with_trace(setup, you_agent, max_turns=50):
    """Play one game like game.run_game, but record every step.

    Returns a list of frames; each frame is a dict with the turn number, who
    moved, the move, both positions, remaining food and scores AFTER the move.
    (Same turn loop as run_game -- kept separate so the engine stays clean.)
    """
    state = GameState(setup['board'], setup['you'], setup['rival'], setup['foods'])
    frames = [{'turn': 0, 'who': None, 'move': None, 'state': state.copy()}]
    for turn in range(1, max_turns + 1):
        if not state.foods:
            break
        if not can_reach_any_food(state, YOU) and not can_reach_any_food(state, RIVAL):
            break
        for who, agent in ((YOU, you_agent), (RIVAL, rival_agent)):
            if not state.foods:
                break
            move = agent(state, who)
            apply_move(state, who, move)
            frames.append({'turn': turn, 'who': who, 'move': move, 'state': state.copy()})
    return frames


def print_game(title, you_agent):
    setup = demo_setup()
    frames = play_with_trace(setup, you_agent)
    print('=' * 60)
    print(title)
    print('=' * 60)
    for frame in frames:
        state = frame['state']
        if frame['who'] is None:
            print('Start position:')
        else:
            mover = 'YOU  ' if frame['who'] == YOU else 'RIVAL'
            print(f"Turn {frame['turn']}: {mover} plays {frame['move']}"
                  f"   score YOU {state.score[YOU]} - RIVAL {state.score[RIVAL]}")
        for row in render(state):
            print('    ' + row)
        # Show the race table before each of YOUR decisions (the interesting part).
        next_is_you = frame['who'] in (None, RIVAL)
        if next_is_you and state.foods:
            print('  Race table before YOUR next move:')
            for line in race_table(state):
                print(line)
        print()
    final = frames[-1]['state']
    result = ('WIN' if final.score[YOU] > final.score[RIVAL]
              else 'LOSS' if final.score[YOU] < final.score[RIVAL] else 'TIE')
    print(f'FINAL: YOU {final.score[YOU]} - RIVAL {final.score[RIVAL]}  -> {result}\n')


def main():
    print(__doc__)
    print_game('GREEDY  (always chase the nearest food)', greedy_agent)
    print_game('CONTEST-AWARE  (chase the nearest food you can WIN)', contest_aware_agent)


if __name__ == '__main__':
    main()
