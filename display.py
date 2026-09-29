'''
Prologue comment
File: display.py
Description: Handles rendering for the Minesweeper game using pygame. Draws the difficulty selection menu, 
game grid with hidden, revealed and flagged cells, top status bar with remaining mine count and elapsed time after click and 
win loss screen after game has been played. 
Inputs: Pygame screen and font objects, the game manager and elapsed time.
Outputs: Rendered game menu and pygame display as well as clickable rectangles used by input_handler.py for menu hit detection
External sources: Claude
Author: Nick Heyer, Andrew Kruckemyer
Created: 9/17/26
'''

import pygame
from game_state import GameStatus

# required constants (referenced in input_handler.py)
# feel free to change these values
DIFFICULTY_LABELS = ["Beginner", "Intermediate", "Expert"]
MENU_SIZE = (300, 200)
TOP_BAR_HEIGHT = 72
CELL_SIZE = 30
MIN_WINDOW_WIDTH = 300

# added from Courtney for dark and light mode implementation

# width of the area to the right of the game board
SIDE_PANEL_WIDTH = 180
THEME_BUTTON_WIDTH = 140
THEME_BUTTON_HEIGHT = 40
SCREEN_MARGIN = 8
BORDER_WIDTH = 15


# basic colors used by the menu and game board

BACKGROUND_COLOR = (225, 225, 225)
BUTTON_COLOR = (190, 190, 190)
BUTTON_HOVER_COLOR = (210, 210, 210)
BORDER_COLOR = (90, 90, 90)
HIDDEN_CELL_COLOR = (180, 180, 180)
REVEALED_CELL_COLOR = (235, 235, 235)
TOP_BAR_COLOR = (205, 205, 205)
TEXT_COLOR = (20, 20, 20)
MINE_COLOR = (190, 40, 40)
FLAG_COLOR = (190, 40, 40)
NUMBER_COLORS = {
    1: (0, 0, 200),

    2: (0, 130, 0),

    3: (200, 0, 0),

    4: (0, 0, 120),

    5: (120, 0, 0),

    6: (0, 120, 120),

    7: (0, 0, 0),

    8: (90, 90, 90),
}

#Default: light mode, can switch to dark mode
LIGHT_THEME = {
    "background": (225, 225, 225),
    "button": (190, 190, 190),
    "button_hover": (210, 210, 210),
    "border": (90, 90, 90),
    "hidden": (180, 180, 180),
    "revealed": (235, 235, 235),
    "top_bar": (205, 205, 205),
    "text": (20, 20, 20),
}

DARK_THEME = {
    "background": (35, 35, 35),
    "button": (70, 70, 70),
    "button_hover": (90, 90, 90),
    "border": (150, 150, 150),
    "hidden": (75, 75, 75),
    "revealed": (110, 110, 110),
    "top_bar": (55, 55, 55),
    "text": (240, 240, 240),
}

CURRENT_THEME = LIGHT_THEME

# required funcions (referenced in input_handler.py)
# called in input_handler.py to get the clickable rect for the difficulty buttons

def menu_button_rect(index):
    """Returns the clickable rect for the difficulty button at `index`.
    Used by input_handler.py for click detection AND should be used
    here in draw_menu() so buttons are drawn exactly where clicks are
    detected. Feel free to change the layout -- just keep both uses in
    sync."""
    width, height = 200, 40
    x = (MENU_SIZE[0] - width) // 2
    y = 40 + index * (height + 10)
    return pygame.Rect(x, y, width, height)

# helper function for centering text inside a rectangle
def _draw_centered_text(screen, font, text, color, rect):
    text_surface = font.render(str(text), True, color)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)

# helper function for reading a value from either an object or dictionary
def _get_value(item, names, default=None):
    if item is None:
        return default
    for name in names:
        if isinstance(item, dict) and name in item:
            return item[name]
        if hasattr(item, name):
            return getattr(item, name)
    return default

# helper function for reading a row/column value from a state matrix
def _get_matrix_value(state, names, row, col):
    matrix = _get_value(state, names)
    if matrix is None:
        return None
    try:
        return matrix[row][col]
    except (TypeError, IndexError, KeyError):
        return None


# helper function for getting a cell from the board
def _get_cell(board, row, col):
    if board is None:  # board does not exist until the first reveal
        return None
    width = board.dimension["column"]
    try:
        return board.board[row * width + col]
    except (TypeError, IndexError):
        return None

# helper function that gets the display information for one cell
def _cell_info(state, cell, row, col):
    revealed = _get_value(
        cell,
        ["revealed", "is_revealed", "visible", "is_visible"]
    )
    flagged = _get_value(
        cell,
        ["isFlagged", "flagged", "is_flagged", "has_flag"]
    )
    is_mine = _get_value(
        cell,
        ["isMine", "is_mine", "mine", "has_mine"]
    )
    number = _get_value(
        cell,
        [
            "adjacent_mines",
            "adjacent",
            "neighbor_mines",
            "nearby_mines",
            "count"
        ]
    )

    # some implementations keep revealed/flagged information in GameState
    if revealed is None:
        revealed = _get_matrix_value(
            state,
            ["revealed", "revealed_cells", "visible_cells"],
            row,
            col
        )

    if flagged is None:
        flagged = _get_matrix_value(
            state,
            ["flags", "flagged", "flagged_cells"],
            row,
            col
        )

    # some cell implementations store the mine/number in a value field
    value = _get_value(cell, ["value"])
    if is_mine is None and isinstance(value, int):
        is_mine = value == -1
    if number is None and isinstance(value, int) and 0 <= value <= 8:
        number = value

    # support simple string boards as well as Cell objects
    if isinstance(cell, str):
        token = cell.strip().upper()
        if flagged is None:
            flagged = token in {"F", "FLAG", "⚑", "🚩"}

        if revealed is None:
            revealed = token not in {
                "",
                "#",
                "?",
                "HIDDEN",
                "COVERED",
                "UNREVEALED",
                "F",
                "FLAG",
                "⚑",
                "🚩"
            }

        if is_mine is None:
            is_mine = token in {"*", "M", "MINE", "X"}

        if number is None and token.isdigit():
            number = int(token)

    # support a simple integer board if that is what GameManager returns
    if isinstance(cell, int) and not isinstance(cell, bool):
        if is_mine is None:
            is_mine = cell == -1

        if number is None and 0 <= cell <= 8:
            number = cell

        if revealed is None:
            revealed = True

    if revealed is None:
        revealed = False

    if flagged is None:
        flagged = False

    if is_mine is None:
        is_mine = False

    return bool(revealed), bool(flagged), bool(is_mine), number


# helper function for counting the number of flags on the board
def _count_flags(state, board):
    count = 0
    for row in range(state.rows):

        for col in range(state.columns):

            cell = _get_cell(board, row, col)

            _, flagged, _, _ = _cell_info(state, cell, row, col)

            if flagged:

                count += 1

    return count


# helper function for getting the total number of mines from GameState
def _get_total_mines(state):
    total = _get_value(
        state,
        ["mine_count", "num_mines", "total_mines", "mines"]
    )

    if isinstance(total, int):

        return total

    if isinstance(total, (list, tuple, set)):

        return len(total)

    return None

# helper function for deciding which game-over message to show
def _game_over_message(state):
    status = _get_value(state, ["status", "game_status"])

    # use the imported GameStatus enum when its members are available
    if hasattr(GameStatus, "WON") and status == GameStatus.WON:
        return "You Win!"

    if hasattr(GameStatus, "WIN") and status == GameStatus.WIN:
        return "You Win!"

    if hasattr(GameStatus, "LOST") and status == GameStatus.LOST:
        return "Game Over"

    if hasattr(GameStatus, "LOSS") and status == GameStatus.LOSS:
        return "Game Over"

    status_name = getattr(status, "name", str(status)).upper()

    if "WIN" in status_name or "WON" in status_name:
        return "You Win!"

    if bool(_get_value(state, ["won", "is_won", "win"], False)):
        return "You Win!"

    return "Game Over"


def set_theme(theme_name):
    """Changes the current display theme."""
    global CURRENT_THEME

    if theme_name == "dark":
        CURRENT_THEME = DARK_THEME

    else:
        CURRENT_THEME = LIGHT_THEME

# Buttons for light/dark themes
def theme_button_rect(state, mode):
    """Returns the clickable rectangle for a theme button."""
    board_width = state.columns * CELL_SIZE
    x = board_width + 20

    if mode == "light":
        y = TOP_BAR_HEIGHT + 50

    else:
        y = TOP_BAR_HEIGHT + 105

    return pygame.Rect(
        x,
        y,
        THEME_BUTTON_WIDTH,
        THEME_BUTTON_HEIGHT

    )

# helper function for drawing the theme choice buttons for the user to click on
def _draw_theme_buttons(screen, font, state):
    """Draws the Light Mode and Dark Mode buttons beside the board."""
    mouse_pos = pygame.mouse.get_pos()

    # Light Mode button
    light_rect = theme_button_rect(state, "light")
    if light_rect.collidepoint(mouse_pos):
        light_color = CURRENT_THEME["button_hover"]

    else:
        light_color = CURRENT_THEME["button"]

    pygame.draw.rect(screen, light_color, light_rect)

    pygame.draw.rect(
        screen,
        CURRENT_THEME["border"],
        light_rect,
        2
    )

    _draw_centered_text(
        screen,
        font,
        "Light Mode",
        CURRENT_THEME["text"],
        light_rect
    )

    # Dark Mode button
    dark_rect = theme_button_rect(state, "dark")
    if dark_rect.collidepoint(mouse_pos):
        dark_color = CURRENT_THEME["button_hover"]

    else:
        dark_color = CURRENT_THEME["button"]

    pygame.draw.rect(screen, dark_color, dark_rect)
    pygame.draw.rect(
        screen,
        CURRENT_THEME["border"],
        dark_rect,
        2
    )

    _draw_centered_text(
        screen,
        font,
        "Dark Mode",
        CURRENT_THEME["text"],
        dark_rect
    )

# called in input_handler.py to draw the menu screen with difficulty buttons
def draw_menu(screen, font):
    screen.fill(CURRENT_THEME["background"])
    title = font.render("Minesweeper", True, CURRENT_THEME["text"])
    title_rect = title.get_rect(
        center=(MENU_SIZE[0] // 2, 20)
    )
    screen.blit(title, title_rect)
    mouse_pos = pygame.mouse.get_pos()
    for i in range(len(DIFFICULTY_LABELS)):
        rect = menu_button_rect(i)

        if rect.collidepoint(mouse_pos):
            color = CURRENT_THEME["button_hover"]

        else:
            color = CURRENT_THEME["button"]

        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(
            screen,
            CURRENT_THEME["border"],
            rect,
            2
        )
        _draw_centered_text(
            screen,
            font,
            DIFFICULTY_LABELS[i],
            CURRENT_THEME["text"],
            rect
        )

# called in input_handler.py to draw the game screen with the grid, status bar, mine counter, timer, and win/loss message
def draw_game(screen, font, big_font, manager, elapsed_seconds):
    state = manager.get_state()
    board = manager.get_board()

    # Fill the entire window with the border color first
    screen.fill(CURRENT_THEME["border"])

    # Create an area inside the border for the game
    game_rect = screen.get_rect().inflate(
        -BORDER_WIDTH * 2,
        -BORDER_WIDTH * 2
    )

    # Fill the game area with the background color
    pygame.draw.rect(
        screen,
        CURRENT_THEME["background"],
        game_rect
    )

    # draw the top status bar
    '''
    top_bar = pygame.Rect(
        BORDER_WIDTH,
        BORDER_WIDTH,
        screen.get_width() - BORDER_WIDTH * 2,
        TOP_BAR_HEIGHT
    )
    '''
    top_bar = pygame.Rect(
        BORDER_WIDTH,
        BORDER_WIDTH,
        screen.get_width() - BORDER_WIDTH * 2,
        TOP_BAR_HEIGHT
    )

    pygame.draw.rect(
        screen,
        CURRENT_THEME["top_bar"],
        top_bar
    )

    pygame.draw.line(
        screen,
        CURRENT_THEME["border"],
        (BORDER_WIDTH, BORDER_WIDTH + TOP_BAR_HEIGHT - 1),
        (
            screen.get_width() - BORDER_WIDTH,
            BORDER_WIDTH + TOP_BAR_HEIGHT - 1
        ),
        1
    )

    flags_used = _count_flags(state, board)
    total_mines = _get_total_mines(state)
    if total_mines is None:
        mine_text = "Flags: " + str(flags_used)

    else:
        mine_text = "Flags: " + str(total_mines - flags_used)

    #mine_surface = font.render(mine_text, True, TEXT_COLOR)
    # Now uses CURRENT_THEME for dark and light mode implementation
    mine_surface = font.render(
        mine_text,
        True,
        CURRENT_THEME["text"]
    )

    screen.blit(
        mine_surface,
        (BORDER_WIDTH + 8, BORDER_WIDTH + 10)
    )

    timer_text = "Time: " + str(int(elapsed_seconds))

    #timer_surface = font.render(timer_text, True, TEXT_COLOR)
    # Now uses CURRENT_THEME for dark and light mode implementation

    timer_surface = font.render(
        timer_text,
        True,
        CURRENT_THEME["text"]
    )

    timer_rect = timer_surface.get_rect()
    timer_rect.top = BORDER_WIDTH + 10
    timer_rect.right = screen.get_width() - BORDER_WIDTH - 8
    screen.blit(timer_surface, timer_rect)
    hints_remaining = _get_value(
        state,
        ["hints_remaining"],
        0
    )

    guide_text = (
        "H: hint (" +
        str(hints_remaining) +
        ")   R: restart   Esc: menu"
    )

    #guide_surface = font.render(guide_text, True, TEXT_COLOR)
    # Now uses CURRENT_THEME for dark and light mode implementation
    guide_surface = font.render(
        guide_text,
        True,
        CURRENT_THEME["text"]
    )

    guide_rect = guide_surface.get_rect()
    guide_rect.top = BORDER_WIDTH + 40
    guide_rect.centerx = screen.get_width() // 2
    screen.blit(guide_surface, guide_rect)

    #explosion emoji font
    emoji_font = pygame.font.SysFont(
        "Noto Color Emoji",
        24
    )

    # draw every cell in the board
    for row in range(state.rows):
        for col in range(state.columns):
            x = BORDER_WIDTH + col * CELL_SIZE
            y = BORDER_WIDTH + TOP_BAR_HEIGHT + row * CELL_SIZE
            rect = pygame.Rect(
                x,
                y,
                CELL_SIZE,
                CELL_SIZE
            )
            cell = _get_cell(
                board,
                row,
                col
            )
            revealed, flagged, is_mine, number = _cell_info(
                state,
                cell,
                row,
                col
            )
            if revealed:
                #pygame.draw.rect(screen, REVEALED_CELL_COLOR, rect)
                # Now uses CURRENT_THEME for dark and light mode implementation
                pygame.draw.rect(
                    screen,
                    CURRENT_THEME["revealed"],
                    rect
                )

                if is_mine:
                    _draw_centered_text(
                        screen,
                        font,
                        "*",
                        MINE_COLOR,
                        rect
                    )

                elif isinstance(number, int) and number > 0:

                    color = NUMBER_COLORS.get(
                        number,
                        TEXT_COLOR
                    )

                    _draw_centered_text(
                        screen,
                        font,
                        number,
                        color,
                        rect
                    )

            else:
                #pygame.draw.rect(screen, HIDDEN_CELL_COLOR, rect)
                # Now uses CURRENT_THEME for dark and light mode implementation
                pygame.draw.rect(
                    screen,
                    CURRENT_THEME["hidden"],
                    rect
                )
                if flagged:
                    _draw_centered_text(
                        screen,
                        font,
                        "F",
                        FLAG_COLOR,
                        rect
                    )

            #pygame.draw.rect(screen, BORDER_COLOR, rect, 1)
            # Now uses CURRENT_THEME for dark and light mode implementation
            pygame.draw.rect(
                screen,
                CURRENT_THEME["border"],
                rect,
                1
            )

    # show the result after the game ends
    if not state.is_active:
        message = _game_over_message(state)

        #message_surface = big_font.render(message, True, TEXT_COLOR)
        # Now uses CURRENT_THEME for dark and light mode implementation
        message_surface = big_font.render(
            message,
            True,
            CURRENT_THEME["text"]
        )

        board_width = state.columns * CELL_SIZE
        board_height = state.rows * CELL_SIZE
        message_rect = message_surface.get_rect(
            center=(
                BORDER_WIDTH + board_width // 2,
                BORDER_WIDTH +
                TOP_BAR_HEIGHT +
                board_height // 2
            )

        )

        background_rect = message_rect.inflate(
            30,
            20
        )

        #pygame.draw.rect(screen, TOP_BAR_COLOR, background_rect)
        #pygame.draw.rect(screen, BORDER_COLOR, background_rect, 2)
        pygame.draw.rect(
            screen,
            CURRENT_THEME["top_bar"],
            background_rect
        )

        pygame.draw.rect(
            screen,
            CURRENT_THEME["border"],
            background_rect,
            2
        )

        screen.blit(
            message_surface,
            message_rect
        )

    # draw theme controls outside the game board
    if state.is_active:
        _draw_theme_buttons(
            screen,
            font,
            state
        )

    # draw a border around the entire window
    pygame.draw.rect(
        screen,
        CURRENT_THEME["border"],
        screen.get_rect(),
        BORDER_WIDTH
    )