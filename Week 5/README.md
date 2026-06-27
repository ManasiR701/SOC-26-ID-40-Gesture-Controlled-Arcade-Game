# Snake Game — Keyboard Controlled

This is a keyboard-controlled Snake game built using **Pygame**.

Your task is to **understand this code thoroughly**, and then in the upcoming weeks, replace the keyboard input with your own gesture logic using MediaPipe. We have provided a **highly commented** snake game code (`keyboard_snake_game.py`). We would recommend you to play around with variables and see the results so that you can understand the code in a better way and you can create changes and add additional features of your own to create your own customized snake game :)
---

## How to Run

**Install the only dependency:**
```bash
pip install pygame
```

**Run the game:**
```bash
python snake_game_keyboard.py
```

---

## Controls

| Key | Action |
|-----|--------|
| `SPACE` | Start the game (on welcome screen) |
| `Arrow Keys` | Change snake direction |
| `P` | Pause / Resume |
| `SPACE` | Restart after game over |
| `Q` | Quit anytime |

---

## Features

- Welcome screen before the game starts
- Score display (top-left) and High Score in gold (top-right)
- Snake gradually speeds up as it eats more food (caps at maximum speed)
- Pause and resume support
- Game over screen with restart option

---

## Code Walkthrough

### Imports

```python
import pygame
```
The main game library. Handles the window, drawing shapes and text, reading keyboard input, and timing. Nothing visual can happen without this.

```python
import random
```
Used for one purpose only i.e. picking a random grid cell for the food to spawn at.

```python
import sys
```
Used to call `sys.exit()` which cleanly terminates the entire Python program. Without it, `pygame.quit()` alone closes the window but leaves Python still running in the background.

---

### Grid and Window Settings

```python
CELL_SIZE = 30
```
Every snake segment and food block is drawn as a 30×30 pixel square. This one number controls how big everything looks; increase it for bigger cells, decrease for smaller.

```python
GRID_WIDTH  = 30
GRID_HEIGHT = 22
```
The play area is 30 cells wide and 22 cells tall. The snake's position is always tracked in these grid units (like column 5, row 3), never in raw pixels.

```python
WIDTH  = CELL_SIZE * GRID_WIDTH    # 30 * 30 = 900 pixels
HEIGHT = CELL_SIZE * GRID_HEIGHT   # 30 * 22 = 660 pixels
```
Converts the grid size into actual pixel dimensions for the window. These are the numbers pygame uses to create the window.

---

### Colors

```python
BG_COLOR  = (15, 15, 25)
```
Each color is an `(R, G, B)` tuple, values 0-255. This is a very dark navy, almost black but with a slight blue tint. Used as the background every frame.

```python
SNAKE_HEAD = (0, 230, 120)
```
Bright green: used for the snake's head only, so it stands out from the body.

```python
SNAKE_BODY = (0, 170, 90)
```
Slightly darker green for the body segments, same hue as the head but dimmer, creating a visual hierarchy.

```python
FOOD_COLOR = (240, 70, 90)
```
Red-pink, chosen to contrast strongly with the green snake so it's easy to spot.

```python
TEXT_COLOR = (235, 235, 245)
```
Near-white, used for all on-screen text (score, pause message, game over).

```python
GRID_COLOR = (30, 30, 45)
```
Very slightly lighter than the background, draws faint grid lines you can barely see. Gives the game a subtle visual structure without being distracting.

---

### `random_food(snake)`

```python
def random_food(snake):
    while True:
        pos = (random.randint(2, GRID_WIDTH - 3), random.randint(2, GRID_HEIGHT - 3))
        if pos not in snake:
            return pos
```

A function that takes the snake's current body positions as input and returns a valid food position.

- `while True` keeps looping until it finds a valid spot. Most of the time it finds one on the first try, but if the snake is very long it might need a few attempts.
- `random.randint(2, GRID_WIDTH-3)` picks a random column from 2 to 27, keeps food away from the very edges by a couple of cells, purely for aesthetics.
- `pos not in snake` checks whether this random position is already occupied by the snake's body. Works because `snake` is a list of `(col, row)` tuples and Python can check if a tuple is in a list directly.
- If the spot is free, return it. If not, the `while True` loop tries again.

---

### `draw_cell(surface, pos, color)`

```python
def draw_cell(surface, pos, color):
    x = pos[0] * CELL_SIZE
    y = pos[1] * CELL_SIZE
    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, BG_COLOR, rect, 1)
```

A helper function that draws one grid cell, used for both snake segments and food.

- `pos[0] * CELL_SIZE` converts grid column to pixel x-coordinate. For example, column 5 → pixel x = 5 × 30 = 150. Same for row → pixel y.
- `pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)` defines a rectangle at the correct pixel location, sized 30×30 pixels.
- First `draw.rect` fills the rectangle with the given color.
- Second `draw.rect` with thickness `1` (last argument) draws just the outline in the background color, this creates a thin dark border so each segment looks separate instead of merging into one blob.

---

### `main()` — Setup

```python
pygame.init()
```
Starts up all of pygame's internal systems (display, fonts, events, timing). Must be called before anything else in pygame; skipping this causes crashes.

```python
screen = pygame.display.set_mode((WIDTH, HEIGHT))
```
Creates the actual game window sized 900×660 pixels. `screen` is the surface you draw everything onto.

```python
font     = pygame.font.SysFont("consolas", 22)
big_font = pygame.font.SysFont("consolas", 40, bold=True)
```
`font` is for small text (score, hints). `big_font` is for large overlay text ("PAUSED", "GAME OVER").

---

### `reset_game()`

```python
def reset_game():
    start = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
    return [start], (1, 0), random_food([start]), 0
```

A function defined *inside* `main()`, called at start and every restart. Returns four fresh values:
- `//` is integer division. `30 // 2 = 15`, `22 // 2 = 11`. So `start = (15, 11)`, the center of the grid. The snake always begins here.
- `[start]`: snake as a list with one starting cell
- `(1, 0)`: initial direction: column +1, row 0, meaning "moving right"
- `random_food([start])`: a random food position not on the snake
- `0`: starting score

---

### Game State Variables

```python
snake, direction, food, score = reset_game()
game_over    = False
is_paused    = False
game_started = False
high_score   = 0
```

- `snake, direction, food, score`:  unpacks all four return values of `reset_game()` in one line.
- `game_over`: when `True`, shows the game over screen.
- `is_paused`: when `True`, the snake stops moving but the screen still renders.
- `game_started`: starts as `False` so the welcome screen shows first. Flips to `True` when SPACE is pressed.
- `high_score`: tracks the best score this session. Resets to 0 every launch — it is not saved to a file.

---

### Speed Control Variables

```python
MOVE_DELAY_START = 200
MOVE_DELAY_MIN   = 80
SPEED_STEP       = 5
MOVE_DELAY       = MOVE_DELAY_START
last_move_time   = pygame.time.get_ticks()
```

- `MOVE_DELAY_START = 200`: the snake starts moving once every 200ms (5 times per second).
- `MOVE_DELAY_MIN = 80`: the snake can never move faster than once every 80ms. This caps the speed so the game doesn't become impossible at high scores.
- `SPEED_STEP = 5`: every time the snake eats food, `MOVE_DELAY` decreases by 5ms. It takes `(150-80)/5 = 14` food blocks to reach maximum speed.
- `MOVE_DELAY`: the current active delay. Starts at 150, decreases as score grows, resets on restart.
- `pygame.time.get_ticks()` returns how many milliseconds have passed since pygame started. Storing it now gives a reference point, we compare future timestamps against this to know when `MOVE_DELAY` ms have passed and the snake should step.

---

### The Main Loop

```python
while True:
```
An infinite loop — each iteration processes exactly one frame. Runs forever until `sys.exit()` is called inside.

---

### Phase 1 — Event Handling

```python
for event in pygame.event.get():
```
Every frame, pygame collects all things that happened (key presses, window close) into a queue. `pygame.event.get()` retrieves and clears that queue. We loop through each event and respond to the ones we care about.

```python
if event.type == pygame.QUIT:
    pygame.quit()
    sys.exit()
```
`pygame.QUIT` fires when the user clicks the window's X button. `pygame.quit()` shuts down pygame, `sys.exit()` ends the Python program. Both are needed.

```python
if event.type == pygame.KEYDOWN:
```
`pygame.KEYDOWN` fires once at the exact moment a key is pressed down.

**Q — quit anytime:**
```python
if event.key == pygame.K_q:
    pygame.quit()
    sys.exit()
```

**SPACE — start from welcome screen:**
```python
if not game_started:
    if event.key == pygame.K_SPACE:
        game_started = True
        snake, direction, food, score = reset_game()
        last_move_time = pygame.time.get_ticks()
        MOVE_DELAY = MOVE_DELAY_START
```
`game_started = True` flips the flag, welcome screen disappears. `reset_game()` initialises a fresh snake/food/score. `last_move_time` is reset to now so the snake doesn't immediately take a step. `MOVE_DELAY` is reset to starting speed.

**SPACE: restart after game over:**
```python
elif game_over:
    if event.key == pygame.K_SPACE:
        snake, direction, food, score = reset_game()
        game_over  = False
        is_paused  = False
        last_move_time = pygame.time.get_ticks()
        MOVE_DELAY = MOVE_DELAY_START
```
`game_over = False` flips the flag, game over screen disappears. `is_paused = False` clears any leftover pause state. Speed and timer are reset.

**P: toggle pause, Arrow keys: change direction:**
```python
else:
    if event.key == pygame.K_p:
        is_paused = not is_paused
    if not is_paused:
        if event.key == pygame.K_UP and direction != (0, 1):
            direction = (0, -1)
```
`not is_paused` flips the boolean, one key handles both pause and resume. For arrow keys, `direction` is a `(col_change, row_change)` tuple. `(0, -1)` means row -1 = upward (in pygame, y increases downward so going up = decreasing y). The check `direction != (0, 1)` prevents reversing, if currently moving down you can't instantly go up, which would run the head straight into the neck.

| Arrow Key | Direction Set | Meaning |
|-----------|--------------|---------|
| UP | `(0, -1)` | Row decreases: move up |
| DOWN | `(0, 1)` | Row increases: move down |
| LEFT | `(-1, 0)` | Column decreases: move left |
| RIGHT | `(1, 0)` | Column increases: move right |

---

### Phase 2: Moving the Snake

```python
current_time = pygame.time.get_ticks()

if game_started and not game_over and not is_paused and (current_time - last_move_time > MOVE_DELAY):
```
Four conditions must all be true before the snake steps forward - past welcome screen, game alive, not paused, and enough time has passed. This is the throttle, it makes the snake move at a fixed speed regardless of how fast the loop runs.

```python
last_move_time = current_time
```
Resets the time anchor to now. The next step won't happen until another `MOVE_DELAY` ms pass.

```python
head     = snake[0]
new_head = (head[0] + direction[0], head[1] + direction[1])
```
`snake[0]` is always the head. `new_head` is where the head would move to it adds the direction vector to the current head position. This is a candidate i.e. we check collisions before placing it.

```python
hit_wall = (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
            new_head[1] < 0 or new_head[1] >= GRID_HEIGHT)
hit_self = new_head in snake
```
- `hit_wall` checks all four walls: left edge (`< 0`), right edge (`>= GRID_WIDTH`), top, bottom.
- `hit_self` checks if the new head position already exists in the snake's body list.

```python
if hit_wall or hit_self:
    game_over = True
    if score > high_score:
        high_score = score
```
Either collision ends the game. High score is updated at this exact moment i.e. only at death.

```python
else:
    snake.insert(0, new_head)
    if new_head == food:
        score += 1
        food = random_food(snake)
        MOVE_DELAY = max(MOVE_DELAY_MIN, MOVE_DELAY - SPEED_STEP)
    else:
        snake.pop()
```
- `snake.insert(0, new_head)` adds the new head to the front of the snake list. The snake is now temporarily one segment longer than it should be.
- If food was eaten: score goes up, new food spawns, speed increases by 5ms. `max(MOVE_DELAY_MIN, ...)` caps the speed. Crucially, we do **not** remove the tail, by adding a head without removing a tail, the snake grows by one segment.
- If no food: `snake.pop()` removes the last element (the tail). New head added at front, old tail removed from back = the snake appears to move forward while staying the same length.

---

### Phase 3 — Rendering

```python
screen.fill(BG_COLOR)
```
Clears the entire window to the background color at the start of every frame. If skipped, the previous frame's drawing remains and you get smearing/ghosting effects.

**TASK: Try commenting this line of code to see what happens**

**Welcome screen:**
```python
title_surf = big_font.render("SNAKE GAME", True, SNAKE_HEAD)
screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, HEIGHT//2 - 40))
```
`font.render()` creates a surface (image) *containing* the text, it doesn't draw directly to screen. `screen.blit()` then stamps that surface onto the screen at a pixel position. `WIDTH//2 - title_surf.get_width()//2` is the standard centering formula: screen center minus half the text's width = text appears centered.

**Grid lines:**
```python
for gx in range(GRID_WIDTH):
    pygame.draw.line(screen, GRID_COLOR, (gx*CELL_SIZE, 0), (gx*CELL_SIZE, HEIGHT))
for gy in range(GRID_HEIGHT):
    pygame.draw.line(screen, GRID_COLOR, (0, gy*CELL_SIZE), (WIDTH, gy*CELL_SIZE))
```
Draws 30 vertical + 22 horizontal faint lines forming the grid.

**Snake and food:**
```python
draw_cell(screen, food, FOOD_COLOR)
for i, segment in enumerate(snake):
    color = SNAKE_HEAD if i == 0 else SNAKE_BODY
    draw_cell(screen, segment, color)
```
`enumerate` gives both the index `i` and the segment position. When `i == 0` (head), uses brighter green. Every other segment uses darker green.

**Score and high score:**
```python
screen.blit(score_surf, (8, 6))
screen.blit(hs_surf,    (WIDTH - hs_surf.get_width() - 8, 6))
```
Score pinned to top-left at pixel `(8, 6)`. High score pinned to top-right: `WIDTH - text_width - 8` ensures the text's right edge is always 8 pixels from the window's right edge.

**Pause overlay:**
```python
if is_paused and not game_over:
```
Only shows when paused AND game is not over it prevents the pause message appearing on top of the game over screen.

**Game over overlay:**
```python
if game_over:
```
Grid, snake, and food are still visible underneath (drawn before this block) so the player can see their final position while reading the game over message.

```python
pygame.display.flip()
```
**The most critical line.** Everything drawn above happened on a hidden back-buffer, not the visible screen. `flip()` swaps the back-buffer with the visible screen, showing the completed frame all at once. Without this line, the window stays blank no matter how much you draw. Must be called once per frame, after all drawing is done.

**TASK: Comment this line of code and see the results**

---

### Entry Point

```python
if __name__ == "__main__":
    main()
```
`__name__` is a special Python variable. When you run this file directly, Python sets `__name__` to `"__main__"` so `main()` is called. If someone imports this file from another script, `__name__` would be the filename instead and `main()` would not auto-run. This is standard Python practice for any runnable script.

---

## Your Task (Week 6)

Once you understand this code, your job is to integrate your gesture detection logic from Week 3-4 into this game:

1. Add the MediaPipe imports and setup at the top
2. Add the webcam capture inside the main loop
3. Add your gesture detection logic (finger angles, stability filter)
4. **Replace the arrow key direction changes with gesture-based direction changes**
5. Map different gestures to pause and to restart

The key insight: the game doesn't care *where* the direction command comes from i.e. keyboard or gesture. You are simply replacing what sets the `direction` variable.



