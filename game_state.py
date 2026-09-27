'''
Prologue comment
File: game_state.py
Description: Stores the current minesweeper game configuration and status
Inputs: Difficulty selection and game state updates from game-manager
Outputs: Board dimensions, mine count, flag counts, first move status, and the current game status
External sources: None
Author: Lydia Peng
Created: 9/15/26
'''
from dataclasses import dataclass, field
from enum import Enum

from difficulty import BEGINNER, INTERMEDIATE, EXPERT


class GameStatus(Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


DIFFICULTIES = {
    0: BEGINNER,
    1: INTERMEDIATE,
    2: EXPERT,
}

MAX_HINTS = 3


@dataclass
class GameState:
    difficulty: int
    flags_placed: int = 0
    status: GameStatus = GameStatus.PLAYING
    first_move: bool = True
    hints_used: int = 0

    mine_count: int = field(init=False)
    rows: int = field(init=False)
    columns: int = field(init=False)

    #initializes values that depend on the selected difficulty
    def __post_init__(self) -> None:
        self._apply_difficulty(self.difficulty)


    #loads the board dimensions and mine count based on the selected difficulty
    def _apply_difficulty(self, difficulty: int) -> None:
        if difficulty not in DIFFICULTIES:
            raise ValueError(
                "Difficulty must be 0 (Beginner), "
                "1 (Intermediate), or 2 (Expert)."
            )

        configuration = DIFFICULTIES[difficulty]

        self.difficulty = difficulty
        self.mine_count = configuration.mineCount
        self.rows = configuration.gridSize["row"]
        self.columns = configuration.gridSize["column"]

    #returns the number of unused flags without going below zero
    @property
    def flags_remaining(self) -> int:
        return max(0, self.mine_count - self.flags_placed)

    @property
    def hints_remaining(self) -> int:
        return max(0, MAX_HINTS - self.hints_used)

    #returns whether the game is currently being played
    @property
    def is_active(self) -> bool:
        return self.status == GameStatus.PLAYING

    #returns whether the game has been won or lost
    @property
    def is_game_over(self) -> bool:
        return self.status in (GameStatus.WON, GameStatus.LOST)

    #marks the first move as completed
    def complete_first_move(self) -> None:
        self.first_move = False

    #increases number of flags placed
    def record_flag_placed(self) -> None:
        if not self.is_active:
            raise RuntimeError("Cannot place a flag after the game has ended.")

        self.flags_placed += 1

    #decreases number of flags placed
    def record_flag_removed(self) -> None:
        if not self.is_active:
            raise RuntimeError("Cannot remove a flag after the game has ended.")

        if self.flags_placed == 0:
            raise ValueError("No flags have been placed.")

        self.flags_placed -= 1

    #changes game status to won
    def mark_won(self) -> None:
        if not self.is_active:
            raise RuntimeError("The game has already ended.")

        self.status = GameStatus.WON

    #changes game status to lost
    def mark_lost(self) -> None:
        if not self.is_active:
            raise RuntimeError("The game has already ended.")

        self.status = GameStatus.LOST

    #restores the game state to its starting values
    def reset(self, difficulty: int | None = None) -> None:
        if difficulty is not None:
            self._apply_difficulty(difficulty)

        self.flags_placed = 0
        self.hints_used = 0
        self.status = GameStatus.PLAYING
        self.first_move = True