import os
import sys
from typing import Optional

import pygame

# Game models
from usa.models import UnitedStates

# --- Pygame setup ---
pygame.init()

# --- Configuration Constants ---
SCREEN_WIDTH: int = 1000
SCREEN_HEIGHT: int = 700
FRAME_RATE: int = 60  # Pygame clock tick rate

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
HIGHLIGHT = (60, 120, 255)
LIGHT_GRAY = (235, 235, 235)
GREEN = (30, 160, 60)
RED = (200, 60, 60)

# Font sizes
TITLE_FONT = pygame.font.Font(None, 64)
MENU_FONT = pygame.font.Font(None, 48)
SMALL_FONT = pygame.font.Font(None, 28)

# Menu options
MENU_OPTIONS = ["Start Game", "Load Game", "Quit"]

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("USA Political Simulation")


# -------- Menu Rendering ---------
def draw_menu(selected_index: int) -> None:
    """Render the main menu and highlight the selected option."""
    screen.fill(WHITE)

    # Title
    title = TITLE_FONT.render("USA Political Simulation", True, BLACK)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
    screen.blit(title, title_rect)

    # Subtitle
    subtitle = SMALL_FONT.render(
        "Use Up/Down arrows or mouse to select. Enter/Click to confirm.",
        True,
        (80, 80, 80),
    )
    subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 200))
    screen.blit(subtitle, subtitle_rect)

    # Menu options
    start_y = 280
    for i, option in enumerate(MENU_OPTIONS):
        color = HIGHLIGHT if i == selected_index else BLACK
        text = MENU_FONT.render(option, True, color)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 70))
        # Hover underline
        if i == selected_index:
            pygame.draw.line(
                screen,
                color,
                (rect.left, rect.bottom + 4),
                (rect.right, rect.bottom + 4),
                2,
            )
        screen.blit(text, rect)

    # Footer
    footer = SMALL_FONT.render(
        "GitHub Copilot demo UI — ESC to quit", True, (120, 120, 120)
    )
    screen.blit(footer, (20, SCREEN_HEIGHT - 40))

    pygame.display.flip()


# -------- Game View / Loop ---------
SAVE_PATH = os.path.join(os.path.dirname(__file__), "simulation_state.json")


def draw_game(ui_us: UnitedStates, msg: Optional[str] = None) -> None:
    """Render a simple HUD displaying macro stats and controls."""
    screen.fill(LIGHT_GRAY)

    # Header
    header = TITLE_FONT.render(
        f"Year {ui_us.year}  Month {ui_us.month:02d}", True, BLACK
    )
    screen.blit(header, (30, 20))

    # Macro stats
    y = 100
    lines = [
        f"Growth: {ui_us.growth*100:.2f}%  Unemployment: {ui_us.unemployment:.1f}%  Inflation: {ui_us.inflation:.1f}%",
        f"President Approval: {ui_us.opinion.approval_president:.1f}%   Congress Approval: {ui_us.opinion.approval_congress:.1f}%",
        f"Budget: Revenue ${ui_us.budget.revenue:.1f}B  Spending ${ui_us.budget.spending:.1f}B  Deficit ${ui_us.budget.deficit:.1f}B",
    ]
    for line in lines:
        txt = MENU_FONT.render(line, True, BLACK)
        screen.blit(txt, (30, y))
        y += 44

    # States overview (first 4 for brevity)
    y += 10
    screen.blit(MENU_FONT.render("Key States:", True, BLACK), (30, y))
    y += 40
    for name in list(ui_us.states.keys())[:4]:
        st = ui_us.states[name]
        line = f"{name}: GDP ${st.gdp:.1f}B  Unemp {st.unemployment:.1f}%  Infl {st.inflation:.1f}%"
        txt = SMALL_FONT.render(line, True, (40, 40, 40))
        screen.blit(txt, (40, y))
        y += 26

    # Controls
    controls = [
        ("SPACE", "Advance 1 month"),
        ("A", "Advance 12 months"),
        ("E", "Trigger an event"),
        ("S", "Save state"),
        ("L", "Load state"),
        ("ESC", "Return to Main Menu"),
    ]
    y = SCREEN_HEIGHT - 150
    screen.blit(MENU_FONT.render("Controls:", True, BLACK), (30, y))
    y += 40
    for key, desc in controls:
        k = SMALL_FONT.render(f"[{key}] {desc}", True, (20, 20, 20))
        screen.blit(k, (40, y))
        y += 24

    # Message banner
    if msg:
        banner = SMALL_FONT.render(
            msg, True, GREEN if "Saved" in msg or "Loaded" in msg else RED
        )
        banner_rect = banner.get_rect(
            right=SCREEN_WIDTH - 20, bottom=SCREEN_HEIGHT - 20
        )
        screen.blit(banner, banner_rect)

    pygame.display.flip()


def game_loop(seed: int = 42, loaded: Optional[UnitedStates] = None) -> None:
    """Start the simulation loop: handle input, update and redraw screen.

    Controls:
      SPACE: advance 1 month
      A: advance 12 months
      E: trigger a random event immediately
      S: save to simulation_state.json
      L: load from simulation_state.json
      ESC: return to main menu
    """
    clock = pygame.time.Clock()
    us = loaded if loaded else UnitedStates.new_default(seed=seed)
    info_msg: Optional[str] = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    us.advance_turn(1)
                    info_msg = "Advanced 1 month"
                elif event.key == pygame.K_a:
                    us.advance_turn(12)
                    info_msg = "Advanced 12 months"
                elif event.key == pygame.K_e:
                    ev = us.trigger_event()
                    if ev:
                        us.ai_react_to_events()
                        info_msg = f"Event: {ev.name}"
                    else:
                        info_msg = "No event triggered"
                elif event.key == pygame.K_s:
                    try:
                        us.save_to_file(SAVE_PATH)
                        info_msg = f"Saved to {os.path.basename(SAVE_PATH)}"
                    except Exception as ex:
                        info_msg = f"Save failed: {ex}"
                elif event.key == pygame.K_l:
                    try:
                        if os.path.exists(SAVE_PATH):
                            us = UnitedStates.load_from_file(SAVE_PATH)
                            info_msg = f"Loaded {os.path.basename(SAVE_PATH)}"
                        else:
                            info_msg = "No save file found"
                    except Exception as ex:
                        info_msg = f"Load failed: {ex}"

        draw_game(us, info_msg)
        info_msg = None
        clock.tick(FRAME_RATE)


# -------- Main Menu Loop ---------
def main_menu() -> None:
    """Main menu: navigate options and launch game or quit."""
    selected_index = 0
    clock = pygame.time.Clock()

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        # Update hover selection
        for i, option in enumerate(MENU_OPTIONS):
            rect = MENU_FONT.render(option, True, BLACK).get_rect(
                center=(SCREEN_WIDTH // 2, 280 + i * 70)
            )
            if rect.collidepoint(mouse_pos):
                selected_index = i

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(MENU_OPTIONS)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(MENU_OPTIONS)
                elif event.key == pygame.K_RETURN:
                    choice = MENU_OPTIONS[selected_index]
                    if choice == "Start Game":
                        game_loop()
                    elif choice == "Load Game":
                        loaded = None
                        if os.path.exists(SAVE_PATH):
                            try:
                                loaded = UnitedStates.load_from_file(SAVE_PATH)
                            except Exception:
                                loaded = None
                        game_loop(loaded=loaded)
                    elif choice == "Quit":
                        pygame.quit()
                        sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Mouse click select
                choice = MENU_OPTIONS[selected_index]
                if choice == "Start Game":
                    game_loop()
                elif choice == "Load Game":
                    loaded = None
                    if os.path.exists(SAVE_PATH):
                        try:
                            loaded = UnitedStates.load_from_file(SAVE_PATH)
                        except Exception:
                            loaded = None
                    game_loop(loaded=loaded)
                elif choice == "Quit":
                    pygame.quit()
                    sys.exit()

        draw_menu(selected_index)
    clock.tick(FRAME_RATE)


if __name__ == "__main__":
    main_menu()
