'''
Prologue comment
File: game_manager.py
Description: Manages player actions and connects the frontend to the board and game state logic
Inputs: Difficulty selections and row/column positions from the frontend
Outputs: Updated tiles, board data, flag counts, and win/loss status. 
External sources: None
Author: Lydia Peng
Created: 9/15/26

Date modified: 9/29/26
Editor: Sam Prestigiacomo
Modifications: Added sound effect for when mine hit using pygame's mixer module which loads the audio.
External Sources:
Pygame Documentation - https://www.pygame.org/docs/ref/mixer.html
'''
from random import randint
from pathlib import Path
from board import Board
from game_state import GameState
import pygame

_audio_unavailable = False
_sound_effect = None
_sound_path = Path(__file__).with_name("sound.mp3")


def _play_mine_sound() -> None:
    global _audio_unavailable, _sound_effect

    if _audio_unavailable:
        return

    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
        if _sound_effect is None:
            _sound_effect = pygame.mixer.Sound(str(_sound_path))
        _sound_effect.play()
    except (OSError, pygame.error):
        _audio_unavailable = True


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
            _play_mine_sound()

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

    def easy_guess(self):
        row_guess = randint(0,self.state.rows)
        col_guess = randint(0,self.state.columns)
        if(self.is_valid_position(row_guess,col_guess)):
            tile = self._get_tile(row_guess,col_guess)
            if not tile.revealed:
                return{row_guess,col_guess}



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