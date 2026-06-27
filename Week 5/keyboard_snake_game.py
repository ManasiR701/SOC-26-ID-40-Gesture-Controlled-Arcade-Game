import pygame     # The main game library. Handles the window, drawing shapes and text, reading keyboard input, and timing. Nothing visual can happen without this.
import random     # Used to generate a random number
import sys        # Used to call "sys.exit" which cleanly terminates the entire python program.
                  # Without it, pygame.quit() alone closes the window but leaves python still running in the background. 

# =====================================================================
# 1. INITIALIZATION & CONFIGURATION
# =====================================================================

# --- PyGame Grid / Window Settings ---
CELL_SIZE   = 30                        # Every snake segment and food block is drawn as a 30×30 pixel square.
                                        # Increase it for bigger cells, decrease for smaller
GRID_WIDTH  = 30                        # The play area is 30 cells wide and 22 cells tall. The snake's position is always tracked in these grid units (like column 5, row 3), never in raw pixels.
GRID_HEIGHT = 22
WIDTH       = CELL_SIZE * GRID_WIDTH    # Convert the grid size into actual pixel dimensions for the window. 
HEIGHT      = CELL_SIZE * GRID_HEIGHT   # These are the numbers pygame uses to create the window.

# --- Colors ---
# Each color is an (R, G, B) tuple, values 0-255. 
BG_COLOR     = (15, 15, 25)     # Dark navy blue
SNAKE_HEAD   = (0, 230, 120)    # Bright green used for the snake's head only, so it stands out from the body.
SNAKE_BODY   = (0, 170, 90)     # Slightly darker green for the body segments
FOOD_COLOR   = (240, 70, 90)    # Red-pink 
TEXT_COLOR   = (235, 235, 245)  # Whitish
GRID_COLOR   = (30, 30, 45)     # Very slightly lighter than the background, draws faint grid lines


# --- Helper Functions ---
def random_food(snake):     # A function that takes the snake's current body positions as input and returns a valid food position.
    while True:             # Keeps looping until it finds a valid spot.
        pos = (random.randint(2, GRID_WIDTH - 3), random.randint(2, GRID_HEIGHT - 3))    # Picks a random (column, row) pair.
        if pos not in snake:       # Checks whether this random position is already occupied by the snake's body. 
            return pos             # If the spot is free, return it. If not, the while True loop tries again with a new random position.

def draw_cell(surface, pos, color):    # A helper function that draws one grid cell. Used for both snake segments and food. Takes the surface to draw on, the grid position (col, row), and the fill color.
    x = pos[0] * CELL_SIZE             # Converts grid coordinates to pixel coordinates. 
    y = pos[1] * CELL_SIZE
    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)      # pygame.Rect defines a rectangle using (x, y, width, height). This rectangle is one cell at the correct pixel location, sized 30×30 pixels.
    pygame.draw.rect(surface, color, rect)              # Fills the rectangle with the given color. 
    pygame.draw.rect(surface, BG_COLOR, rect, 1)        # Draws a second rectangle on top, but with thickness 1 (the last argument), which means just the outline, not filled. Colour of the outline = background colour

# =====================================================================
# 2. MAIN APPLICATION LOOP
# =====================================================================
def main():         # Everything game-related lives inside this function.
    pygame.init()   # Starts up all of pygame's internal systems (display, fonts, events, timing). Must be called before anything else in pygame, skipping this causes crashes.
    screen = pygame.display.set_mode((WIDTH, HEIGHT))    # Creates the actual game window sized 900×660 pixels. screen is the surface you draw everything onto. 
    pygame.display.set_caption("Snake Game")      # Sets the text shown in the window's title bar.
    font = pygame.font.SysFont("consolas", 22)    # Loads the "Consolas" system font at size 22. Used for small text like score and hints.
    big_font = pygame.font.SysFont("consolas", 40, bold=True)     # Same font at size 40, bold. Used for large overlay text like "PAUSED" and "GAME OVER".

    # --- Game State Initialization ---
    def reset_game():     # Called at start and every restart.
        start = (GRID_WIDTH // 2, GRID_HEIGHT // 2)     # declaring the start position of the snake
        return [start], (1, 0), random_food([start]), 0 # returns four values at once
                                                        # [start] -> the snake as a list containing just the starting cell (one segment)
                                                        # (1, 0) -> initial direction: column + 1, row + 0, meaning "moving right"
                                                        # random_food([start]) -> a random food position that isn't on the snake's starting cell
                                                        # 0 -> starting score
    
    snake, direction, food, score = reset_game()     # Calls reset_game() and unpacks its four return values into four variables. 
    
    # game_over, is_paused, game_started, high_score are the four boolean/integer flags that control what the game is doing at any moment
    game_over    = False    
    is_paused    = False
    game_started = False    # True only after the player presses SPACE on the welcome screen
    high_score   = 0        # resets to 0 every time the program starts

    ### GAME SPEED CONTROL ###
    # We want the snake to move every 200 milliseconds (i.e. 5 times per second).
    # You can increase this number (e.g., 250) to make it even slower and easier!
    MOVE_DELAY_START = 200           # starting speed (ms between steps)
    MOVE_DELAY_MIN   = 80               # fastest the snake can ever get
    SPEED_STEP       = 5                # how many ms to shave off per food eaten
    MOVE_DELAY       = MOVE_DELAY_START  # current delay, will shrink as score grows
    last_move_time   = pygame.time.get_ticks()   # pygame.time.get_ticks() returns how many milliseconds have passed since pygame started, as an integer. 

    while True:     # An infinite loop, each iteration processes exactly one frame. The game runs forever until sys.exit() is called inside the loop.
        # ---------------------------------------------------------
        # PHASE 1: EVENT HANDLING & DIRECTION UPDATES
        # ---------------------------------------------------------
        for event in pygame.event.get():       # Every frame, pygame collects all things that happened (key presses, mouse clicks, window close) into a queue. 
                                               # pygame.event.get() retrieves and clears that queue. 
                                               # We loop through each event and respond to the ones we care about.
            if event.type == pygame.QUIT:      # pygame.QUIT fires when the user clicks the window's X button.
                pygame.quit()                  # pygame.quit() shuts down pygame cleanly
                sys.exit()                     # sys.exit() ends the Python program

            if event.type == pygame.KEYDOWN:   # pygame.KEYDOWN fires once at the exact moment a key is pressed down. 

                # Q = quit anytime
                if event.key == pygame.K_q:    # event.key is the specific key that was pressed. pygame.K_q is pygame's constant for the Q key. Pressing Q quits from anywhere in the game
                    pygame.quit()
                    sys.exit()

                # SPACE = start on welcome screen
                if not game_started:
                    if event.key == pygame.K_SPACE:       # While on the welcome screen (not game_started), SPACE starts the game. 
                        game_started = True               
                        snake, direction, food, score = reset_game()     # reset_game() initialises a fresh snake/food/score. 
                        last_move_time = pygame.time.get_ticks()         # last_move_time is reset to now so the snake doesn't immediately take a step.
                        MOVE_DELAY = MOVE_DELAY_START                    # MOVE_DELAY is reset to the starting speed.

                # SPACE = restart after game over
                elif game_over:
                    if event.key == pygame.K_SPACE:                         # While on the game over screen, SPACE restarts.
                        snake, direction, food, score = reset_game()
                        game_over  = False                                  # flips the flag back so the game loop resumes. 
                        is_paused  = False                                  # is_paused = False clears any leftover pause state. 
                        last_move_time = pygame.time.get_ticks()
                        MOVE_DELAY = MOVE_DELAY_START   # reset speed on restart

                else:
                    # P = toggle pause
                    if event.key == pygame.K_p:         # While actively playing (not welcome screen, not game over), P toggles pause. 
                        is_paused = not is_paused       # not is_paused flips the boolean. If it was True it becomes False and vice versa. 
                                                        # One key, both pause and resume.

                    # Arrow keys = change direction
                    # Arrow keys only work when not paused.
                    # We never let the snake reverse directly into itself
                    # (e.g. moving right, you cannot instantly go left)
                    # direction is a (col_change, row_change) tuple.
                    # (0, -1) means "move zero columns, move minus one row" which is upward (because in pygame, y increases downward so going up = decreasing y = row -1). 
                    # The check direction != (0, 1) prevents reversing
                    if not is_paused:
                        if event.key == pygame.K_UP and direction != (0, 1):         
                            direction = (0, -1)
                        elif event.key == pygame.K_DOWN and direction != (0, -1):      # Down arrow sets direction to (0, 1), row increases, moving the snake downward. Can't do this if currently moving up.
                            direction = (0, 1)
                        elif event.key == pygame.K_LEFT and direction != (1, 0):       # Left arrow: column decreases by 1 each step. Can't do this if currently moving right (1, 0).
                            direction = (-1, 0)
                        elif event.key == pygame.K_RIGHT and direction != (-1, 0):     # Right arrow: column increases by 1 each step. Can't do this if currently moving left (-1, 0).
                            direction = (1, 0)

        # ---------------------------------------------------------
        # PHASE 2: UPDATE GAME STATE (THROTTLED STEP UPDATE)
        # ---------------------------------------------------------
        current_time = pygame.time.get_ticks()    # Gets the current timestamp in milliseconds. 

        # Only advance the game mechanics if enough milliseconds have passed!
        if game_started and not game_over and not is_paused and (current_time - last_move_time > MOVE_DELAY):     # Four conditions must all be true before the snake steps forward:
                                                                                                                  # game should be started (past the welcome screen), 
                                                                                                                  # not game_over: game is still alive
                                                                                                                  # not is_paused: game is not paused
                                                                                                                  # current_time - last_move_time > MOVE_DELAY: at least MOVE_DELAY time has passed since the snake's last step
                                                                                                                  # this is the throttle, it's what makes the snake move at a fixed speed regardless of how fast the loop itself runs.

            last_move_time = current_time   # reset time anchor for next step

            head = snake[0]    # snake is a list of (col, row) tuples. snake[0] is always the head, the first element. The body follows after it.
            new_head = (head[0] + direction[0], head[1] + direction[1])   # Calculates where the head would move to. head[0] is the current column; direction[0] is the column change (-1, 0, or 1). Same for rows.

            hit_wall = (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or    #Checks all four walls in one expression. new_head[0] < 0 = went off the left edge. >= GRID_WIDTH = went off the right edge. 
                        new_head[1] < 0 or new_head[1] >= GRID_HEIGHT)     # Same logic for top and bottom with row index. If any one of these is true, hit_wall is True.
            hit_self = new_head in snake       # Checks if the new head position already exists somewhere in the snake's body list.

            if hit_wall or hit_self:        # If either collision happened, the game ends.
                game_over = True
                if score > high_score:      # update high score when the game ends
                    high_score = score
            else:
                snake.insert(0, new_head)   # If there is no collision, the move is valid. insert(0, new_head) adds the new head to the front of the snake list (index 0)
                if new_head == food:        # If the new head landed exactly on the food position: score goes up, a new food spawns somewhere else, and the snake speeds up by 5ms. 
                    score += 1
                    food = random_food(snake)
                    MOVE_DELAY = max(MOVE_DELAY_MIN, MOVE_DELAY - SPEED_STEP)  # max(MOVE_DELAY_MIN, ...) ensures the delay never goes below 80ms, the snake can't get infinitely fast. 
                else:
                    snake.pop()     # if there is no collision and no food is captured, increment the head and remove the tail to move the snake forward in any direction we want to move it in

        # ---------------------------------------------------------
        # PHASE 3: RENDERING (Always updates smoothly)
        # ---------------------------------------------------------
        screen.fill(BG_COLOR)     # Clears the entire window to the background color at the start of every frame. 

        # The drawing section has two branches —> welcome screen or gameplay, based on whether the game has started yet.
        if not game_started:
            # ----- WELCOME SCREEN -----
            title_surf = big_font.render("SNAKE GAME", True, SNAKE_HEAD)                       # font.render() doesn't draw text directly onto the screen, it creates a separate surfac (image) containing that text. 
            sub_surf   = font.render("Press SPACE to start", True, TEXT_COLOR)                 # Same process for the smaller subtitle text using the smaller font.
            screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, HEIGHT//2 - 40))    # Blit stamps a surface onto another surface at a given pixel position. 
            screen.blit(sub_surf,   (WIDTH//2 - sub_surf.get_width()//2,   HEIGHT//2 + 20))

        else:
            for gx in range(GRID_WIDTH):      #  This loop runs 30 times (one per column). Each iteration draws one vertical line from the top of the screen (gx*CELL_SIZE, 0) to the bottom (gx*CELL_SIZE, HEIGHT). 
                pygame.draw.line(screen, GRID_COLOR, (gx*CELL_SIZE, 0), (gx*CELL_SIZE, HEIGHT))
            for gy in range(GRID_HEIGHT):     # Same for horizontal lines: 22 lines, one per row, spanning the full width.
                pygame.draw.line(screen, GRID_COLOR, (0, gy*CELL_SIZE), (WIDTH, gy*CELL_SIZE))

            draw_cell(screen, food, FOOD_COLOR)      # Draws the food as a red square at its current grid position using the helper function.
            for i, segment in enumerate(snake):      # Draws every segment of the snake. enumerate gives both the index i and the segment position. 
                color = SNAKE_HEAD if i == 0 else SNAKE_BODY       # When i == 0 (the head), it uses SNAKE_HEAD (brighter green). Every other segment uses SNAKE_BODY (darker green).
                draw_cell(screen, segment, color)

            score_surf = font.render(f"Score: {score}", True, TEXT_COLOR)           # Renders the score and high score as text surfaces.
            hs_surf    = font.render(f"Best: {high_score}", True, (255, 215, 0))    # gold color
            screen.blit(score_surf, (8, 6))                                         # Stamps the score at pixel (8, 6), 8 pixels from the left edge, 6 from the top. Pinned to the top-left corner.
            screen.blit(hs_surf,    (WIDTH - hs_surf.get_width() - 8, 6))           # Pins the high score to the top-right corner.

            if is_paused and not game_over:                                         # The pause overlay only shows when is_paused is True AND the game isn't over (checking both prevents the pause message appearing on top of the game over message).
                pause_surf = big_font.render("PAUSED", True, TEXT_COLOR)
                sub_surf   = font.render("Press P to resume", True, TEXT_COLOR)
                screen.blit(pause_surf, (WIDTH//2 - pause_surf.get_width()//2, HEIGHT//2 - 40))
                screen.blit(sub_surf,   (WIDTH//2 - sub_surf.get_width()//2,   HEIGHT//2 + 15))

            if game_over:
                msg = big_font.render("GAME OVER", True, FOOD_COLOR)
                sub = font.render("Press SPACE to restart   |   Q to quit", True, TEXT_COLOR)
                screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 40))
                screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 15))

        pygame.display.flip()        # This is the most critical line in the rendering section. Everything drawn above was happening on a hidden back-buffer, not the visible screen. 
                                     # flip() swaps the back-buffer with the visible screen, showing the completed frame all at once. 
                                     # Without this line, the window stays blank, you'd draw everything but never display it. Must be called once per frame, after all drawing is done.

if __name__ == "__main__":          # __name__ is a special Python variable. When you run this file directly (python3 snake_game_keyboard.py), Python sets __name__ to "__main__", so main() is called. 
    main()