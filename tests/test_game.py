"""Correctness tests for the engine. Run with:  python -m pytest  (or unittest)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import (Board, bfs, legal_moves, GameState, apply_move,
                  run_game, can_reach_any_food, YOU, RIVAL)
from agents import greedy_agent, contest_aware_agent, rival_agent
from boards import generate_valid_board


class TestBFS(unittest.TestCase):
    def test_distances_on_open_grid(self):
        board = Board(walls=set(), size=5)
        dist, first = bfs(board, (0, 0))
        self.assertEqual(dist[(0, 0)], 0)
        self.assertEqual(dist[(0, 1)], 1)
        self.assertEqual(dist[(2, 3)], 5)            # Manhattan distance
        self.assertIn(first[(0, 4)], ('R',))         # straight line right

    def test_wall_blocks_path(self):
        # A vertical wall column 1 (rows 0..3) forces a detour through row 4.
        walls = {(r, 1) for r in range(4)}
        board = Board(walls=walls, size=5)
        dist, _ = bfs(board, (0, 0))
        # Detour: down 4 rows to (4,0), across columns 1-2, back up 4 rows = 10.
        self.assertEqual(dist[(0, 2)], 10)

    def test_blocked_cell_is_unreachable(self):
        board = Board(walls=set(), size=3)
        # Block the only two exits from the corner (0,0): (0,1) and (1,0).
        dist, _ = bfs(board, (0, 0), blocked={(0, 1), (1, 0)})
        self.assertNotIn((2, 2), dist)
        self.assertEqual(set(dist), {(0, 0)})


class TestMovesAndCollection(unittest.TestCase):
    def test_legal_moves_reject_wall_edge_and_opponent(self):
        board = Board(walls={(0, 1)}, size=3)
        moves = legal_moves(board, pos=(0, 0), other_pos=(1, 0))
        self.assertIn('S', moves)
        self.assertNotIn('U', moves)                 # off the top edge
        self.assertNotIn('L', moves)                 # off the left edge
        self.assertNotIn('R', moves)                 # wall at (0,1)
        self.assertNotIn('D', moves)                 # opponent at (1,0)

    def test_food_is_collected_and_scored(self):
        board = Board(walls=set(), size=3)
        state = GameState(board, you=(0, 0), rival=(2, 2), foods={(0, 1)})
        apply_move(state, YOU, 'R')
        self.assertEqual(state.pos[YOU], (0, 1))
        self.assertNotIn((0, 1), state.foods)
        self.assertEqual(state.score[YOU], 1)

    def test_illegal_move_keeps_player_put(self):
        board = Board(walls={(0, 1)}, size=3)
        state = GameState(board, you=(0, 0), rival=(2, 2), foods=set())
        apply_move(state, YOU, 'R')                  # into a wall
        self.assertEqual(state.pos[YOU], (0, 0))


class TestTermination(unittest.TestCase):
    def test_game_terminates_and_conserves_food(self):
        board = Board(walls=set(), size=5)
        setup = {'board': board, 'you': (0, 0), 'rival': (4, 4),
                 'foods': {(0, 2), (2, 2), (4, 0)}}
        result = run_game(setup, greedy_agent, rival_agent, max_turns=200)
        self.assertLessEqual(result['my_food'] + result['rival_food'], 3)
        self.assertGreater(result['turns'], 0)
        self.assertIn(result['outcome'], ('win', 'loss', 'tie'))

    def test_stalemate_when_no_food_reachable(self):
        # Food walled off in its own pocket: nobody can reach it.
        walls = {(0, 1), (1, 1), (1, 0)}
        board = Board(walls=walls, size=5)
        state = GameState(board, you=(4, 4), rival=(3, 3), foods={(0, 0)})
        self.assertFalse(can_reach_any_food(state, YOU))
        setup = {'board': board, 'you': (4, 4), 'rival': (3, 3), 'foods': {(0, 0)}}
        result = run_game(setup, greedy_agent, rival_agent, max_turns=200)
        self.assertEqual(result['my_food'] + result['rival_food'], 0)


class TestContestAwareBehaviour(unittest.TestCase):
    def test_contest_aware_skips_a_food_it_would_lose(self):
        # Open 5x5. YOU at (0,0), RIVAL at (0,3).
        #   F_lose (0,2): you need 2 steps, rival needs 1  -> rival wins it.
        #   F_win  (3,0): you need 3 steps, rival needs 6  -> you win it.
        # Greedy chases the NEAREST food (F_lose, dist 2) and steps 'R'.
        # Contest-aware skips the unwinnable F_lose and heads to F_win, stepping 'D'.
        board = Board(walls=set(), size=5)
        state = GameState(board, you=(0, 0), rival=(0, 3), foods={(0, 2), (3, 0)})
        self.assertEqual(greedy_agent(state, YOU), 'R')
        self.assertEqual(contest_aware_agent(state, YOU), 'D')

    def test_demo_board_outcomes(self):
        # The hand-walkthrough board in demo.py: greedy loses 0-3, contest-aware wins 2-1.
        from demo import demo_setup
        greedy = run_game(demo_setup(), greedy_agent, rival_agent)
        contest = run_game(demo_setup(), contest_aware_agent, rival_agent)
        self.assertEqual((greedy['my_food'], greedy['rival_food']), (0, 3))
        self.assertEqual((contest['my_food'], contest['rival_food']), (2, 1))


class TestBoardGeneration(unittest.TestCase):
    def test_generated_board_is_connected(self):
        from boards import _open_component
        setup = generate_valid_board(density=0.25, n_food=15, seed=42)
        region = _open_component(setup['board'], setup['you'])
        self.assertIn(setup['rival'], region)               # rival reachable
        for food in setup['foods']:                         # every kept food reachable
            self.assertIn(food, region)
        self.assertTrue(setup['foods'])                     # at least some food


class TestAgentsOnRandomBoards(unittest.TestCase):
    def test_both_agents_finish_valid_games(self):
        for index in range(20):
            setup = generate_valid_board(density=0.25, n_food=15, seed=1000 + index)
            for agent in (greedy_agent, contest_aware_agent):
                result = run_game(setup, agent, rival_agent)
                total = result['my_food'] + result['rival_food']
                self.assertLessEqual(total, result['total_food'])
                self.assertLess(result['turns'], 400)


if __name__ == '__main__':
    unittest.main()
