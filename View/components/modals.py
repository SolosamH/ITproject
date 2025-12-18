"""
Modal Components
Modal dialogs for History and Victory screens
"""
import pygame
from View.utils import draw_shadow, draw_glass_card, calculate_button_size
from View.components.button import Button


class ModalHistory:
    """Modal dialog for displaying game history"""
    
    def __init__(self, get_history):
        self.get_history = get_history
        self.visible = False

    def draw(self, surface, screen_rect, font_header, font_row):
        """Draw history modal"""
        if not self.visible:
            return

        # Overlay
        overlay = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Panel
        w = int(screen_rect.w * 0.65)
        h = int(screen_rect.h * 0.65)
        panel = pygame.Rect((screen_rect.w - w) // 2, (screen_rect.h - h) // 2, w, h)
        
        draw_glass_card(surface, panel, radius=18, bg=(250, 250, 250, 235), 
                       border=(60, 60, 60), border_alpha=80)

        # Title
        title = font_header.render("History", True, (20, 20, 20))
        surface.blit(title, (panel.x + 16, panel.y + 12))

        # Headers
        headers = ["#", "Time", "Steps", "Rank", "Mode"]
        col_w = [60, 200, 160, 120, w - 60 - 200 - 160 - 120 - 48]
        x = panel.x + 24
        y = panel.y + 64

        for i, head in enumerate(headers):
            lab = font_row.render(head, True, (60, 60, 60))
            surface.blit(lab, (x, y))
            x += col_w[i]

        # Separator line
        y += 28
        pygame.draw.line(surface, (220, 220, 220), (panel.x + 16, y), (panel.right - 16, y))
        y += 12

        # History rows
        history = self.get_history()
        row_alt = (245, 245, 245)

        for idx, item in enumerate(history, start=1):
            if idx % 2 == 0:
                pygame.draw.rect(surface, row_alt, 
                               pygame.Rect(panel.x + 16, y - 4, panel.w - 32, 26), 
                               border_radius=6)

            x = panel.x + 24
            cols = [
                str(idx),
                item.get("time_str", "--"),
                str(item.get("steps", "--")),
                item.get("rank", "--"),
                item.get("mode", "--")
            ]

            for i, val in enumerate(cols):
                lab = font_row.render(val, True, (40, 40, 40))
                surface.blit(lab, (x, y))
                x += col_w[i]

            y += 26
            if y > panel.bottom - 32:
                break


class ModalVictory:
    """Modal dialog for victory screen"""
    
    def __init__(self, on_restart=None, on_next=None):
        self.visible = False
        self.on_restart = on_restart
        self.on_next = on_next
        self.time_str = ""
        self.steps = 0
        self.restart_btn = None
        self.next_btn = None
        self.win_restart_img = None
        self.is_victory = True  # True for victory, False for defeat
        self.show_next = False  # Show next button for victory

    def show(self, time_str, steps, is_victory=True, show_next=False):
        """Show victory/defeat modal"""
        self.visible = True
        self.time_str = time_str
        self.steps = steps
        self.is_victory = is_victory
        self.show_next = show_next
        self.restart_btn = None
        self.next_btn = None

    def hide(self):
        """Hide victory modal"""
        self.visible = False

    def draw(self, surface, screen_rect, font_header, font_ui):
        """Draw victory modal"""
        if not self.visible:
            return

        # Overlay
        overlay = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Victory panel
        w, h = 400, 280
        panel = pygame.Rect((screen_rect.w - w) // 2, (screen_rect.h - h) // 2, w, h)

        # Theme based on victory/defeat
        if self.is_victory:
            # Golden victory theme
            draw_shadow(surface, panel, radius=20, offset=(0, 12), alpha=140)
            draw_glass_card(surface, panel, radius=20, bg=(255, 215, 0, 220), 
                           border=(218, 165, 32), border_alpha=100)
            title_text = "VICTORY!"
            title_color = (139, 69, 19)
            title_glow_color = (255, 255, 255)
        else:
            # Dark defeat theme
            draw_shadow(surface, panel, radius=20, offset=(0, 12), alpha=140)
            draw_glass_card(surface, panel, radius=20, bg=(60, 60, 80, 220), 
                           border=(100, 40, 40), border_alpha=100)
            title_text = "YOU LOSE!"
            title_color = (180, 50, 50)
            title_glow_color = (255, 100, 100)

        # Title with glow effect
        title = font_header.render(title_text, True, title_color)
        title_glow = font_header.render(title_text, True, title_glow_color)

        # Draw glow effect
        glow_pos = (panel.centerx - title_glow.get_width() // 2, panel.y + 30)
        for offset_x in [-2, -1, 0, 1, 2]:
            for offset_y in [-2, -1, 0, 1, 2]:
                if offset_x != 0 or offset_y != 0:
                    surface.blit(title_glow, (glow_pos[0] + offset_x, glow_pos[1] + offset_y))

        # Main title
        title_pos = (panel.centerx - title.get_width() // 2, panel.y + 30)
        surface.blit(title, title_pos)

        # Stats
        y_pos = panel.y + 100
        stats_color = (101, 67, 33) if self.is_victory else (200, 200, 210)

        time_text = f"Time: {self.time_str}"
        time_surface = font_ui.render(time_text, True, stats_color)
        surface.blit(time_surface, (panel.centerx - time_surface.get_width() // 2, y_pos))

        y_pos += 40
        steps_text = f"Steps: {self.steps}"
        steps_surface = font_ui.render(steps_text, True, stats_color)
        surface.blit(steps_surface, (panel.centerx - steps_surface.get_width() // 2, y_pos))

        # Buttons - show both Retry and Next if victory and show_next is True
        if self.restart_btn is None:
            if self.win_restart_img:
                btn_size = calculate_button_size(self.win_restart_img, target_width=110)
                btn_w, btn_h = btn_size
            else:
                btn_w, btn_h = 140, 45

            if self.is_victory and self.show_next:
                # Show both Retry and Next buttons
                btn_spacing = 20
                total_width = btn_w * 2 + btn_spacing
                btn_x_retry = panel.centerx - total_width // 2
                btn_x_next = btn_x_retry + btn_w + btn_spacing
                btn_y = panel.y + h - btn_h - 15

                self.restart_btn = Button(
                    (btn_x_retry, btn_y, btn_w, btn_h),
                    "Retry",
                    font_ui,
                    self.handle_restart,
                    theme='yellow',
                    bg_image=None,
                    keep_aspect=False
                )
                
                self.next_btn = Button(
                    (btn_x_next, btn_y, btn_w, btn_h),
                    "Next",
                    font_ui,
                    self.handle_next,
                    theme='green',
                    bg_image=None,
                    keep_aspect=False
                )
            else:
                # Show only Retry button (for lose screen - no text, just image)
                btn_x = panel.centerx - btn_w // 2
                btn_y = panel.y + h - btn_h - 15

                self.restart_btn = Button(
                    (btn_x, btn_y, btn_w, btn_h),
                    "",  # Không có text khi lose
                    font_ui,
                    self.handle_restart,
                    theme='green',
                    bg_image=self.win_restart_img,
                    keep_aspect=False
                )

        self.restart_btn.draw(surface)
        if self.next_btn:
            self.next_btn.draw(surface)

    def handle_restart(self):
        """Handle restart button click"""
        self.hide()
        if self.on_restart:
            self.on_restart()
    
    def handle_next(self):
        """Handle next button click"""
        self.hide()
        if self.on_next:
            self.on_next()

    def handle_event(self, event):
        """Handle modal events"""
        if not self.visible:
            return

        if self.restart_btn:
            self.restart_btn.handle_event(event)
        
        if self.next_btn:
            self.next_btn.handle_event(event)

        # Close on ESC or click outside (only for defeat)
        if not self.is_victory:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.hide()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                w, h = 400, 280
                screen_rect = pygame.display.get_surface().get_rect()
                panel = pygame.Rect((screen_rect.w - w) // 2, (screen_rect.h - h) // 2, w, h)
                if not panel.collidepoint(event.pos):
                    self.hide()
