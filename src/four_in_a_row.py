#!/usr/bin/env python3
from enum import Enum
import numpy as np


class Player(Enum):
    Empty: int = 0
    Red: int = 1
    Yellow: int = 2


class Board:
    ROW = 6
    COL = 7

    def __init__(self):
        self.board = np.full((self.ROW, self.COL), Player.Empty)


    def occupied_by(self, row: int, col: int) -> str:
        '''
        Return the string representation of the player who occupies the cell.

        Args:
            row (int): row
            col (int): column

        Return:
            the string representation of the player who occupies the cell.
        '''
        occupied_by_dict = {
            Player.Empty: ' ',
            Player.Red: 'R',
            Player.Yellow: 'Y',
        }
        return occupied_by_dict.get(self.board[row, col])


    def show(self) -> None:
        '''Print the board'''
        # Print header
        col_str = '  | '
        col_str += ' | '.join([str(i) for i in range(self.COL)])
        col_str += ' |'
        print(col_str)

        # Print all the rows
        for r in range(self.ROW):
            row_occupied = [self.occupied_by(r,c) for c in range(self.COL)]
            row_str = f'{r} | '
            row_str += ' | '.join(row_occupied)
            row_str += ' |'
            print(row_str)
        print()


    def is_cell_empty(self, row: int, col: int) -> bool:
        '''
        Check if a cell in the board is empty.

        Args:
            row (int): row
            col (int): column

        Return:
            True if the cell is empty
        '''
        return self.board[row, col] == Player.Empty


    def has_empty_cell(self, col: int) -> bool:
        '''
        Check if a column in the board has an empty cell.

        Args:
            col (int): column

        Return:
            True if there is an empty cell in the column
        '''
        for row in range(self.ROW):
            if self.is_cell_empty(row, col):
                return True
        return False


    def insert(self, player: Player, col:int) -> None:
        '''
        Insert a chip into a column. The chip will be in the first empty cell.

        Args:
            player (Player): the player who inserts the chip
            col (int): the column to insert
        '''
        for row in range(self.ROW):
            if self.is_cell_empty(row, col):
                if row == self.ROW - 1:
                    # The last row
                    self.board[row, col] = player
                else:
                    if not self.is_cell_empty(row + 1, col):
                        self.board[row, col] = player

    def check_winner(self) -> Optional[Player]:
        for row in range(self.ROW):
            for col in range(self.COL - 3):
                chips = set([self.board[row, col + i] for i in range(4)])
                if len(chips) == 1:
                    if ( winner := chips.pop() ) != Player.Empty:
                        return winner

        for col in range(self.COL):
            for row in range(self.ROW - 3):
                chips = set([self.board[row + i, col] for i in range(4)])
                if len(chips) == 1:
                    if ( winner := chips.pop() ) != Player.Empty:
                        return winner

        for row in range(self.ROW - 3):
            for col in range(self.COL - 3):
                chips = set([self.board[row + i, col + i] for i in range(4)])
                if len(chips) == 1:
                    if ( winner := chips.pop() ) != Player.Empty:
                        return winner

        for row in range(self.ROW - 3):
            for col in range(3, self.COL):
                chips = set([self.board[row + i, col - i] for i in range(4)])
                if len(chips) == 1:
                    if ( winner := chips.pop() ) != Player.Empty:
                        return winner

        return None

    def play(self):
        self.show()

        player = Player.Yellow
        while True:
            input_str = input("Enter the column number or 'q' to quit: ").strip()
            if input_str == 'q':
                return

            try:
                col = int(input_str)
            except ValueError:
                continue
            if not self.has_empty_cell(col):
                continue

            self.insert(player, col)
            player = Player.Yellow if player == Player.Red else Player.Red

            self.show()
            if (winner := self.check_winner()):
                print(f'{winner} won')
                break


def main():
    board = Board()
    board.play()


if __name__ == '__main__':
    main()
