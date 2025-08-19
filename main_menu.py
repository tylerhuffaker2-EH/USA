import os
import sys
import textwrap
import math  # Add standard math library
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple, Union

import pygame

# Game models
from usa.models import UnitedStates

# --- Pygame setup ---
pygame.init()

# --- Configuration Constants ---
SCREEN_WIDTH: int = 1000
SCREEN_HEIGHT: int = 700
FRAME_RATE: int = 60  # Pygame clock tick rate

# --- UI Constants ---
PADDING = 20
CORNER_RADIUS = 8
BORDER_WIDTH = 2
BUTTON_HEIGHT = 60
MENU_BUTTON_WIDTH = 220


# --- Color Palette ---
class Colors:
    # Main colors
    BG_LIGHT = (245, 245, 250)
    BG_DARK = (32, 34, 48)
    PRIMARY = (65, 105, 225)  # Royal Blue
    SECONDARY = (0, 123, 167)  # Darker Blue
    ACCENT = (255, 165, 0)  # Orange
    SUCCESS = (46, 183, 121)  # Green
    WARNING = (255, 140, 26)  # Orange
    ERROR = (220, 53, 69)  # Red

    # Text colors
    TEXT_LIGHT = (240, 240, 240)
    TEXT_DARK = (32, 33, 36)
    TEXT_MUTED = (108, 117, 125)

    # UI element colors
    PANEL_BG = (255, 255, 255, 220)  # Slightly transparent white
    PANEL_BORDER = (210, 210, 220)
    BUTTON_NORMAL = (240, 240, 250)
    BUTTON_HOVER = (220, 220, 235)
    BUTTON_TEXT = (32, 33, 36)
    BUTTON_DISABLED = (200, 200, 200)
    TOOLTIP_BG = (50, 50, 60, 240)  # Dark with transparency


# --- Load Fonts ---
class Fonts:
    @staticmethod
    def init():
        """Initialize with fallback to system fonts if custom fonts aren't available"""
        Fonts.TITLE = pygame.font.Font(None, 56)
        Fonts.HEADING = pygame.font.Font(None, 42)
        Fonts.BUTTON = pygame.font.Font(None, 34)
        Fonts.NORMAL = pygame.font.Font(None, 28)
        Fonts.SMALL = pygame.font.Font(None, 22)

        # Note: We use pygame's default anti-aliasing for text rendering
        # The render method's first parameter controls anti-aliasing


Fonts.init()


# --- UI Components ---
class ComponentType(Enum):
    BUTTON = auto()
    PANEL = auto()
    LABEL = auto()
    IMAGE = auto()


@dataclass
class UIComponent:
    """Base class for UI components with common properties"""

    rect: pygame.Rect
    component_type: ComponentType
    visible: bool = True
    enabled: bool = True

    # Visual properties
    bg_color: Optional[Tuple[int, int, int]] = None
    border_color: Optional[Tuple[int, int, int]] = None
    border_width: int = 0
    corner_radius: int = 0
    alpha: int = 255  # 0-255 transparency

    # Internal
    _hovered: bool = False
    _pressed: bool = False

    def is_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if mouse is hovering over this component"""
        if not self.visible or not self.enabled:
            return False
        return self.rect.collidepoint(mouse_pos)

    def update(self, mouse_pos: Tuple[int, int]) -> None:
        """Update component state based on mouse position"""
        self._hovered = self.is_hovered(mouse_pos)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the component to the given surface"""
        if not self.visible:
            return

        # Draw background with rounded corners if set
        if self.bg_color:
            if self.corner_radius > 0:
                draw_rounded_rect(surface, self.rect, self.bg_color, self.corner_radius)
            else:
                pygame.draw.rect(surface, self.bg_color, self.rect)

        # Draw border with rounded corners if set
        if self.border_color and self.border_width > 0:
            if self.corner_radius > 0:
                draw_rounded_rect(
                    surface,
                    self.rect,
                    self.border_color,
                    self.corner_radius,
                    self.border_width,
                )
            else:
                pygame.draw.rect(
                    surface, self.border_color, self.rect, self.border_width
                )


class Button(UIComponent):
    """Interactive button with hover/click states"""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        on_click: Callable = None,
        bg_color: Tuple[int, int, int] = Colors.BUTTON_NORMAL,
        hover_color: Tuple[int, int, int] = Colors.BUTTON_HOVER,
        text_color: Tuple[int, int, int] = Colors.BUTTON_TEXT,
        disabled_color: Tuple[int, int, int] = Colors.BUTTON_DISABLED,
        border_color: Tuple[int, int, int] = Colors.PANEL_BORDER,
        font: pygame.font.Font = Fonts.BUTTON,
        corner_radius: int = CORNER_RADIUS,
        border_width: int = BORDER_WIDTH,
        icon: Optional[pygame.Surface] = None,
    ):
        super().__init__(
            rect=rect,
            component_type=ComponentType.BUTTON,
            bg_color=bg_color,
            border_color=border_color,
            border_width=border_width,
            corner_radius=corner_radius,
        )
        self.text = text
        self.on_click = on_click
        self.hover_color = hover_color
        self.text_color = text_color
        self.disabled_color = disabled_color
        self.font = font
        self.icon = icon
        self.icon_padding = 10 if icon else 0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events and return True if clicked"""
        if not self.visible or not self.enabled:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hovered:
                self._pressed = True
                return False

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self._pressed
            self._pressed = False

            if was_pressed and self._hovered and self.on_click:
                self.on_click()
                return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw button with hover/press effects"""
        if not self.visible:
            return

        # Determine background color based on state
        if not self.enabled:
            bg = self.disabled_color
        elif self._pressed and self._hovered:
            # Slightly darker when pressed
            bg = tuple(max(0, c - 20) for c in self.hover_color)
        elif self._hovered:
            bg = self.hover_color
        else:
            bg = self.bg_color

        # Store original and set current background for parent draw
        original_bg = self.bg_color
        self.bg_color = bg

        # Draw button background and border
        super().draw(surface)

        # Restore original background
        self.bg_color = original_bg

        # Render text centered on button
        text_surf = self.font.render(self.text, True, self.text_color)

        # Account for icon if present
        icon_offset = 0
        if self.icon:
            icon_offset = (self.icon.get_width() + self.icon_padding) // 2
            icon_rect = self.icon.get_rect(
                centery=self.rect.centery, right=self.rect.centerx - 5
            )
            surface.blit(self.icon, icon_rect)

        # Position text
        text_rect = text_surf.get_rect(
            center=(self.rect.centerx + icon_offset, self.rect.centery)
        )
        surface.blit(text_surf, text_rect)


class Panel(UIComponent):
    """Container panel with optional title and border"""

    def __init__(
        self,
        rect: pygame.Rect,
        title: Optional[str] = None,
        bg_color: Tuple[int, int, int] = Colors.PANEL_BG,
        border_color: Tuple[int, int, int] = Colors.PANEL_BORDER,
        title_color: Tuple[int, int, int] = Colors.TEXT_DARK,
        corner_radius: int = CORNER_RADIUS,
        border_width: int = BORDER_WIDTH,
        title_font: pygame.font.Font = Fonts.HEADING,
    ):
        super().__init__(
            rect=rect,
            component_type=ComponentType.PANEL,
            bg_color=bg_color,
            border_color=border_color,
            border_width=border_width,
            corner_radius=corner_radius,
        )
        self.title = title
        self.title_color = title_color
        self.title_font = title_font
        self.title_height = title_font.get_height() + PADDING if title else 0

        # Content area is the panel minus padding and title
        self.content_rect = pygame.Rect(
            self.rect.x + PADDING,
            self.rect.y + PADDING + self.title_height,
            self.rect.width - (PADDING * 2),
            self.rect.height - (PADDING * 2) - self.title_height,
        )

    def draw(self, surface: pygame.Surface) -> None:
        """Draw panel with optional title"""
        if not self.visible:
            return

        # Draw panel background and border
        super().draw(surface)

        # Draw title if provided
        if self.title:
            title_surf = self.title_font.render(self.title, True, self.title_color)
            title_rect = title_surf.get_rect(
                x=self.rect.x + PADDING, y=self.rect.y + PADDING // 2
            )
            surface.blit(title_surf, title_rect)

            # Draw separator line below title
            pygame.draw.line(
                surface,
                self.border_color,
                (self.rect.x + PADDING, self.rect.y + self.title_height),
                (self.rect.right - PADDING, self.rect.y + self.title_height),
                1,
            )


class ScrollPanel(Panel):
    """Panel with a vertical scroll area for overflowing content.

    Supports smooth wheel scrolling and dragging the scrollbar thumb.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scroll_y = 0.0
        self.content_height = 0
        self.scrollbar_width = 10
        self.scroll_active = False

        # smooth scrolling target and drag state
        self.target_scroll = 0.0
        self.smooth_factor = 0.18  # interpolation factor (0..1)
        self._dragging = False
        self._drag_offset = 0

    def set_content_height(self, h: int) -> None:
        self.content_height = h
        # clamp scroll and target to valid range
        max_scroll = max(0, self.content_height - self.content_rect.height)
        self.scroll_y = max(0.0, min(self.scroll_y, float(max_scroll)))
        self.target_scroll = max(0.0, min(self.target_scroll, float(max_scroll)))

    def handle_event(self, event: pygame.event.Event) -> None:
        # Wheel scrolling: adjust target for smooth scroll
        if event.type == pygame.MOUSEWHEEL:
            # Only scroll if mouse is over panel
            if self.content_rect.collidepoint(pygame.mouse.get_pos()):
                max_scroll = max(0, self.content_height - self.content_rect.height)
                # larger delta for more responsive scroll
                self.target_scroll = max(
                    0.0, min(float(max_scroll), self.target_scroll - event.y * 60.0)
                )

        # Mouse button for dragging the thumb
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            thumb = self._thumb_rect()
            if thumb and thumb.collidepoint((mx, my)):
                self._dragging = True
                self._drag_offset = my - thumb.y

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False

        elif event.type == pygame.MOUSEMOTION and self._dragging:
            # Map mouse y to scroll position
            _, my = pygame.mouse.get_pos()
            view_h = self.content_rect.height
            max_scroll = max(0, self.content_height - view_h)
            thumb = self._thumb_rect()
            if not thumb:
                return
            thumb_h = thumb.height
            # Compute top of thumb relative to content_rect
            rel_y = my - self.content_rect.y - self._drag_offset
            rel_y = max(0, min(rel_y, view_h - thumb_h))
            proportion = rel_y / max(1, (view_h - thumb_h))
            self.target_scroll = int(proportion * max_scroll)

    def draw(self, surface: pygame.Surface) -> None:
        # Draw the panel frame
        super().draw(surface)

        # Clip content drawing to the content_rect
        prev_clip = surface.get_clip()
        surface.set_clip(self.content_rect)

        # Smoothly approach target_scroll
        if abs(self.target_scroll - self.scroll_y) > 0.5:
            self.scroll_y += (self.target_scroll - self.scroll_y) * self.smooth_factor
        else:
            self.scroll_y = float(self.target_scroll)

        # draw a faint scrollbar if needed
        if self.content_height > self.content_rect.height:
            self._draw_scrollbar(surface)

        surface.set_clip(prev_clip)

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        # compute thumb height
        view_h = self.content_rect.height
        thumb_h = max(30, int(view_h * (view_h / self.content_height)))
        max_scroll = self.content_height - view_h
        if max_scroll <= 0:
            thumb_y = self.content_rect.y
        else:
            thumb_y = int(
                self.content_rect.y + (self.scroll_y / max_scroll) * (view_h - thumb_h)
            )

        thumb_rect = pygame.Rect(
            self.content_rect.right - self.scrollbar_width - 6,
            thumb_y,
            self.scrollbar_width,
            thumb_h,
        )
        pygame.draw.rect(surface, (200, 200, 200), thumb_rect, border_radius=4)

    def _thumb_rect(self) -> Optional[pygame.Rect]:
        """Return the current scrollbar thumb rect (or None if not needed)"""
        if self.content_height <= self.content_rect.height:
            return None
        view_h = self.content_rect.height
        thumb_h = max(30, int(view_h * (view_h / self.content_height)))
        max_scroll = self.content_height - view_h
        if max_scroll <= 0:
            thumb_y = self.content_rect.y
        else:
            thumb_y = int(
                self.content_rect.y + (self.scroll_y / max_scroll) * (view_h - thumb_h)
            )
        return pygame.Rect(
            self.content_rect.right - self.scrollbar_width - 6,
            thumb_y,
            self.scrollbar_width,
            thumb_h,
        )


class Label:
    """Text label with wrapping support"""

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        font: pygame.font.Font = Fonts.NORMAL,
        color: Tuple[int, int, int] = Colors.TEXT_DARK,
        max_width: Optional[int] = None,
        align: str = "left",
        padding: int = 0,
        line_spacing: float = 1.0,
        tracking: int = 0,
    ):
        self.text = text
        self.x = x
        self.y = y
        self.font = font
        self.color = color
        self.max_width = max_width
        self.align = align
        self.padding = padding
        self.line_spacing = line_spacing
        self.tracking = tracking
        self._rendered_lines = []
        self._height = 0
        self._width = 0
        self._render_text()

    def _render_text(self) -> None:
        """Pre-render wrapped text lines"""
        self._rendered_lines = []
        self._height = 0
        self._width = 0

        if not self.text:
            return

        # If max width is set, wrap text using font-aware measurement
        if self.max_width:
            wrapped_lines = []
            for line in self.text.splitlines():
                if not line:
                    wrapped_lines.append("")
                    continue
                # Use the helper which measures words with the font for accurate wrapping
                wrapped_lines.extend(wrap_text(line, self.font, self.max_width))
        else:
            # No wrapping, just split on newlines
            wrapped_lines = self.text.splitlines()

        # Render each line with tracking and line spacing
        base_line_height = self.font.get_linesize()
        line_height = int(base_line_height * self.line_spacing)
        for i, line in enumerate(wrapped_lines):
            if not line:  # Blank line
                self._height += line_height
                continue

            if self.tracking == 0:
                # Normal rendering
                line_surf = self.font.render(line, True, self.color)
            else:
                # Render per-character to apply tracking
                parts = [self.font.render(ch, True, self.color) for ch in line]
                width = sum(p.get_width() for p in parts) + self.tracking * (
                    len(parts) - 1
                )
                line_surf = pygame.Surface((width, base_line_height), pygame.SRCALPHA)
                x_offset = 0
                for p in parts:
                    line_surf.blit(p, (x_offset, 0))
                    x_offset += p.get_width() + self.tracking

            line_rect = line_surf.get_rect()

            # Track maximum width
            self._width = max(self._width, line_rect.width)

            # Position based on alignment
            if self.align == "center":
                line_rect.centerx = self.x
            elif self.align == "right":
                line_rect.right = self.x
            else:  # left
                line_rect.left = self.x

            line_rect.top = self.y + i * line_height

            self._rendered_lines.append((line_surf, line_rect))
            self._height += line_height

    def update_text(self, new_text: str) -> None:
        """Update the label text and re-render"""
        if self.text != new_text:
            self.text = new_text
            self._render_text()

    @property
    def height(self) -> int:
        """Get the total height of wrapped text"""
        return self._height + (self.padding * 2)

    @property
    def width(self) -> int:
        """Get the maximum width of wrapped text"""
        return self._width + (self.padding * 2)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all rendered text lines"""
        for line_surf, line_rect in self._rendered_lines:
            surface.blit(line_surf, line_rect)


# --- Helper Functions ---
def draw_rounded_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: Tuple[int, int, int],
    corner_radius: int,
    border_width: int = 0,
) -> None:
    """Draw a rectangle with rounded corners"""
    if corner_radius <= 0:
        if border_width:
            pygame.draw.rect(surface, color, rect, border_width)
        else:
            pygame.draw.rect(surface, color, rect)
        return

    # Adjust radius if it's too large for the rect
    corner_radius = min(corner_radius, rect.width // 2, rect.height // 2)

    if border_width:
        # For borders, we need to draw lines connecting the arcs
        # Top horizontal line
        pygame.draw.line(
            surface,
            color,
            (rect.left + corner_radius, rect.top),
            (rect.right - corner_radius, rect.top),
            border_width,
        )
        # Bottom horizontal line
        pygame.draw.line(
            surface,
            color,
            (rect.left + corner_radius, rect.bottom),
            (rect.right - corner_radius, rect.bottom),
            border_width,
        )
        # Left vertical line
        pygame.draw.line(
            surface,
            color,
            (rect.left, rect.top + corner_radius),
            (rect.left, rect.bottom - corner_radius),
            border_width,
        )
        # Right vertical line
        pygame.draw.line(
            surface,
            color,
            (rect.right, rect.top + corner_radius),
            (rect.right, rect.bottom - corner_radius),
            border_width,
        )

        # Draw the corner arcs
        pygame.draw.arc(
            surface,
            color,
            pygame.Rect(rect.left, rect.top, corner_radius * 2, corner_radius * 2),
            3 * math.pi / 2,
            2 * math.pi,
            border_width,
        )
        pygame.draw.arc(
            surface,
            color,
            pygame.Rect(
                rect.right - corner_radius * 2,
                rect.top,
                corner_radius * 2,
                corner_radius * 2,
            ),
            0,
            math.pi / 2,
            border_width,
        )
        pygame.draw.arc(
            surface,
            color,
            pygame.Rect(
                rect.left,
                rect.bottom - corner_radius * 2,
                corner_radius * 2,
                corner_radius * 2,
            ),
            math.pi,
            3 * math.pi / 2,
            border_width,
        )
        pygame.draw.arc(
            surface,
            color,
            pygame.Rect(
                rect.right - corner_radius * 2,
                rect.bottom - corner_radius * 2,
                corner_radius * 2,
                corner_radius * 2,
            ),
            math.pi / 2,
            math.pi,
            border_width,
        )
    else:
        # For filled rects, we draw filled shapes and connect them
        # Draw the main rect
        pygame.draw.rect(
            surface,
            color,
            pygame.Rect(
                rect.left + corner_radius,
                rect.top,
                rect.width - 2 * corner_radius,
                rect.height,
            ),
        )
        # Draw side rects
        pygame.draw.rect(
            surface,
            color,
            pygame.Rect(
                rect.left,
                rect.top + corner_radius,
                corner_radius,
                rect.height - 2 * corner_radius,
            ),
        )
        pygame.draw.rect(
            surface,
            color,
            pygame.Rect(
                rect.right - corner_radius,
                rect.top + corner_radius,
                corner_radius,
                rect.height - 2 * corner_radius,
            ),
        )

        # Draw the corner circles
        pygame.draw.circle(
            surface,
            color,
            (rect.left + corner_radius, rect.top + corner_radius),
            corner_radius,
        )
        pygame.draw.circle(
            surface,
            color,
            (rect.right - corner_radius, rect.top + corner_radius),
            corner_radius,
        )
        pygame.draw.circle(
            surface,
            color,
            (rect.left + corner_radius, rect.bottom - corner_radius),
            corner_radius,
        )
        pygame.draw.circle(
            surface,
            color,
            (rect.right - corner_radius, rect.bottom - corner_radius),
            corner_radius,
        )


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """Wrap text to fit within a given width"""
    words = text.split(" ")
    lines = []
    current_line = []

    for word in words:
        # Test width with this word added
        test_line = " ".join(current_line + [word])
        test_width = font.size(test_line)[0]

        if test_width <= max_width:
            current_line.append(word)
        else:
            # Line would be too long, start a new one
            if current_line:  # Add the current line if it has content
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # Handle case where a single word is too long
                lines.append(word)
                current_line = []

    # Add the last line if there's content
    if current_line:
        lines.append(" ".join(current_line))

    return lines


def find_font_for_width(
    text: str,
    max_width: int,
    font_name: Optional[str] = None,
    max_size: int = 72,
    min_size: int = 24,
) -> pygame.font.Font:
    """Return a pygame Font sized so 'text' fits within max_width on one line if possible.

    The function tries sizes from max_size down to min_size and returns the first
    font whose rendered width is <= max_width. If none fit, returns the font at
    min_size (the Label will then wrap if a max_width is supplied).
    """
    # Try larger sizes first to keep the title visually prominent
    for size in range(max_size, min_size - 1, -1):
        f = pygame.font.Font(font_name, size)
        w, _ = f.size(text)
        if w <= max_width:
            return f
    return pygame.font.Font(font_name, min_size)


# --- UI Screens ---

# Save path
SAVE_PATH = os.path.join(os.path.dirname(__file__), "simulation_state.json")

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("USA Political Simulation")


class MainMenu:
    """Main menu screen with stylish buttons"""

    def __init__(self):
        self.buttons = []
        self.selected_index = 0

        # Create background gradient
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            # Gradient from navy to lighter blue
            r = 32 + int((y / SCREEN_HEIGHT) * 20)
            g = 34 + int((y / SCREEN_HEIGHT) * 20)
            b = 48 + int((y / SCREEN_HEIGHT) * 60)
            pygame.draw.line(self.background, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Set up menu panel
        panel_width = 400
        panel_height = 500
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2

        self.panel = Panel(
            rect=pygame.Rect(panel_x, panel_y, panel_width, panel_height),
            bg_color=Colors.PANEL_BG,
            border_color=Colors.PANEL_BORDER,
            corner_radius=CORNER_RADIUS + 4,
            border_width=BORDER_WIDTH,
        )

        # Calculate content positions relative to panel
        content_x = panel_x + panel_width // 2  # Center of panel

        # Title - constrain to the panel content width so it wraps/scales
        title_max_w = max(100, self.panel.content_rect.width - PADDING)
        title_y = panel_y + 40

        # Auto-scale title font to keep on a single line if possible
        title_text = "USA Political Simulation"
        title_font_scaled = find_font_for_width(
            title_text, title_max_w, None, max_size=56, min_size=28
        )
        self.title = Label(
            title_text,
            x=content_x,
            y=title_y,
            font=title_font_scaled,
            color=Colors.TEXT_DARK,
            align="center",
            max_width=title_max_w,
            padding=6,
        )

        # Compute subtitle position immediately below the title using the measured title height
        subtitle_y = title_y + self.title.height + 8
        subtitle_max_w = max(80, self.panel.content_rect.width - PADDING * 2)
        self.subtitle = Label(
            "Navigate with Up/Down arrows or mouse. Press Enter to select.",
            x=content_x,
            y=subtitle_y,
            font=Fonts.SMALL,
            color=Colors.TEXT_MUTED,
            align="center",
            max_width=subtitle_max_w,
            padding=4,
        )

        # Create menu buttons - ensure they're centered in the panel and placed beneath subtitle
        button_width = MENU_BUTTON_WIDTH
        button_y = subtitle_y + self.subtitle.height + 28

        for i, (text, action) in enumerate(
            [
                ("Start Game", self.start_game),
                ("Load Game", self.load_game),
                ("Quit", self.quit_game),
            ]
        ):
            button = Button(
                rect=pygame.Rect(
                    panel_x + (panel_width - button_width) // 2,
                    button_y + i * (BUTTON_HEIGHT + 20),
                    button_width,
                    BUTTON_HEIGHT,
                ),
                text=text,
                on_click=action,
                bg_color=Colors.BUTTON_NORMAL,
                hover_color=Colors.BUTTON_HOVER,
                text_color=Colors.TEXT_DARK,
                border_color=Colors.PANEL_BORDER,
                corner_radius=CORNER_RADIUS,
            )
            self.buttons.append(button)

        # Footer
        self.footer = Label(
            "© 2025 Political Simulation - ESC to quit",
            x=SCREEN_WIDTH // 2,
            y=SCREEN_HEIGHT - 30,
            font=Fonts.SMALL,
            color=Colors.TEXT_MUTED,
            align="center",
        )

    def start_game(self) -> None:
        game_screen = GameScreen()
        game_screen.run()

    def load_game(self) -> None:
        loaded = None
        if os.path.exists(SAVE_PATH):
            try:
                loaded = UnitedStates.load_from_file(SAVE_PATH)
            except Exception:
                loaded = None

        game_screen = GameScreen(loaded_state=loaded)
        game_screen.run()

    def quit_game(self) -> None:
        pygame.quit()
        sys.exit()

    def handle_events(self) -> bool:
        """Process events and return False if should exit menu"""
        mouse_pos = pygame.mouse.get_pos()

        # Update all buttons
        for button in self.buttons:
            button.update(mouse_pos)

        # Check if mouse is hovering over any button to update selected_index
        for i, button in enumerate(self.buttons):
            if button._hovered:
                self.selected_index = i

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                elif event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.buttons)

                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.buttons)

                elif event.key == pygame.K_RETURN:
                    self.buttons[self.selected_index].on_click()

            # Pass events to buttons for click handling
            for i, button in enumerate(self.buttons):
                if button.handle_event(event):
                    return False

        return True

    def draw(self) -> None:
        """Render the menu screen"""
        # Draw background gradient
        screen.blit(self.background, (0, 0))

        # Draw panel
        self.panel.draw(screen)

        # Draw title and subtitle
        self.title.draw(screen)
        self.subtitle.draw(screen)

        # Draw menu buttons
        for i, button in enumerate(self.buttons):
            # First draw the button
            button.draw(screen)

            # Then add selection indicator if this button is selected
            if i == self.selected_index:
                # Calculate indicator positions
                circle_x = button.rect.x + 20  # Place inside the button
                circle_y = button.rect.y + (button.rect.height // 2)

                # Draw a dot inside the button
                pygame.draw.circle(screen, Colors.PRIMARY, (circle_x, circle_y), 5)

        # Draw footer
        self.footer.draw(screen)

        pygame.display.flip()

    def run(self) -> None:
        """Main menu loop"""
        clock = pygame.time.Clock()

        running = True
        while running:
            running = self.handle_events()
            self.draw()
            clock.tick(FRAME_RATE)


class GameScreen:
    """Game screen with simulation view and controls"""

    def __init__(self, loaded_state: Optional[UnitedStates] = None, seed: int = 42):
        self.us = loaded_state if loaded_state else UnitedStates.new_default(seed=seed)
        self.info_msg = None
        self.info_timer = 0

        # Create UI components

        # Header panel (year, month, key stats)
        self.header_panel = Panel(
            rect=pygame.Rect(PADDING, PADDING, SCREEN_WIDTH - PADDING * 2, 120),
            bg_color=Colors.PANEL_BG,
            border_color=Colors.PANEL_BORDER,
            corner_radius=CORNER_RADIUS,
        )

        # Stats panel (economy, approval, budget) - make scrollable
        self.stats_panel = ScrollPanel(
            rect=pygame.Rect(PADDING, 140, (SCREEN_WIDTH - PADDING * 3) // 2, 180),
            title="National Statistics",
            bg_color=Colors.PANEL_BG,
            border_color=Colors.PANEL_BORDER,
            corner_radius=CORNER_RADIUS,
        )

        # States panel
        states_panel_x = (SCREEN_WIDTH - PADDING * 3) // 2 + PADDING * 2
        self.states_panel = ScrollPanel(
            rect=pygame.Rect(
                states_panel_x, 140, (SCREEN_WIDTH - PADDING * 3) // 2, 180
            ),
            title="Key States",
            bg_color=Colors.PANEL_BG,
            border_color=Colors.PANEL_BORDER,
            corner_radius=CORNER_RADIUS,
        )

        # Controls panel
        controls_width = 240
        self.controls_panel = Panel(
            rect=pygame.Rect(
                PADDING, 340, controls_width, SCREEN_HEIGHT - 340 - PADDING
            ),
            title="Controls",
            bg_color=Colors.PANEL_BG,
            border_color=Colors.PANEL_BORDER,
            corner_radius=CORNER_RADIUS,
        )

        # Log panel
        log_panel_x = controls_width + PADDING * 2
        self.log_panel = ScrollPanel(
            rect=pygame.Rect(
                log_panel_x,
                340,
                SCREEN_WIDTH - log_panel_x - PADDING,
                SCREEN_HEIGHT - 340 - PADDING,
            ),
            title="Recent Events",
            bg_color=Colors.PANEL_BG,
            border_color=Colors.PANEL_BORDER,
            corner_radius=CORNER_RADIUS,
        )

        # Action buttons
        button_width = 180
        button_spacing = 15  # Reduced spacing to fit buttons
        button_y = self.controls_panel.content_rect.y + 10
        button_x = (
            self.controls_panel.rect.x
            + (self.controls_panel.rect.width - button_width) // 2
        )

        self.buttons = {
            "advance1": Button(
                rect=pygame.Rect(button_x, button_y, button_width, BUTTON_HEIGHT),
                text="Advance 1 Month",
                on_click=lambda: self.advance_turn(1),
                bg_color=Colors.PRIMARY,
                hover_color=tuple(min(255, c + 20) for c in Colors.PRIMARY),
                text_color=Colors.TEXT_LIGHT,
                font=Fonts.NORMAL,  # Use smaller font
                border_color=None,
            ),
            "advance12": Button(
                rect=pygame.Rect(
                    button_x,
                    button_y + BUTTON_HEIGHT + button_spacing,
                    button_width,
                    BUTTON_HEIGHT,
                ),
                text="Advance 1 Year",
                on_click=lambda: self.advance_turn(12),
                bg_color=Colors.SECONDARY,
                hover_color=tuple(min(255, c + 20) for c in Colors.SECONDARY),
                text_color=Colors.TEXT_LIGHT,
                font=Fonts.BUTTON,
                border_color=None,
            ),
            "event": Button(
                rect=pygame.Rect(
                    button_x,
                    button_y + (BUTTON_HEIGHT + button_spacing) * 2,
                    button_width,
                    BUTTON_HEIGHT,
                ),
                text="Trigger Event",
                on_click=self.trigger_event,
                bg_color=Colors.ACCENT,
                hover_color=tuple(min(255, c + 20) for c in Colors.ACCENT),
                text_color=Colors.TEXT_DARK,
                font=Fonts.BUTTON,
                border_color=None,
            ),
            "save": Button(
                rect=pygame.Rect(
                    button_x,
                    button_y + (BUTTON_HEIGHT + button_spacing) * 3,
                    button_width,
                    BUTTON_HEIGHT,
                ),
                text="Save Game",
                on_click=self.save_game,
                bg_color=Colors.SUCCESS,
                hover_color=tuple(min(255, c + 20) for c in Colors.SUCCESS),
                text_color=Colors.TEXT_LIGHT,
                font=Fonts.BUTTON,
                border_color=None,
            ),
            "load": Button(
                rect=pygame.Rect(
                    button_x,
                    button_y + (BUTTON_HEIGHT + button_spacing) * 4,
                    button_width,
                    BUTTON_HEIGHT,
                ),
                text="Load Game",
                on_click=self.load_game,
                bg_color=Colors.WARNING,
                hover_color=tuple(min(255, c + 20) for c in Colors.WARNING),
                text_color=Colors.TEXT_DARK,
                font=Fonts.BUTTON,
                border_color=None,
            ),
            "menu": Button(
                rect=pygame.Rect(
                    button_x,
                    button_y + (BUTTON_HEIGHT + button_spacing) * 5,
                    button_width,
                    BUTTON_HEIGHT,
                ),
                text="Return to Menu",
                on_click=self.return_to_menu,
                bg_color=(100, 100, 100),
                hover_color=(120, 120, 120),
                text_color=Colors.TEXT_LIGHT,
                font=Fonts.NORMAL,  # Use smaller font
                border_color=None,
            ),
        }

        # Initialize dynamic labels (will be updated in update_ui)
        # Auto-scale header to fit the header panel content width and constrain it
        header_max_w = max(200, self.header_panel.content_rect.width - PADDING)
        header_text = f"USA Simulation: Year {self.us.year}  Month {self.us.month:02d}"
        header_font = find_font_for_width(
            header_text, header_max_w, None, max_size=40, min_size=20
        )
        self.header_label = Label(
            header_text,
            x=self.header_panel.content_rect.x + PADDING,
            y=self.header_panel.content_rect.y + PADDING,
            font=header_font,
            color=Colors.TEXT_DARK,
            max_width=header_max_w,
        )

        # Placeholder for other dynamic labels
        self.labels = {}

        # Create initial log text
        self.log_text = "\n".join(
            self.us.log[-12:] if self.us.log else ["No events yet."]
        )

    def advance_turn(self, months: int) -> None:
        """Advance the simulation by given months"""
        self.us.advance_turn(months)

        plural = "month" if months == 1 else "months"
        self.set_info_message(f"Advanced {months} {plural}", Colors.SUCCESS)

        # Update UI with new state
        self.update_ui()

    def trigger_event(self) -> None:
        """Trigger a random event"""
        ev = self.us.trigger_event()

        if ev:
            # React immediately as in monthly loop
            self.us.ai_react_to_events()
            self.set_info_message(f"Event: {ev.name}", Colors.ACCENT)
        else:
            self.set_info_message("No event triggered", Colors.WARNING)

        # Update UI with new state
        self.update_ui()

    def save_game(self) -> None:
        """Save game to file"""
        try:
            self.us.save_to_file(SAVE_PATH)
            self.set_info_message(
                f"Saved to {os.path.basename(SAVE_PATH)}", Colors.SUCCESS
            )
        except Exception as ex:
            self.set_info_message(f"Save failed: {ex}", Colors.ERROR)

    def load_game(self) -> None:
        """Load game from file"""
        try:
            if os.path.exists(SAVE_PATH):
                self.us = UnitedStates.load_from_file(SAVE_PATH)
                self.set_info_message(
                    f"Loaded {os.path.basename(SAVE_PATH)}", Colors.SUCCESS
                )
                # Update UI with loaded state
                self.update_ui()
            else:
                self.set_info_message("No save file found", Colors.WARNING)
        except Exception as ex:
            self.set_info_message(f"Load failed: {ex}", Colors.ERROR)

    def return_to_menu(self) -> None:
        """Return to main menu"""
        self.running = False

    def set_info_message(
        self, message: str, color: Tuple[int, int, int] = Colors.SUCCESS
    ) -> None:
        """Set a temporary info message with color"""
        self.info_msg = message
        self.info_color = color
        self.info_timer = 180  # frames (3 seconds at 60 FPS)

    def update_ui(self) -> None:
        """Update all dynamic UI elements with current state"""
        # Update header
        self.header_label.update_text(
            f"USA Simulation: Year {self.us.year}  Month {self.us.month:02d}"
        )

        # Update national stats
        stats_x = self.stats_panel.content_rect.x
        stats_y = self.stats_panel.content_rect.y

        # Format economy stats with color coding
        growth_color = (
            Colors.SUCCESS
            if self.us.growth > 0.01
            else Colors.ERROR if self.us.growth < 0 else Colors.TEXT_DARK
        )
        unemp_color = (
            Colors.SUCCESS
            if self.us.unemployment < 5.0
            else Colors.ERROR if self.us.unemployment > 7.0 else Colors.WARNING
        )
        infl_color = (
            Colors.SUCCESS
            if self.us.inflation < 2.5
            else Colors.ERROR if self.us.inflation > 4.0 else Colors.WARNING
        )

        # Stack national statistics deterministically using a vertical cursor
        stat_w = self.stats_panel.content_rect.width - PADDING
        cursor_y = stats_y
        line_gap = 6

        # Economy lines
        for key, text, color in [
            ("growth", f"Growth: {self.us.growth*100:.1f}%", growth_color),
            ("unemployment", f"Unemployment: {self.us.unemployment:.1f}%", unemp_color),
            ("inflation", f"Inflation: {self.us.inflation:.1f}%", infl_color),
        ]:
            lbl = Label(
                text,
                x=stats_x,
                y=cursor_y,
                font=Fonts.NORMAL,
                color=color,
                max_width=stat_w,
            )
            self.labels[key] = lbl
            self.labels[key]._parent = self.stats_panel
            cursor_y += lbl.height + line_gap

        # Approval ratings
        pres_approval_color = (
            Colors.SUCCESS
            if self.us.opinion.approval_president > 55
            else (
                Colors.ERROR
                if self.us.opinion.approval_president < 40
                else Colors.WARNING
            )
        )
        cong_approval_color = (
            Colors.SUCCESS
            if self.us.opinion.approval_congress > 45
            else (
                Colors.ERROR
                if self.us.opinion.approval_congress < 30
                else Colors.WARNING
            )
        )

        lbl = Label(
            f"President: {self.us.opinion.approval_president:.1f}%",
            x=stats_x,
            y=cursor_y,
            font=Fonts.NORMAL,
            color=pres_approval_color,
            max_width=stat_w,
        )
        self.labels["pres_approval"] = lbl
        self.labels["pres_approval"]._parent = self.stats_panel
        cursor_y += lbl.height + line_gap

        lbl = Label(
            f"Congress: {self.us.opinion.approval_congress:.1f}%",
            x=stats_x,
            y=cursor_y,
            font=Fonts.NORMAL,
            color=cong_approval_color,
            max_width=stat_w,
        )
        self.labels["cong_approval"] = lbl
        self.labels["cong_approval"]._parent = self.stats_panel
        cursor_y += lbl.height + line_gap

        # Budget line
        deficit = self.us.budget.deficit
        budget_color = (
            Colors.SUCCESS
            if deficit < 0
            else Colors.ERROR if deficit > 800 else Colors.WARNING
        )
        lbl = Label(
            f"Budget: Rev ${self.us.budget.revenue:.0f}B | Spend ${self.us.budget.spending:.0f}B | Deficit ${deficit:.0f}B",
            x=stats_x,
            y=cursor_y,
            font=Fonts.NORMAL,
            color=budget_color,
            max_width=stat_w,
        )
        self.labels["budget"] = lbl
        self.labels["budget"]._parent = self.stats_panel
        cursor_y += lbl.height + line_gap

        # Set content height for stats panel based on stacked labels
        total_stats_h = cursor_y - stats_y
        self.stats_panel.set_content_height(
            max(self.stats_panel.content_rect.height, int(total_stats_h + PADDING))
        )

        # Update states info
        states_x = self.states_panel.content_rect.x
        states_y = self.states_panel.content_rect.y

        # Lay out state labels vertically using measured heights to avoid overlap
        current_state_y = states_y
        for i, name in enumerate(list(self.us.states.keys())[:8]):
            st = self.us.states[name]
            state_label_key = f"state_{i}"

            gdp_color = Colors.SUCCESS if st.gdp > 2000 else Colors.TEXT_DARK
            unemp_color = (
                Colors.SUCCESS
                if st.unemployment < 5.0
                else Colors.ERROR if st.unemployment > 7.0 else Colors.WARNING
            )

            lbl = Label(
                f"{name}: GDP ${st.gdp:.0f}B | Unemp {st.unemployment:.1f}% | Gov: {st.governor_party.value}",
                x=states_x,
                y=current_state_y,
                font=Fonts.NORMAL,
                color=Colors.TEXT_DARK,
                max_width=self.states_panel.content_rect.width - PADDING,
            )
            self.labels[state_label_key] = lbl
            self.labels[state_label_key]._parent = self.states_panel
            current_state_y += lbl.height + 6
        # Compute content height for states panel (stacked entries)
        total_states_h = 0
        for k in [k for k in self.labels.keys() if k.startswith("state_")]:
            total_states_h += self.labels[k].height
        self.states_panel.set_content_height(
            max(self.states_panel.content_rect.height, total_states_h + PADDING)
        )

        # Update log with recent events
        recent_logs = self.us.log[-12:] if self.us.log else ["No events yet."]
        self.log_text = "\n".join(recent_logs)
        # Estimate log content height and set scrollable height
        # Render a temporary log_label to measure height
        temp_log = Label(
            self.log_text,
            x=0,
            y=0,
            font=Fonts.SMALL,
            max_width=self.log_panel.content_rect.width - PADDING,
        )
        self.log_panel.set_content_height(
            max(self.log_panel.content_rect.height, temp_log.height + PADDING)
        )

    def handle_events(self) -> None:
        """Process pygame events"""
        mouse_pos = pygame.mouse.get_pos()

        # Update all buttons
        for button in self.buttons.values():
            button.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.return_to_menu()
                elif event.key == pygame.K_SPACE:
                    self.advance_turn(1)
                elif event.key == pygame.K_a:
                    self.advance_turn(12)
                elif event.key == pygame.K_e:
                    self.trigger_event()
                elif event.key == pygame.K_s:
                    self.save_game()
                elif event.key == pygame.K_l:
                    self.load_game()

            # Pass events to buttons
            for button in self.buttons.values():
                button.handle_event(event)
            # Forward wheel events to scroll panels
            if event.type == pygame.MOUSEWHEEL:
                self.stats_panel.handle_event(event)
                self.states_panel.handle_event(event)
                self.log_panel.handle_event(event)

    def draw(self) -> None:
        """Render the game screen"""
        # Fill background
        screen.fill(Colors.BG_LIGHT)

        # Draw panels
        self.header_panel.draw(screen)
        self.stats_panel.draw(screen)
        self.states_panel.draw(screen)
        self.controls_panel.draw(screen)
        self.log_panel.draw(screen)

        # Draw header
        self.header_label.draw(screen)

        # Draw all labels
        # Draw labels, handling scroll offsets for panels
        # Header/stats/controls labels are drawn normally
        for k, label in self.labels.items():
            parent = getattr(label, "_parent", None)
            if parent is not None and isinstance(parent, Panel):
                prev_clip = screen.get_clip()
                screen.set_clip(parent.content_rect)

                # If parent is a ScrollPanel, apply vertical scroll offset
                scroll_y = parent.scroll_y if hasattr(parent, "scroll_y") else 0
                for surf, rect in label._rendered_lines:
                    surf_rect = rect.copy()
                    surf_rect.top -= scroll_y
                    screen.blit(surf, surf_rect)

                screen.set_clip(prev_clip)
            else:
                label.draw(screen)

        # Draw buttons
        for button in self.buttons.values():
            button.draw(screen)

        # Draw log text inside log_panel with scroll offset
        log_x = self.log_panel.content_rect.x
        log_y = self.log_panel.content_rect.y
        log_label = Label(
            self.log_text,
            x=log_x,
            y=log_y,
            font=Fonts.SMALL,
            color=Colors.TEXT_DARK,
            max_width=self.log_panel.content_rect.width - PADDING,
        )
        prev_clip = screen.get_clip()
        screen.set_clip(self.log_panel.content_rect)
        for surf, rect in log_label._rendered_lines:
            surf_rect = rect.copy()
            surf_rect.top -= self.log_panel.scroll_y
            screen.blit(surf, surf_rect)
        screen.set_clip(prev_clip)

        # Draw info message if active
        if self.info_msg and self.info_timer > 0:
            info_panel = Panel(
                rect=pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 70, 400, 50),
                bg_color=(50, 50, 60, min(200, self.info_timer * 2)),
                border_color=None,
                corner_radius=CORNER_RADIUS,
            )
            info_panel.draw(screen)

            info_label = Label(
                self.info_msg,
                x=SCREEN_WIDTH // 2,
                y=SCREEN_HEIGHT - 45,
                font=Fonts.NORMAL,
                color=self.info_color,
                align="center",
            )
            info_label.draw(screen)

            self.info_timer -= 1

        pygame.display.flip()

    def run(self) -> None:
        """Main game loop"""
        clock = pygame.time.Clock()

        # Initial UI update
        self.update_ui()

        self.running = True
        while self.running:
            self.handle_events()
            self.draw()
            clock.tick(FRAME_RATE)


# Run the main menu when this file is executed directly
if __name__ == "__main__":
    menu = MainMenu()
    menu.run()
