#!/usr/bin/env python
'''
A script to play Tic Tac Toe against the computer.
This script demonstrates the Minimax algorithm.
'''
import argparse
import math
import random
import uuid


class TicTacToe:
    '''The classic Tic Tac Toe board game'''
    human = 'O'        # A cell occupied by the human
    machine = 'X'      # A cell occupied by the machine
    empty = ' '        # An empty cell
    tie = 'T'          # Represent the tie result

    def __init__(self, size: int = 3) -> None:
        '''Constructor

        Args:
            size (int): the size of the board
        '''
        self.size = size
        self.board = [[self.empty for _ in range(self.size)]
                      for _ in range(self.size)]

    def draw(self) -> None:
        '''Draw the board on the console screen'''
        col = [str(i) for i in range(self.size)]
        col_str = '    ' + '   '.join(col)
        print(col_str)
        for row in range(self.size):
            content = f'{row} | ' + ' | '.join(self.board[row]) + ' |'
            print(content)
        print()

    def check_winner(self) -> str:
        '''Check if there is a winner

        Returns:
            the winner ('O' or 'X'), draw ('T') or no winner yet (None)
        '''
        # horizontal
        for row in range(self.size):
            value = list(set(self.board[row][i] for i in range(self.size)))
            if len(value) == 1 and value[0] != self.empty:
                return value[0]

        # vertical
        for col in range(self.size):
            value = list(set(self.board[i][col] for i in range(self.size)))
            if len(value) == 1 and value[0] != self.empty:
                return value[0]

        # diagonal
        value = list(set(self.board[row][row] for row in range(self.size)))
        if len(value) == 1 and value[0] != self.empty:
            return value[0]
        value = list(set(self.board[row][self.size - row - 1]
                         for row in range(self.size)))
        if len(value) == 1 and value[0] != self.empty:
            return value[0]

        empty_count = [self.board[r][c] for r in range(self.size)
                       for c in range(self.size) if self.board[r][c] == self.empty]
        if len(empty_count) == 0:
            return self.tie

        return None

    def minimax(self, depth: int, is_maximizing: bool) -> int:
        '''An implementation of the Minimax algorithm

        Arguments:
            depth (int): the current depth in the decision tree. We don't use
                         this here because the decision of the tree for Tic Tac
                         Toe is not that deep. For some other games, we may need
                         to limit the depth that the algorithm can go to yield
                         reasonable response time

            is_maximizing (bool): operating as a maximizer or a minimizer

        Returns:
            (int) the score of this path. -1 and 1 for losing and winning outcomes
            respectively
        '''
        result = self.check_winner()
        if result:
            if result == self.tie:
                return 0
            if result == self.human:
                return -1
            return 1

        if is_maximizing:
            best_score = -math.inf
            for row in range(self.size):
                for col in range(self.size):
                    if self.board[row][col] != self.empty:
                        continue
                    self.board[row][col] = self.machine
                    score = self.minimax(depth + 1, False)
                    best_score = max(best_score, score)
                    self.board[row][col] = self.empty
        else:
            best_score = math.inf
            for row in range(self.size):
                for col in range(self.size):
                    if self.board[row][col] != self.empty:
                        continue
                    self.board[row][col] = self.human
                    score = self.minimax(depth + 1, True)
                    best_score = min(best_score, score)
                    self.board[row][col] = self.empty
        return best_score

    def best_move(self) -> None:
        '''For the computer to choose his next best move, one with the
        highest score according to the minimax algorithm'''
        best_score = -10
        move_row = move_col = None
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] != self.empty:
                    continue
                self.board[row][col] = self.machine
                score = self.minimax(0, False)
                self.board[row][col] = self.empty

                if score >= best_score:
                    best_score = score
                    move_row, move_col = row, col
        self.board[move_row][move_col] = self.machine

    def random_move(self) -> None:
        '''Choose an empty cell randomly'''
        empty_cells = []
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == self.empty:
                    empty_cells.append((row, col))
        r, c = random.choice(empty_cells)
        self.board[r][c] = self.machine

    def coin_toss(self) -> bool:
        '''Toss a coin

        Returns:
            (bool) either True or False 50% of the times
        '''
        gen_id = str(uuid.uuid4())
        while not gen_id[0].isnumeric():
            gen_id = str(uuid.uuid4())
        return int(gen_id[0]) >= 5

    def play(self, difficulty: int = None, human_first: bool = None) -> None:
        '''Play the game against the computer

        Args:
            difficulty (int): difficulty level

            human_first (bool): the first move is for the human or machine
        '''
        count = 0
        human = human_first if human_first else self.coin_toss()

        if human:
            self.draw()

        while count < self.size * self.size:
            if human:
                input_str = input("Enter 'q' to quit or row col e.g. 1 2: ").strip()
                if input_str == 'q':
                    return
                row, col = input_str.split(' ')
                row, col = int(row), int(col)
                if (row >= self.size or col >= self.size) or \
                        self.board[row][col] != self.empty:
                    continue
                self.board[row][col] = self.human
                print()
            else:
                if difficulty == 3:
                    self.best_move()
                elif difficulty == 2:
                    if self.coin_toss():
                        self.best_move()
                    else:
                        self.random_move()
                else:
                    self.random_move()
                print("Machine's turn\n")
            self.draw()
            count += 1
            human = not human

            if not (winner := self.check_winner()):
                continue
            message = 'Tie!' if winner == self.tie else f'{winner} won!'
            print(message)
            break


def process_arguments() -> argparse.Namespace:
    '''Process commandline arguments

    return:
        a Parameters object which contains all command line arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--difficulty', action='store', dest='difficulty',
                        choices=['1', '2', '3'], default='3',
                        help='Choose the difficulty level')
    parser.add_argument('-H', '--human-first', action='store_true', dest='human_first',
                        help='Let the human play first')
    return parser.parse_args()


def main():
    '''The main program'''
    args = process_arguments()
    game = TicTacToe()
    difficulty = int(args.difficulty)
    game.play(difficulty=difficulty, human_first=args.human_first)


if __name__ == '__main__':
    main()
