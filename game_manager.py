'''
Prologue comment
File: game_manager.py
Description: Manages player actions and connects the frontend to the board and game state logic
Inputs: Difficulty selections and row/column positions from the frontend
Outputs: Updated tiles, board data, flag counts, and win/loss status. 
External sources: None
Author: Lydia Peng
Created: 9/15/26
'''
from board import Board
from game_state import GameState


class GameManager:
    #creates a new game manager 
    def __init__(self, difficulty: int):
        self.state = GameState(difficulty)
        self.board = None

    #checks whether a position is inside the board
    def is_valid_position(self, row: int, column: int) -> bool:
        return (
            0 <= row < self.state.rows
            and 0 <= column < self.state.columns
        )

    #starts a new game with the selected difficulty
    def start_game(self, difficulty: int) -> None:
        self.state = GameState(difficulty)
        self.board = None

    #reveals a tile and updates the game state
    def reveal(self, row: int, column: int):
        if not self.state.is_active:
            return None

        if not self.is_valid_position(row, column):
            raise ValueError("Position is outside the board.")

        if self.state.first_move:
            self._initialize_board(row, column)
            self.state.complete_first_move()

        tile = self._get_tile(row, column)

        if tile.isFlagged or tile.revealed:
            return None


        if tile.isMine:
            tile.revealed = True
            self.reveal_all_mines()
            self.state.mark_lost()
            return tile
        
        elif tile.adjacent == 0:
            self._flood_fill(row, column)
        else:
            tile.revealed = True

        if self.check_win():
            self.state.mark_won()

        return tile


    #creates the board after receiving the first clicked position
    def _initialize_board(self, row: int, column: int) -> None:
        self.board = Board(
            self.state.difficulty,
            row,
            column
        )

        self.board.makeBoard()


    #returns the tile located at the given row and column
    def _get_tile(self, row: int, column: int):
        if self.board is None:
            raise RuntimeError("The board has not been initialized.")

        width = self.board.dimension["column"]
        index = row * width + column

        return self.board.board[index]


    #places or removes a flag from a covered tile
    def toggle_flag(self, row: int, column: int) -> None:
        if not self.state.is_active:
            return 
        
        if not self.is_valid_position(row, column):
            raise ValueError("Position is outside the board.")
        
        if self.board is None:
            return
        
        tile = self._get_tile(row, column)

        if tile.revealed: 
            return
        
        if tile.isFlagged:
            self.state.record_flag_removed()
            tile.isFlagged = False
        else:
            self.state.record_flag_placed()
            tile.isFlagged = True

    #reveals one covered, non-mine tile while hint uses remain
    def hint(self):
        if not self.state.is_active or self.state.hints_remaining == 0:
            return None

        if self.state.first_move:
            self._initialize_board(0, 0)
            self.state.complete_first_move()

        if self.board is None:
            return None

        width = self.board.dimension["column"]
        for index, tile in enumerate(self.board.board):
            if tile.revealed or tile.isFlagged or tile.isMine:
                continue

            row, column = divmod(index, width)
            result = self.reveal(row, column)
            if result is not None:
                self.state.hints_used += 1
            return result

        return None


    #reveals connected empty tiles and their numbered borders using a stack-based flood fill algorithm
    def _flood_fill(self, row: int, column: int) -> None:
        stack = [(row, column)]

        while stack:
            current_row, current_column = stack.pop()

            if not self.is_valid_position(current_row, current_column):
                continue

            tile = self._get_tile(current_row, current_column)

            if tile.revealed or tile.isFlagged or tile.isMine:
                continue

            tile.revealed = True

            if tile.adjacent != 0:
                continue

            for row_offset in (-1, 0, 1):
                for column_offset in (-1, 0, 1):
                    if row_offset == 0 and column_offset == 0:
                        continue

                    stack.append(
                        (current_row + row_offset, current_column + column_offset)
                    )


    #checks whether every non-mine tile has been revealed
    def check_win(self) -> bool:
        if self.board is None:
            return False
        
        return all(
            tile.isMine or tile.revealed
            for tile in self.board.board
        )
    
    #reveals every mine after the player loses
    def reveal_all_mines(self) -> None:
        if self.board is None:
            return
        for tile in self.board.board:
            if tile.isMine:
                tile.revealed = True

    #restarts the game using the current difficulty
    def reset(self) -> None:
        self.start_game(self.state.difficulty)

    #returns current board
    def get_board(self):
        return self.board

    #returns current game state
    def get_state(self) -> GameState:
        return self.state