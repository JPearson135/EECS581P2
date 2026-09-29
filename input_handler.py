'''
Prologue comment
File: input_handler.py
Description: Handles user input (mouse clicks and keyboard presses) and manages the game loop for Minesweeper. 
It connects the frontend display with the game logic in GameManager, updating the game state based on user actions.
Inputs: Mouse click positions, mouse button types, and keyboard key presses.
Outputs: Updated game state, board display, and timer updates.
External sources: Claude
Author: Andrew Kruckemyer
Created: 9/17/26


Edited by Courtney McCray on 9/27/2026
'''

import sys
import pygame
 
from game_manager import GameManager
import display
 
DIFFICULTY_LABELS = display.DIFFICULTY_LABELS
 
# class for running the minesweeper game
class MinesweeperGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Minesweeper")
        self.font = pygame.font.SysFont("arial", 24)
        self.big_font = pygame.font.SysFont("arial", 40, bold=True)
        self.clock = pygame.time.Clock()

        # game state
        self.screen_mode = "menu"
        self.manager = None
        self.screen = pygame.display.set_mode(display.MENU_SIZE)
 
        # timer state
        self.start_ticks = None
        self.frozen_elapsed = None
    
    # main game loop
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_click(event.pos, event.button)
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)
 
            if self.screen_mode == "menu":
                display.draw_menu(self.screen, self.font)
            else:
                display.draw_game(self.screen, self.font, self.big_font,
                                   self.manager, self._elapsed_seconds())
 
            pygame.display.flip()
            self.clock.tick(30)
 
        pygame.quit()
        sys.exit()
 
    # handle mouse inputs
    def _handle_click(self, pos, button):
        if self.screen_mode == "menu":
            self._handle_menu_click(pos)
        else:
            self._handle_game_click(pos, button)
 
    def _handle_menu_click(self, pos):
        for i in range(len(DIFFICULTY_LABELS)):
            if display.menu_button_rect(i).collidepoint(pos):
                self._start_game(i)
                return

    # handle game clicks (left click to reveal, right click to flag)
    def _handle_game_click(self, pos, button):
        x, y = pos
        state = self.manager.get_state()

        # Handle theme buttons first.
        # These should work even after the game is over.
        if button == 1:
            if display.theme_button_rect(
                state, "light", self.screen.get_width()
            ).collidepoint(pos):
                display.set_theme("light")
                return

            if display.theme_button_rect(
                state, "dark", self.screen.get_width()
            ).collidepoint(pos):
                display.set_theme("dark")
                return

        # Ignore clicks in the top status bar.
        if y < display.TOP_BAR_HEIGHT:
            return

        # do not allow board clicks after the game is over
        if not state.is_active:
            return
        
        board_rect, cell_size = display.board_geometry(self.screen, state)
        if not board_rect.collidepoint(pos):
            return

        row = (y - board_rect.top) // cell_size
        col = (x - board_rect.left) // cell_size
        display.set_last_click(row, col)
 
        # left click to reveal square
        if button == 1:
            was_first_move = state.first_move
            self.manager.reveal(row, col)

            #start the timer when the first quare is actually revealed
            if was_first_move and not self.manager.get_state().first_move:
                self.start_ticks = pygame.time.get_ticks()

        # right click to flag square
        elif button == 3:
            self.manager.toggle_flag(row, col)


    # handle keyboard inputs
    def _handle_keydown(self, key):
        if self.screen_mode != "playing":
            return

        # if key click is "r", restart the game with the same difficulty
        if key == pygame.K_r:
            display.clear_last_click()
            self._restart_game()

        elif key == pygame.K_h:
            was_first_move = self.manager.get_state().first_move
            self.manager.hint()

            if was_first_move and not self.manager.get_state().first_move:
                self.start_ticks = pygame.time.get_ticks()

        # if key click is "escape", go back to the main menu
        elif key == pygame.K_ESCAPE:
            display.clear_last_click()
            self._go_to_menu()
 
    # start a new game with the selected difficulty
    def _start_game(self, difficulty_index):
        self.manager = GameManager(difficulty_index)
        self.screen_mode = "playing"
        self.start_ticks = None
        self.frozen_elapsed = None

        state = self.manager.get_state()

        # window_w = max(state.columns * display.CELL_SIZE, display.MIN_WINDOW_WIDTH)
        # window_h = state.rows * display.CELL_SIZE + display.TOP_BAR_HEIGHT

        self.screen = pygame.display.set_mode(
            display.game_window_size(state)
        )
 
    # restart the game with the same difficulty
    def _restart_game(self):
        # get difficulty from current game and restart with same difficulty
        difficulty = self.manager.get_state().difficulty
        self._start_game(difficulty)
 
    # go back to main menu function
    def _go_to_menu(self):
        # reset game state
        self.screen_mode = "menu"
        self.manager = None
        self.start_ticks = None
        self.frozen_elapsed = None

        # reset the display to menu size
        self.screen = pygame.display.set_mode(display.MENU_SIZE)
    
    # calculate total time in seconds since game started, or frozen time if game is over
    def _elapsed_seconds(self):
        if self.start_ticks is None:
            return 0.0

        state = self.manager.get_state()

        # if the game is over, freeze the timer and return the frozen time
        if not state.is_active:
            if self.frozen_elapsed is None:
                self.frozen_elapsed = (pygame.time.get_ticks() - self.start_ticks) / 1000

            return self.frozen_elapsed

        # otherwise, game is still active, return the elapsed time since the game started
        return (pygame.time.get_ticks() - self.start_ticks) / 1000
 
# main function to start the game
def main():
    game = MinesweeperGame()
    game.run()
 
 
if __name__ == "__main__":
    main()
