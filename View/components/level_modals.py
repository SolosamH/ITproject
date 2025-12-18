"""
Level Selection and Game Complete Modals
"""
import pygame
import random
import math
from View.utils import draw_shadow, draw_glass_card, calculate_button_size
from View.components.button import Button


class ConfettiParticle:
    """Single confetti particle for celebration effect"""
    
    def __init__(self, x, y, screen_width, screen_height):
        self.x = x
        self.y = y
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Random properties
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(2, 6)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
        self.size = random.randint(8, 15)
        self.shape = random.choice(['rect', 'circle', 'star'])
        
        # Vibrant colors for confetti
        self.color = random.choice([
            (255, 0, 0),      # Red
            (255, 165, 0),    # Orange
            (255, 255, 0),    # Yellow
            (0, 255, 0),      # Green
            (0, 191, 255),    # Deep Sky Blue
            (138, 43, 226),   # Blue Violet
            (255, 20, 147),   # Deep Pink
            (255, 215, 0),    # Gold
            (0, 255, 255),    # Cyan
            (255, 105, 180),  # Hot Pink
        ])
        
        # Swaying motion
        self.sway_offset = random.uniform(0, math.pi * 2)
        self.sway_amplitude = random.uniform(1, 3)
        self.time = 0
        
    def update(self, dt):
        """Update confetti position"""
        self.time += dt
        
        # Gravity and air resistance
        self.vy += 0.1  # Gravity
        self.vy = min(self.vy, 8)  # Terminal velocity
        
        # Swaying motion
        sway = math.sin(self.time * 5 + self.sway_offset) * self.sway_amplitude
        
        self.x += self.vx + sway
        self.y += self.vy
        self.rotation += self.rotation_speed
        
        # Check if off screen
        return self.y < self.screen_height + 50
        
    def draw(self, surface):
        """Draw confetti particle"""
        if self.shape == 'rect':
            # Rotated rectangle
            rect_surf = pygame.Surface((self.size, self.size // 2), pygame.SRCALPHA)
            rect_surf.fill(self.color)
            rotated = pygame.transform.rotate(rect_surf, self.rotation)
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated, rect)
            
        elif self.shape == 'circle':
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size // 3)
            
        elif self.shape == 'star':
            # Simple star shape
            points = []
            for i in range(5):
                angle = math.radians(self.rotation + i * 72 - 90)
                outer_x = self.x + math.cos(angle) * self.size // 2
                outer_y = self.y + math.sin(angle) * self.size // 2
                points.append((outer_x, outer_y))
                
                inner_angle = math.radians(self.rotation + i * 72 + 36 - 90)
                inner_x = self.x + math.cos(inner_angle) * self.size // 4
                inner_y = self.y + math.sin(inner_angle) * self.size // 4
                points.append((inner_x, inner_y))
            
            if len(points) >= 3:
                pygame.draw.polygon(surface, self.color, points)


class ConfettiSystem:
    """Manages confetti particles for celebration"""
    
    def __init__(self):
        self.particles = []
        self.spawn_timer = 0
        self.active = False
        self.screen_width = 0
        self.screen_height = 0
        
    def start(self, screen_width, screen_height):
        """Start confetti effect"""
        self.active = True
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles = []
        self.spawn_timer = 0
        
        # Initial burst of confetti
        for _ in range(100):
            x = random.randint(0, screen_width)
            y = random.randint(-100, screen_height // 3)
            self.particles.append(ConfettiParticle(x, y, screen_width, screen_height))
            
    def stop(self):
        """Stop spawning new confetti"""
        self.active = False
        
    def clear(self):
        """Clear all confetti"""
        self.particles = []
        self.active = False
        
    def update(self, dt):
        """Update all confetti particles"""
        if not self.active and not self.particles:
            return
            
        # Spawn new confetti while active
        if self.active:
            self.spawn_timer += dt
            if self.spawn_timer >= 0.05:  # Spawn every 50ms
                self.spawn_timer = 0
                for _ in range(3):  # Spawn 3 particles at a time
                    x = random.randint(0, self.screen_width)
                    y = random.randint(-50, 0)
                    self.particles.append(ConfettiParticle(x, y, self.screen_width, self.screen_height))
        
        # Update particles and remove dead ones
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # Limit max particles
        if len(self.particles) > 300:
            self.particles = self.particles[-300:]
            
    def draw(self, surface):
        """Draw all confetti particles"""
        for particle in self.particles:
            particle.draw(surface)


class ModalLevelSelect:
    """Modal for selecting game level"""
    
    def __init__(self, on_level_select):
        self.visible = False
        self.on_level_select = on_level_select
        self.level_buttons = []
        self.unlocked_levels = {1}  # Level 1 always unlocked
        self.coins = 0  # Player's coins
        
    def show(self, unlocked_levels=None, coins=0):
        """Show level select modal"""
        self.visible = True
        self.level_buttons = []  # Reset buttons để tạo lại với unlock state mới
        # Luôn cập nhật unlocked_levels - nếu None thì chỉ level 1
        self.unlocked_levels = unlocked_levels if unlocked_levels is not None else {1}
        self.coins = coins
        
    def hide(self):
        """Hide level select modal"""
        self.visible = False
        
    def draw(self, surface, screen_rect, font_header, font_ui, level_configs):
        """Draw level select modal"""
        if not self.visible:
            return
            
        # Overlay
        overlay = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Panel - larger to show coins
        w, h = 500, 450
        panel = pygame.Rect((screen_rect.w - w) // 2, (screen_rect.h - h) // 2, w, h)
        
        draw_shadow(surface, panel, radius=20, offset=(0, 12), alpha=140)
        draw_glass_card(surface, panel, radius=20, bg=(240, 250, 240, 230), 
                       border=(100, 150, 100), border_alpha=100)
        
        # Title
        title_text = "SELECT LEVEL"
        title = font_header.render(title_text, True, (40, 80, 40))
        title_pos = (panel.centerx - title.get_width() // 2, panel.y + 25)
        surface.blit(title, title_pos)
        
        # Coin display với icon vẽ bằng code
        coin_icon_size = 18
        coin_text = f"Coins: {self.coins}"
        coin_surf = font_ui.render(coin_text, True, (218, 165, 32))
        
        # Tính vị trí để căn giữa
        total_coin_width = coin_icon_size + 6 + coin_surf.get_width()
        coin_start_x = panel.centerx - total_coin_width // 2
        coin_y = panel.y + 70
        
        # Vẽ coin icon (hình tròn vàng)
        coin_icon_center_x = coin_start_x + coin_icon_size // 2
        coin_icon_center_y = coin_y + coin_surf.get_height() // 2
        pygame.draw.circle(surface, (255, 200, 50), (coin_icon_center_x, coin_icon_center_y), coin_icon_size // 2)
        pygame.draw.circle(surface, (218, 165, 32), (coin_icon_center_x, coin_icon_center_y), coin_icon_size // 2, 2)
        # Vẽ chữ $ nhỏ trong coin
        dollar_font = pygame.font.SysFont('Arial', 12, bold=True)
        dollar_text = dollar_font.render('$', True, (139, 90, 0))
        surface.blit(dollar_text, (coin_icon_center_x - dollar_text.get_width() // 2, coin_icon_center_y - dollar_text.get_height() // 2))
        
        # Vẽ text coins
        surface.blit(coin_surf, (coin_start_x + coin_icon_size + 6, coin_y))
        
        # Level buttons
        if not self.level_buttons:
            btn_w, btn_h = 380, 60
            start_y = panel.y + 110
            spacing = 20
            
            for level in [1, 2, 3]:
                config = level_configs[level]
                btn_x = panel.centerx - btn_w // 2
                btn_y = start_y + (level - 1) * (btn_h + spacing)
                
                is_unlocked = level in self.unlocked_levels
                
                # Create level info text
                if is_unlocked:
                    level_text = f"{config['name']} - {config['cols']}x{config['rows']} - {config['time_limit']}s"
                else:
                    level_text = f"🔒 {config['name']} - LOCKED"
                
                btn = Button(
                    (btn_x, btn_y, btn_w, btn_h),
                    level_text,
                    font_ui,
                    lambda l=level: self.select_level(l) if l in self.unlocked_levels else None,
                    theme='green' if level == 1 else ('yellow' if level == 2 else 'orange')
                )
                # Store unlock status
                btn.is_locked = not is_unlocked
                self.level_buttons.append(btn)
        
        # Draw level buttons
        for i, btn in enumerate(self.level_buttons):
            level = i + 1
            is_unlocked = level in self.unlocked_levels
            
            if is_unlocked:
                btn.draw(surface)
            else:
                # Draw locked button with gray overlay
                btn.draw(surface)
                # Add locked overlay
                lock_overlay = pygame.Surface((btn.rect.w, btn.rect.h), pygame.SRCALPHA)
                lock_overlay.fill((50, 50, 50, 150))
                surface.blit(lock_overlay, btn.rect.topleft)
            
    def select_level(self, level):
        """Handle level selection"""
        # Only allow selection if level is unlocked
        if level not in self.unlocked_levels:
            return
        self.hide()
        if self.on_level_select:
            self.on_level_select(level)
            
    def handle_event(self, event):
        """Handle modal events"""
        if not self.visible:
            return
            
        for i, btn in enumerate(self.level_buttons):
            level = i + 1
            # Only handle events for unlocked levels
            if level in self.unlocked_levels:
                btn.handle_event(event)
            
        # Close on ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.hide()


class ModalGameComplete:
    """Modal for game completion with all level stats"""
    
    def __init__(self, on_back_to_menu):
        self.visible = False
        self.on_back_to_menu = on_back_to_menu
        self.level_stats = {}
        self.back_btn = None
        self.confetti = ConfettiSystem()
        self.screen_size = (0, 0)
        
    def show(self, level_stats, screen_width=1200, screen_height=700):
        """Show game complete modal with stats and confetti"""
        self.visible = True
        self.level_stats = level_stats
        self.back_btn = None
        self.screen_size = (screen_width, screen_height)
        # Start confetti celebration!
        self.confetti.start(screen_width, screen_height)
        
    def hide(self):
        """Hide game complete modal"""
        self.visible = False
        self.confetti.stop()
        self.confetti.clear()
        
    def draw(self, surface, screen_rect, font_header, font_ui):
        """Draw game complete modal"""
        if not self.visible:
            return
            
        # Overlay
        overlay = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Panel
        w, h = 550, 500
        panel = pygame.Rect((screen_rect.w - w) // 2, (screen_rect.h - h) // 2, w, h)
        
        draw_shadow(surface, panel, radius=20, offset=(0, 12), alpha=140)
        draw_glass_card(surface, panel, radius=20, bg=(255, 215, 0, 230), 
                       border=(218, 165, 32), border_alpha=120)
        
        # Title with glow
        title_text = "YOU WON THE GAME!"
        title = font_header.render(title_text, True, (139, 69, 19))
        title_glow = font_header.render(title_text, True, (255, 255, 255))
        
        # Draw glow effect
        glow_pos = (panel.centerx - title_glow.get_width() // 2, panel.y + 30)
        for offset_x in [-2, -1, 0, 1, 2]:
            for offset_y in [-2, -1, 0, 1, 2]:
                if offset_x != 0 or offset_y != 0:
                    surface.blit(title_glow, (glow_pos[0] + offset_x, glow_pos[1] + offset_y))
        
        # Main title
        title_pos = (panel.centerx - title.get_width() // 2, panel.y + 30)
        surface.blit(title, title_pos)
        
        # Subtitle
        subtitle = font_ui.render("Congratulations! You completed all levels!", True, (101, 67, 33))
        subtitle_pos = (panel.centerx - subtitle.get_width() // 2, panel.y + 85)
        surface.blit(subtitle, subtitle_pos)
        
        # Stats header
        y_pos = panel.y + 130
        header_font = font_ui
        header_text = header_font.render("Level Statistics", True, (80, 50, 20))
        surface.blit(header_text, (panel.centerx - header_text.get_width() // 2, y_pos))
        
        # Draw separator
        y_pos += 35
        pygame.draw.line(surface, (180, 140, 60), (panel.x + 40, y_pos), (panel.right - 40, y_pos), 2)
        y_pos += 20
        
        # Column headers
        col_x = panel.x + 60
        headers = ["Level", "Time", "Steps"]
        col_widths = [120, 180, 150]
        
        for i, header in enumerate(headers):
            header_surf = font_ui.render(header, True, (60, 40, 10))
            surface.blit(header_surf, (col_x + sum(col_widths[:i]), y_pos))
        
        y_pos += 35
        
        # Draw stats for each level
        stats_color = (80, 50, 20)
        for level in [1, 2, 3]:
            if level in self.level_stats:
                stat = self.level_stats[level]
                level_text = f"Level {level}"
                time_text = stat.get('time', '--:--')
                steps_text = str(stat.get('steps', '--'))
                
                texts = [level_text, time_text, steps_text]
                
                # Draw background for row
                row_bg = pygame.Rect(panel.x + 40, y_pos - 5, panel.w - 80, 35)
                pygame.draw.rect(surface, (255, 235, 180, 150), row_bg, border_radius=8)
                
                for i, text in enumerate(texts):
                    text_surf = font_ui.render(text, True, stats_color)
                    surface.blit(text_surf, (col_x + sum(col_widths[:i]), y_pos))
                
                y_pos += 45
        
        # Back to menu button
        if self.back_btn is None:
            btn_w, btn_h = 200, 50
            btn_x = panel.centerx - btn_w // 2
            btn_y = panel.bottom - btn_h - 30
            
            self.back_btn = Button(
                (btn_x, btn_y, btn_w, btn_h),
                "Back to Menu",
                font_ui,
                self.handle_back,
                theme='green'
            )
        
        self.back_btn.draw(surface)
        
        # Draw confetti on top of everything
        self.confetti.draw(surface)
        
    def update(self, dt):
        """Update confetti animation"""
        if self.visible:
            self.confetti.update(dt)
        
    def handle_back(self):
        """Handle back to menu button"""
        self.hide()
        if self.on_back_to_menu:
            self.on_back_to_menu()
            
    def handle_event(self, event):
        """Handle modal events"""
        if not self.visible:
            return
            
        if self.back_btn:
            self.back_btn.handle_event(event)
