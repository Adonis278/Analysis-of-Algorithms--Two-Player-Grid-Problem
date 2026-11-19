"""Draw the board pictures used in the README and the walkthrough doc.

Writes three PNGs to docs/images/:
    example_board.png   a real 15x15 board exactly as the experiment generates it
    demo_race.png       the 5x5 demo board, each food labelled "you / rival" distance
    demo_paths.png      greedy vs contest-aware on the demo board, paths drawn in

Run:  python draw_boards.py
"""

import os

import matplotlib
matplotlib.use('Agg')                      # write files, no window
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from boards import generate_valid_board
from game import bfs, YOU, RIVAL
from agents import greedy_agent, contest_aware_agent
from demo import demo_setup, play_with_trace

OUT_DIR = os.path.join('docs', 'images')

# One colour per kind of cell, reused in every picture.
COLORS = {
    'empty': '#ffffff',
    'wall': '#3b3b3b',
    'you': '#2563eb',        # blue
    'rival': '#ea580c',      # orange
    'food': '#16a34a',       # green
    'win': '#dcfce7',        # light green background: food you win the race to
    'lose': '#fee2e2',       # light red background: food the rival wins
    'grid': '#c7c7c7',
}


def draw_grid(ax, board, you, rival, foods, food_bg=None, labels=None):
    """Draw one board on a matplotlib axis.

    food_bg: optional {food_cell: colour} to shade food cells (win/lose).
    labels:  optional {cell: text} small text printed under the cell's letter.
    Row 0 is drawn at the top so the picture matches the printed boards.
    """
    n = board.size
    for r in range(n):
        for c in range(n):
            cell = (r, c)
            face = COLORS['wall'] if cell in board.walls else COLORS['empty']
            if food_bg and cell in food_bg:
                face = food_bg[cell]
            # (x, y) = (col, n-1-row) so row 0 is at the top.
            ax.add_patch(Rectangle((c, n - 1 - r), 1, 1, facecolor=face,
                                   edgecolor=COLORS['grid'], linewidth=0.8))

    def letter(cell, text, colour):
        r, c = cell
        dy = 0.12 if labels and cell in labels else 0
        ax.text(c + 0.5, n - 1 - r + 0.5 + dy, text, ha='center', va='center',
                fontsize=14 if n <= 6 else 9, fontweight='bold', color=colour)

    for food in foods:
        letter(food, 'F', COLORS['food'])
    letter(you, 'P', COLORS['you'])
    letter(rival, 'O', COLORS['rival'])

    if labels:
        for (r, c), text in labels.items():
            ax.text(c + 0.5, n - 1 - r + 0.22, text, ha='center', va='center',
                    fontsize=8, color='#333333')

    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect('equal')
    # Axis ticks show (row, col) coordinates so cells can be named in the talk.
    ax.set_xticks([c + 0.5 for c in range(n)])
    ax.set_xticklabels(range(n), fontsize=7 if n > 6 else 9)
    ax.set_yticks([n - 1 - r + 0.5 for r in range(n)])
    ax.set_yticklabels(range(n), fontsize=7 if n > 6 else 9)
    ax.set_xlabel('col')
    ax.set_ylabel('row')
    ax.tick_params(length=0)


def legend_handles():
    from matplotlib.lines import Line2D
    def dot(colour, text):
        return Line2D([], [], marker='s', linestyle='', markersize=10,
                      markerfacecolor=colour, markeredgecolor='#999999', label=text)
    return [dot(COLORS['you'], 'P = YOU (agent under test)'),
            dot(COLORS['rival'], 'O = RIVAL (fixed greedy)'),
            dot(COLORS['food'], 'F = food'),
            dot(COLORS['wall'], 'wall')]


def draw_example_board():
    """A real experiment board: 25% walls, 15 food, seed 42."""
    setup = generate_valid_board(density=0.25, n_food=15, seed=42)
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    draw_grid(ax, setup['board'], setup['you'], setup['rival'], setup['foods'])
    ax.set_title('Example experiment board (15x15, 25% walls, 15 food)')
    ax.legend(handles=legend_handles(), loc='upper center',
              bbox_to_anchor=(0.5, -0.09), ncol=2, frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, 'example_board.png'), dpi=130)
    plt.close(fig)


def draw_demo_race():
    """The demo start position with the race table drawn onto the food cells."""
    setup = demo_setup()
    board, you, rival, foods = setup['board'], setup['you'], setup['rival'], setup['foods']
    my_dist, _ = bfs(board, you, blocked={rival})
    opp_dist, _ = bfs(board, rival, blocked={you})

    food_bg, labels = {}, {}
    for food in foods:
        win = my_dist[food] <= opp_dist[food]
        food_bg[food] = COLORS['win'] if win else COLORS['lose']
        labels[food] = f'you {my_dist[food]} / rival {opp_dist[food]}'

    fig, ax = plt.subplots(figsize=(5.6, 5.8))
    draw_grid(ax, board, you, rival, foods, food_bg=food_bg, labels=labels)
    ax.set_title('Demo board: the race to each food\n'
                 'green = you win the race,  red = rival gets there first', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, 'demo_race.png'), dpi=130)
    plt.close(fig)


def _path(frames, who):
    """The sequence of cells `who` stood on during a traced game."""
    cells = [frames[0]['state'].pos[who]]
    for frame in frames[1:]:
        if frame['who'] == who:
            cells.append(frame['state'].pos[who])
    return cells


def draw_demo_paths():
    """Side by side: the full game for greedy and for contest-aware."""
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 6.0), layout='constrained')
    for ax, (name, agent) in zip(axes, (('Greedy', greedy_agent),
                                        ('Contest-aware', contest_aware_agent))):
        setup = demo_setup()
        frames = play_with_trace(setup, agent)
        final = frames[-1]['state']
        draw_grid(ax, setup['board'], setup['you'], setup['rival'], setup['foods'])

        n = setup['board'].size
        for who, colour, offset in ((YOU, COLORS['you'], -0.08), (RIVAL, COLORS['rival'], 0.08)):
            cells = _path(frames, who)
            xs = [c + 0.5 + offset for _, c in cells]
            ys = [n - 1 - r + 0.5 + offset for r, _ in cells]
            ax.plot(xs, ys, color=colour, linewidth=3, alpha=0.75, marker='o', markersize=4)
            # Number each step so the path can be read in order. If a player
            # revisits a cell (greedy doubles back), show both turns: "1,3".
            steps_at = {}
            for step, (x, y) in enumerate(zip(xs[1:], ys[1:]), start=1):
                steps_at.setdefault((x, y), []).append(str(step))
            for (x, y), steps in steps_at.items():
                ax.text(x + 0.18, y + 0.18, ','.join(steps), fontsize=8, color=colour,
                        fontweight='bold')

        verdict = ('WIN' if final.score[YOU] > final.score[RIVAL]
                   else 'LOSS' if final.score[YOU] < final.score[RIVAL] else 'TIE')
        ax.set_title(f'{name}: YOU {final.score[YOU]} - RIVAL {final.score[RIVAL]}  ({verdict})',
                     fontsize=11)

    fig.suptitle('Same board, same rival - only the target choice differs\n'
                 'blue = YOU\'s path,  orange = RIVAL\'s path,  numbers = turn', fontsize=10)
    fig.savefig(os.path.join(OUT_DIR, 'demo_paths.png'), dpi=130)
    plt.close(fig)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    draw_example_board()
    draw_demo_race()
    draw_demo_paths()
    print(f'Board pictures written to {OUT_DIR}/')


if __name__ == '__main__':
    main()
