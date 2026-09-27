# EECS-581-Minesweeper Project 2
Maintaining a single-player puzzle game implemented using Python. Players uncover cells on a board until either all safe cells or a mine is revealed, resulting in a game over. Flags can be placed on potential mine cells.
## Features
- Beginner, Intermediate, and Expert difficulties
- First-click safety
- Flood-fill for safe cells with 0 adjacent mines
- Uncovered cells display a number (0-8) indicating adjacent mines
- Randomized mine placement
- Tracks the number of flags remaining
- Tracks the time to solve
- Win by uncovering all safe cells
- Hints
## Controls
- Left click: Reveal a cell
- Right click: Place a flag
- r: Restart on current difficulty
- esc: Return to difficulty select menu
- H: Reveal a tile using a hint
## Installation
### Prequisites
- Python
- Pygame

### Clone the repository
```bash
git clone https://github.com/RockettKings/EECS-581-Minesweeper.git
```

### Run the game
```bash
python input_handler.py
```
or

python3 -m venv .venv
source .venv/bin/source
python input_handler.py