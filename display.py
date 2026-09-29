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
BOARD_MARGIN = 20

# added from Courtney for dark and light mode implementation

# width of the area to the right of the game board
SIDE_PANEL_WIDTH = 180
THEME_BUTTON_WIDTH = 70
THEME_BUTTON_HEIGHT = 28
SCREEN_MARGIN = 8
BORDER_WIDTH = 5


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

# (row, col) of the last cell the player left-clicked, used to find the mine that was hit
LAST_CLICK = None

def set_last_click(row, col):
    """Called by input_handler.py whenever the player reveals a cell."""
    global LAST_CLICK
    LAST_CLICK = (row, col)

def clear_last_click():
    global LAST_CLICK
    LAST_CLICK = None

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
def theme_button_rect(state, mode, screen_width=None):
    """Returns the clickable rectangle for a theme button."""
    if screen_width is None:
        screen_width = game_window_size(state)[0]

    group_width = (THEME_BUTTON_WIDTH * 2) + 6
    x = (screen_width - group_width) // 2

    if mode == "light":
        x += THEME_BUTTON_WIDTH + 6

    y = BORDER_WIDTH + 6
    return pygame.Rect(
        x,
        y,
        THEME_BUTTON_WIDTH,
        THEME_BUTTON_HEIGHT
    )

def board_geometry(screen, state):
    """Returns the board rectangle and cell size for the current window."""
    available_width = screen.get_width() - BOARD_MARGIN * 2
    available_height = screen.get_height() - TOP_BAR_HEIGHT - BOARD_MARGIN * 2
    cell_size = max(
        1,
        min(
            available_width // state.columns,
            available_height // state.rows
        )
    )
    board_width = cell_size * state.columns
    board_height = cell_size * state.rows
    board_rect = pygame.Rect(
        (screen.get_width() - board_width) // 2,
        TOP_BAR_HEIGHT + BOARD_MARGIN + (available_height - board_height) // 2,
        board_width,
        board_height
    )
    return board_rect, cell_size
def game_window_size(state):
    """Returns (width, height) for the window so the board, side panel,
    and border all fit. Use this for pygame.display.set_mode() when a
    game starts."""
    board_width = state.columns * CELL_SIZE
    board_height = state.rows * CELL_SIZE

    width = (
        board_width
        + BOARD_MARGIN * 2
    )
    height = (
        TOP_BAR_HEIGHT
        + board_height
        + BOARD_MARGIN * 2
    )
    return max(width, MIN_WINDOW_WIDTH), height

# helper function for drawing the theme choice buttons for the user to click on
def _draw_theme_buttons(screen, font, state):

    """Draws the Light Mode and Dark Mode buttons in the top status bar."""

    mouse_pos = pygame.mouse.get_pos()

    # Light Mode button
    light_rect = theme_button_rect(state, "light", screen.get_width())

    if light_rect.collidepoint(mouse_pos):
        light_color = CURRENT_THEME["button_hover"]
    else:
        light_color = CURRENT_THEME["button"]

    pygame.draw.rect(screen, light_color, light_rect)

    light_width = 4 if CURRENT_THEME is LIGHT_THEME else 2
    pygame.draw.rect(screen, CURRENT_THEME["border"], light_rect, light_width)

    _draw_centered_text(
        screen,
        font,
        "Light",
        CURRENT_THEME["text"],
        light_rect
    )

    # Dark Mode button
    dark_rect = theme_button_rect(state, "dark", screen.get_width())

    if dark_rect.collidepoint(mouse_pos):
        dark_color = CURRENT_THEME["button_hover"]
    else:
        dark_color = CURRENT_THEME["button"]

    pygame.draw.rect(screen, dark_color, dark_rect)

    dark_width = 4 if CURRENT_THEME is DARK_THEME else 2
    pygame.draw.rect(screen, CURRENT_THEME["border"], dark_rect, dark_width)

    _draw_centered_text(
        screen,
        font,
        "Dark",
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

def _draw_flag(screen, rect):
    cx, cy = rect.center
    # pole
    pygame.draw.line(screen, (30, 30, 30), (cx, rect.top + 6), (cx, rect.bottom - 7), 2)
    # flag
    pygame.draw.polygon(screen, FLAG_COLOR, [
        (cx, rect.top + 6), (cx - 9, rect.top + 11), (cx, rect.top + 16)
    ])
    # base
    pygame.draw.line(screen, (30, 30, 30), (cx - 6, rect.bottom - 7), (cx + 6, rect.bottom - 7), 2)

def _draw_mine(screen, rect):
    pygame.draw.circle(screen, (20, 20, 20), rect.center, 8)
    pygame.draw.circle(screen, (255, 255, 255), (rect.centerx - 3, rect.centery - 3), 2)

def _shade(color, amount):
    """Returns a lighter (positive) or darker (negative) version of a color."""
    return tuple(max(0, min(255, c + amount)) for c in color)

def _draw_hidden_cell(screen, rect):
    """Draws a hidden cell with a raised, button-like edge."""
    base = CURRENT_THEME["hidden"]
    light = _shade(base, 45)
    dark = _shade(base, -45)

    pygame.draw.rect(screen, base, rect)
    # light edges on top and left
    pygame.draw.line(screen, light, rect.topleft, rect.topright, 2)
    pygame.draw.line(screen, light, rect.topleft, rect.bottomleft, 2)
    # dark edges on bottom and right
    pygame.draw.line(screen, dark, rect.bottomleft, rect.bottomright, 2)
    pygame.draw.line(screen, dark, rect.topright, rect.bottomright, 2)

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

    board_rect, cell_size = board_geometry(screen, state)
    game_lost = (not state.is_active) and _game_over_message(state) == "Game Over"
    # draw every cell in the board
    for row in range(state.rows):
        for col in range(state.columns):
            x = board_rect.left + col * cell_size
            y = board_rect.top + row * cell_size
            rect = pygame.Rect(
                x,
                y,
                cell_size,
                cell_size
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
            clicked_mine = is_mine and (row, col) == LAST_CLICK      # the mine the player actually hit
            if game_lost and is_mine and not flagged:
                revealed = True                      # show every unflagged mine on a loss

            if revealed:
                if clicked_mine and game_lost:
                    fill = (200, 60, 60)             # red tint on the mine that was hit
                else:
                    fill = CURRENT_THEME["revealed"]
                pygame.draw.rect(screen, fill, rect)

                if is_mine:
                    _draw_mine(screen, rect)
                elif isinstance(number, int) and number > 0:
                    color = NUMBER_COLORS.get(number, TEXT_COLOR)
                    _draw_centered_text(screen, font, number, color, rect)

                # soft grid line, revealed cells only
                pygame.draw.rect(
                    screen,
                    _shade(CURRENT_THEME["revealed"], -30),
                    rect,
                    1
                )
            else:
                _draw_hidden_cell(screen, rect)
                if flagged:
                    _draw_flag(screen, rect)

            #pygame.draw.rect(screen, BORDER_COLOR, rect, 1)
            # Now uses CURRENT_THEME for dark and light mode implementation
            pygame.draw.rect(
                screen,
                _shade(CURRENT_THEME["revealed"], -30),
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

        message_rect = message_surface.get_rect(
            center=(
                board_rect.centerx,
                board_rect.centery
            )

        )

        background_rect = message_rect.inflate(
            50,
            30
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
            1
        )

        screen.blit(
            message_surface,
            message_rect
        )

    pygame.draw.rect(
        screen,
        CURRENT_THEME["border"],
        board_rect.inflate(4, 4),
        2
    )

    # draw theme controls in the top status bar
    _draw_theme_buttons(screen, font, state)