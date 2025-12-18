import os, sys, math, random, pygame, time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Model import GenerationModel, SolvingModel
from View.components import Button, Dropdown, ModalHistory, ModalVictory
from View.components.level_modals import ModalLevelSelect, ModalGameComplete
from View.sprites import FloatingBanana, MonkeyIdle
from View.utils import load_image, draw_shadow, draw_glass_card, draw_smooth_rect, try_load_font, calculate_button_size
from View.particle import ParticleSystem
#from Controller import MazeController


GAME_TITLE = "Monkey's Treasure"
FULLSCREEN = True  # Game khởi động ở chế độ fullscreen
RIGHT_PANEL_W = 420  # Tăng từ 360 lên 420 để có nhiều không gian hơn
FPS = 60
# Performance optimization settings
PERFORMANCE_MODE = False  # Automatically enabled when window is small
MIN_FPS_THRESHOLD = 30    # Switch to performance mode if FPS drops below this
PERFORMANCE_FPS = 30      # Reduced FPS in performance mode
MIN_CELL_SIZE_FOR_DETAILS = 12  # Don't draw detailed elements if cells are smaller
GENERATOR = "None" # DFS, Kruskal, Binary Tree, Wilson, Recursive Division
MODE = None  # Easy, Medium, Hard
MAZE_COLS, MAZE_ROWS = 25, 19
CELL_GAP = 0  # khít nhau

# Level system configuration
LEVEL_CONFIGS = {
    1: {
        'name': 'Level 1',
        'cols': 13,  # 25 - 12 (6 ô mỗi bên)
        'rows': 7,   # 19 - 12 (6 ô mỗi bên)
        'time_limit': 30,   # 30 giây
        'extra_steps': 10,  # Dư 10 bước
    },
    2: {
        'name': 'Level 2',
        'cols': 19,  # 25 - 6 (3 ô mỗi bên)
        'rows': 13,  # 19 - 6 (3 ô mỗi bên)
        'time_limit': 90,   # 1 phút 30 giây
        'extra_steps': 5,   # Dư 5 bước
    },
    3: {
        'name': 'Level 3',
        'cols': 25,  # Kích thước đầy đủ
        'rows': 19,
        'time_limit': 75,   # 1 phút 15 giây
        'extra_steps': 3,   # Dư 3 bước
    }
}

ASSETS = os.path.join(os.path.dirname(__file__), "assets")
IMG = lambda name: os.path.join(ASSETS, name)

PALETTES = {
    'neutral': ((20,28,20), (28,36,28), (60,80,60)),
    'green'  : ((32,64,44), (48,104,74), (84,140,110)),
    'yellow' : ((88,72,24), (130,110,36), (170,140,50)),
    'orange' : ((120,64,30), (170,96,48), (210,130,70)),
    'blue'   : ((34,54,86),  (48,86,138), (72,118,170)),
    'purple' : ((52,34,86),  (88,58,140), (120,90,168)),
    'red'    : ((92,38,38),  (138,54,54), (170,84,84)),
}

# ---------- App ----------
class App:
    def __init__(self):
        self.cell_size = None
        self.maze_rect = None
        pygame.init()
        flags = pygame.FULLSCREEN if FULLSCREEN else 0
        self.screen = pygame.display.set_mode((0, 0) if FULLSCREEN else (1024, 768), flags)
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.window_rect = self.screen.get_rect()
        self.running = True

        # Performance optimization - Cache system
        self._image_cache = {}
        self._surface_cache = {}
        self._last_cell_size = None
        self._bg_cache = {}

        # Performance monitoring and optimization
        self.fps_samples = []
        self.current_fps = FPS
        self.performance_mode = PERFORMANCE_MODE
        self.frame_skip_counter = 0
        self.dirty_regions = []
        self.last_draw_time = 0
        self.skip_expensive_effects = False

        # Precomputed maze surface for small sizes
        self._maze_surface = None
        self._maze_surface_dirty = True
        self._ui_surface = None
        self._ui_surface_dirty = True

        # assets
        self.bg_jungle = load_image(IMG("bg_jungle.png"))
        self.bg_start = load_image(IMG("bg_start.png"))
        self.tile_wall = load_image(IMG("tile_wall.png"))
        self.monkey_img = load_image(IMG("monkey.png"))
        self.banana_img = load_image(IMG("banana_rainbow.png"))

        # button assets
        self.btn_assets = {
            'start': load_image(IMG("button/start_btn.png")),
            'restart': load_image(IMG("button/restart_btn.png")),
            'close': load_image(IMG("button/close_btn.png")),
            'exit': load_image(IMG("button/exit_btn.png")),
            'minimize': load_image(IMG("button/minimize_btn.png")),
            'back': load_image(IMG("button/back_btn.png")),
            'history': load_image(IMG("button/history_btn.png")),
            'auto': load_image(IMG("button/auto_btn.png")),
            'small': load_image(IMG("button/small_btn.png")),
            'win_restart': load_image(IMG("button/win_restart_btn.png"))
        }

        # box assets - UI boxes cho time, steps, algorithm
        self.box_assets = {
            'time': load_image(IMG("box/time_box.png")),
            'step': load_image(IMG("box/step_box.png")),
            'algorithm': load_image(IMG("box/algorithm_box.png")),
            'algorithm_choice': load_image(IMG("box/algorithm_choice_box.png")),
            'menu': load_image(IMG("box/menu_box.png"))
        }

        # floor tiles
        self.floor_tiles = []
        tiles_dir = os.path.join(ASSETS, "tiles")
        for name in sorted(os.listdir(tiles_dir)):
            if name.lower().endswith(".png"):
                self.floor_tiles.append(load_image(os.path.join(tiles_dir, name)))

        # fonts
        self.font_title = try_load_font(64)
        self.font_ui = try_load_font(26)
        self.font_small = try_load_font(20)
        self.font_chip = try_load_font(28)  # Font lớn hơn cho time/step boxes (jungle theme)

        # state
        self.state = "start"
        self.paused = False
        self.auto_on = False
        self.selected_algo = None
        self.steps = 0
        self.timer = 0.0
        self.start_time = None
        self.history = []
        self.game_won = False
        
        # Game difficulty and time limit
        self.difficulty = "Medium"  # Easy, Medium, Hard
        self.time_limits = {"Easy": 180, "Medium": 120, "Hard": 60}
        self.time_limit = self.time_limits[self.difficulty]
        self.time_remaining = self.time_limit
        
        # Collectibles (small bananas)
        self.collectibles = []  # List of (x, y) positions
        self.collected_count = 0
        self.total_collectibles = 0
        self.collectible_points = 10  # Points per collectible
        
        # Steps system (optimal path based)
        self.steps = 0  # Current steps taken
        self.max_steps = 0  # Maximum allowed steps (optimal + 3)
        self.steps_remaining = 0  # Steps left
        
        # Level system
        self.current_level = 1
        self.max_level = 3
        self.level_stats = {}  # Store stats for each level {level: {'time': str, 'steps': int, 'completed': bool}}
        self.showing_level_select = False
        self.showing_game_complete = False
        self.unlocked_levels = {1}  # Only level 1 is unlocked initially
        
        # Coin system
        self.coins = 0  # Current coins
        self.auto_use_count = 0  # Number of times auto has been used
        self.coin_reward_ratio = 0.6  # Earn coin if time_remaining > time_limit * 0.6
        
        # Transition effect system
        self.transitioning = False
        self.transition_progress = 0.0
        self.transition_duration = 1.2  # seconds - 2 pha (shrink + expand)
        self.transition_from = None
        self.transition_to = None
        self.transition_surface_from = None
        self.transition_surface_to = None
        
        self.modal_history = ModalHistory(lambda: self.history)
        self.modal_victory = ModalVictory(self.restart_level, self.next_level)
        self.modal_victory.win_restart_img = self.btn_assets['win_restart']
        self.modal_level_select = ModalLevelSelect(self.start_level)
        self.modal_game_complete = ModalGameComplete(self.back_to_menu)
        
        # Cached small banana image
        self.small_banana_cache = None
        self.small_banana_size_cache = 0
        
        # Cached glow and rotation surfaces for bananas (performance optimization)
        self.banana_glow_cache = []  # List of pre-rendered glow surfaces
        self.banana_rotation_cache = {}  # Dict of angle -> rotated surface
        self.banana_last_cache_size = 0
        
        # Maze generation animation
        self.generating_maze = False
        self.generation_model = None
        self.generation_timer = 0.0
        self.generation_speed = 0.001  # Seconds per step (tối ưu: 0.001 để nhanh và mượt hơn)
        
        # Auto solve animation
        self.solving_maze = False
        self.solving_model = None
        self.solution_path = []
        self.solution_index = 0
        self.solve_speed = 0.15  # Seconds per step
        self.solve_timer = 0.0
        
        # Particle effects for wall breaking
        self.particle_system = ParticleSystem()
        self.last_broken_cells = []  # Track recently broken cells for particle emission

        # Lưu kích thước windowed và trạng thái fullscreen
        self.windowed_size = (1024, 768)  # Kích thước khi không full màn hình
        self.is_fullscreen = FULLSCREEN  # Ban đầu là full màn hình
        self.is_minimized = False  # Trạng thái thu nhỏ

        # Window dragging state
        self.dragging = False
        self.drag_offset = (0, 0)

        # Continuous movement state - cho phép giữ phím để di chuyển liên tục
        self.key_hold_timer = 0
        self.key_hold_delay = 0.15  # Delay giữa các bước di chuyển (seconds)
        self.last_move_time = 0

        # Window controls - 3 nút ở góc trên phải
        btn_size = 48  # Kích thước nút - tăng lên
        btn_y = 10     # Vị trí Y - dời lên cao hơn
        btn_gap = 8    # Khoảng cách giữa các nút

        # Tính vị trí từ phải sang trái (Exit -> Maximize -> Minimize)
        x_exit = self.window_rect.w - 10 - btn_size
        x_maximize = x_exit - btn_gap - btn_size
        x_minimize = x_maximize - btn_gap - btn_size

        # Tạo 3 nút mới với assets đúng
        # Nút trái: Hide (ẩn cửa sổ)
        self.btn_min = Button(
            (x_minimize, btn_y, btn_size, btn_size),
            "", self.font_small, self.hide_window,
            theme='yellow',
            bg_image=self.btn_assets['minimize'],
            keep_aspect=False
        )

        # Nút giữa: Minimize (thu nhỏ cửa sổ)
        self.btn_max = Button(
            (x_maximize, btn_y, btn_size, btn_size),
            "", self.font_small, self.shrink_window,
            theme='blue',
            bg_image=self.btn_assets['small'],
            keep_aspect=False
        )

        self.btn_close = Button(
            (x_exit, btn_y, btn_size, btn_size),
            "", self.font_small, self.quit,
            theme='red',
            bg_image=self.btn_assets['close'],  # Dùng close_btn thay vì exit_btn
            keep_aspect=False
        )

        # start screen - tăng kích thước nút start
        start_size = calculate_button_size(self.btn_assets['start'], target_width=320)  # Tăng từ 240 lên 320
        self.btn_start = Button((0, 0, start_size[0], start_size[1]), "", self.font_ui, self.goto_game, theme='green', bg_image=self.btn_assets['start'], keep_aspect=False)

        # game UI
        self.compute_layout()

        # Tính toán vị trí sidebar và margin
        sidebar_left = self.window_rect.w - RIGHT_PANEL_W
        margin = 25  # Margin từ mép sidebar
        cur_y = 120  # Vị trí Y bắt đầu (tránh window controls)

        # Tính toán sidebar card thực tế (giống như trong draw_game)
        # sidebar card có margin 10px từ mép và width nhỏ hơn 20px
        sidebar_card_x = sidebar_left + 10  # +10px margin
        sidebar_card_w = RIGHT_PANEL_W - 20  # -20px margin (10px mỗi bên)

        # Chiều rộng các nút - giảm margin để nút lớn hơn
        side_margin = 10  # Margin rất nhỏ để nút tối đa hóa kích thước
        target_btn_w = sidebar_card_w - (side_margin * 2)  # Chiều rộng tối đa
        max_btn_h = 110  # Chiều cao tối đa (tăng từ 90 lên 110)
        row_spacing = 10  # Khoảng cách giữa các dòng

        # Vị trí X bắt đầu (căn giữa trong sidebar)
        spx = sidebar_left + side_margin

        # Helper function để tính kích thước nút với giới hạn chiều cao
        def get_button_size(asset, target_width, max_height=max_btn_h):
            size = calculate_button_size(asset, target_width=target_width)
            if size[1] > max_height:
                # Nếu cao quá, scale lại dựa trên chiều cao tối đa
                size = calculate_button_size(asset, target_height=max_height)
            return size

        # Tính kích thước nút giữ nguyên aspect ratio từ asset
        restart_size = get_button_size(self.btn_assets['restart'], target_btn_w)
        auto_size = get_button_size(self.btn_assets['auto'], target_btn_w)
        half_btn_w = (target_btn_w - 8) // 2
        play_size = get_button_size(self.btn_assets['small'], half_btn_w)
        history_size = get_button_size(self.btn_assets['history'], target_btn_w)
        back_size = get_button_size(self.btn_assets['back'], target_btn_w)

        # Dòng 1: Restart button (căn giữa trong sidebar card)
        restart_x = sidebar_card_x + (sidebar_card_w - restart_size[0]) // 2
        self.btn_restart = Button((restart_x, cur_y, restart_size[0], restart_size[1]), "", self.font_ui, 
                                  self.restart_level, theme='orange', 
                                  bg_image=self.btn_assets['restart'], keep_aspect=True)
        cur_y += restart_size[1] + row_spacing

        # Dòng 2: Auto button (căn giữa trong sidebar card)
        auto_x = sidebar_card_x + (sidebar_card_w - auto_size[0]) // 2
        self.btn_auto = Button((auto_x, cur_y, auto_size[0], auto_size[1]), "", self.font_ui, 
                              self.toggle_auto, theme='blue', 
                              bg_image=self.btn_assets['auto'], keep_aspect=True)
        cur_y += auto_size[1] + row_spacing

        # Dòng 3: Play và Pause (2 nút căn giữa trong sidebar card)
        total_play_width = play_size[0] * 2 + 8  # Tổng chiều rộng 2 nút + khoảng cách
        play_start_x = sidebar_card_x + (sidebar_card_w - total_play_width) // 2
        self.btn_play = Button((play_start_x, cur_y, play_size[0], play_size[1]), "", self.font_ui, 
                              self.toggle_play, theme='green', 
                              bg_image=self.btn_assets['small'], keep_aspect=True)
        self.btn_pause = Button((play_start_x + play_size[0] + 8, cur_y, play_size[0], play_size[1]), "", 
                               self.font_ui, self.toggle_play, theme='yellow', 
                               bg_image=self.btn_assets['small'], keep_aspect=True)
        cur_y += play_size[1] + row_spacing + 5

        # Dòng 4: History button (căn giữa trong sidebar card)
        history_x = sidebar_card_x + (sidebar_card_w - history_size[0]) // 2
        self.btn_history = Button((history_x, cur_y, history_size[0], history_size[1]), "", self.font_ui, 
                                 self.open_history, theme='purple', 
                                 bg_image=self.btn_assets['history'], keep_aspect=True)
        cur_y += history_size[1] + row_spacing

        # Dòng 5: Back button (căn giữa trong sidebar card)
        back_x = sidebar_card_x + (sidebar_card_w - back_size[0]) // 2
        self.btn_back = Button((back_x, cur_y, back_size[0], back_size[1]), "", self.font_ui, 
                              self.goto_start, theme='red', 
                              bg_image=self.btn_assets['back'], keep_aspect=True)

        # maze - use level 1 config for initial setup
        level_config = LEVEL_CONFIGS[1]
        self.MazeGenerated = GenerationModel(level_config['cols'], level_config['rows'], GENERATOR).generate_maze()
        self.maze = self.MazeGenerated
        self.player = [1,1]  # Khởi tạo từ (1,1) thay vì (0,0)
        self.prepare_sprites()

        # prebuild random floor map for repeatability
        random.seed(42)
        self.floor_map = [[random.randrange(len(self.floor_tiles)) for _ in range(level_config['cols'])] for _ in range(level_config['rows'])]

        # Cập nhật scale các nút game ngay sau khi khởi tạo
        self.update_game_buttons()

    def prepare_sprites(self):
        cell = self.cell_size
        # Clear cache if cell size changed
        if self._last_cell_size != cell:
            self.clear_size_dependent_cache()
            self._last_cell_size = cell
            # Reset small banana cache when cell size changes
            self.small_banana_cache = None
            self.small_banana_size_cache = 0

        def scale_to_cell(img, ratio=0.9):
            w = h = int(cell*ratio)
            return self.get_scaled_image(img, (w,h))

        # Pre-scale and cache all floor tiles for current cell size
        self.scaled_floor_tiles = []
        for tile in self.floor_tiles:
            self.scaled_floor_tiles.append(self.get_scaled_image(tile, (cell, cell)))

        # Pre-scale wall tile
        self.scaled_wall_tile = self.get_scaled_image(self.tile_wall, (cell, cell))

        # idle frames
        stand_dir = os.path.join(ASSETS, "monkey_stand")
        frames = []
        if os.path.exists(stand_dir):
            for name in sorted(os.listdir(stand_dir)):
                if name.lower().endswith((".png",".jpg",".jpeg")):
                    frames.append(scale_to_cell(load_image(os.path.join(stand_dir, name))))
        self.monkey_idle = MonkeyIdle(frames, scale_to_cell(self.monkey_img), self.cell_size)
        self.banana = FloatingBanana(scale_to_cell(self.banana_img, 0.85), self.cell_size)

    # ---- Window controls
    def update_window_controls(self):
        """Cập nhật vị trí window controls khi cửa sổ thay đổi kích thước"""
        btn_size = 48  # Tăng kích thước nút
        btn_y = 10  # Vị trí Y - cao hơn
        btn_gap = 8

        x_exit = self.window_rect.w - 10 - btn_size
        x_maximize = x_exit - btn_gap - btn_size
        x_minimize = x_maximize - btn_gap - btn_size

        self.btn_min.rect = pygame.Rect(x_minimize, btn_y, btn_size, btn_size)
        self.btn_max.rect = pygame.Rect(x_maximize, btn_y, btn_size, btn_size)
        self.btn_close.rect = pygame.Rect(x_exit, btn_y, btn_size, btn_size)

        # Re-scale background images
        if self.btn_min.bg_image:
            self.btn_min.scaled_bg = pygame.transform.smoothscale(self.btn_min.bg_image, (btn_size, btn_size))
        if self.btn_max.bg_image:
            self.btn_max.scaled_bg = pygame.transform.smoothscale(self.btn_max.bg_image, (btn_size, btn_size))
        if self.btn_close.bg_image:
            self.btn_close.scaled_bg = pygame.transform.smoothscale(self.btn_close.bg_image, (btn_size, btn_size))

    def update_game_buttons(self):
        """Cập nhật kích thước và vị trí các nút game khi cửa sổ thay đổi"""
        # Scale sidebar width theo tỷ lệ cửa sổ
        scale_factor = min(self.window_rect.w / 1920, self.window_rect.h / 1080)
        scale_factor = max(0.5, min(1.5, scale_factor))  # Tăng max từ 1.2 lên 1.5 để cho phép to hơn nữa

        scaled_panel_w = int(RIGHT_PANEL_W * scale_factor)
        scaled_panel_w = max(180, min(scaled_panel_w, 650))  # Giảm tối thiểu từ 240 xuống 180px

        # Tính toán vị trí sidebar và margin
        sidebar_left = self.window_rect.w - scaled_panel_w
        
        # Tính toán sidebar card thực tế (giống như trong draw_game)
        sidebar_card_margin = int(10 * scale_factor)  # Margin của sidebar card
        sidebar_card_margin = max(2, sidebar_card_margin)  # Giảm margin xuống 2px khi màn hình nhỏ
        sidebar_card_x = sidebar_left + sidebar_card_margin
        sidebar_card_w = scaled_panel_w - (sidebar_card_margin * 2)
        
        side_margin = int(8 * scale_factor)  # Margin các nút trong sidebar  
        side_margin = max(2, side_margin)  # Giảm margin tối thiểu xuống 2px khi màn hình rất nhỏ
        
        # Tính chiều cao sidebar có sẵn
        sidebar_height = self.window_rect.h - 70  # Chiều cao sidebar
        
        # Vị trí bắt đầu các nút - điều chỉnh theo chiều cao màn hình
        cur_y_start = max(80, int(120 * scale_factor))  # Giảm xuống 80px khi màn hình nhỏ
        
        # Ước tính chiều cao time/step boxes
        estimated_chip_h = max(40, int(100 * scale_factor))
        estimated_chip_h = min(estimated_chip_h, 120)
        
        # Chiều cao khả dụng cho các nút (trừ đi time/step boxes và margins)
        available_height = sidebar_height - cur_y_start - estimated_chip_h - 40  # 40px buffer
        
        cur_y = cur_y_start

        # Chiều rộng các nút - KHÔNG VƯỢT QUÁ sidebar card
        target_btn_w = sidebar_card_w - (side_margin * 2)
        target_btn_w = max(80, min(target_btn_w, sidebar_card_w - 6))  # Giảm từ 100 xuống 80px, margin 6px
        
        # Chiều cao điều chỉnh theo kích thước màn hình - THU NHỎ KHI MÀN HÌNH NHỎ
        target_btn_h = int(120 * scale_factor)  
        target_btn_h = max(30, min(target_btn_h, 130))  # Giảm tối thiểu từ 40 xuống 30px
        
        # Tính tổng chiều cao cần thiết cho các nút
        # 4 nút: restart + auto + history + back
        total_elements_height = target_btn_h * 4
        
        # Tính spacing cần thiết
        num_spaces = 3  # Số khoảng cách giữa 4 nút
        min_spacing = 3  # Spacing tối thiểu
        desired_spacing = max(4, int(12 * scale_factor))  # Spacing mong muốn: 4-12px
        
        # Thử với spacing mong muốn trước
        required_height_desired = total_elements_height + (num_spaces * desired_spacing)
        required_height_min = total_elements_height + (num_spaces * min_spacing)
        
        if required_height_desired <= available_height:
            # Đủ chỗ với spacing lớn
            row_spacing = desired_spacing
        elif required_height_min <= available_height:
            # Đủ chỗ với spacing vừa phải, tính toán spacing chính xác
            row_spacing = int((available_height - total_elements_height) / num_spaces)
            row_spacing = max(min_spacing, min(row_spacing, desired_spacing))
        else:
            # Không đủ chỗ, giảm chiều cao nút để có spacing tối thiểu
            available_for_elements = available_height - (num_spaces * min_spacing)
            reduction_ratio = available_for_elements / total_elements_height
            
            target_btn_h = int(target_btn_h * reduction_ratio * 0.95)  # 0.95 để có buffer
            target_btn_h = max(22, target_btn_h)  # Tối thiểu 22px
            
            row_spacing = min_spacing  # Dùng spacing tối thiểu

        # Tính kích thước riêng cho từng nút trước
        restart_size_temp = calculate_button_size(self.btn_assets['restart'], target_height=target_btn_h)
        auto_size_temp = calculate_button_size(self.btn_assets['auto'], target_height=target_btn_h)
        
        # Lấy chiều rộng lớn nhất nhưng KHÔNG ĐƯỢC vượt quá target_btn_w
        max_width = max(restart_size_temp[0], auto_size_temp[0])
        max_width = min(max_width, target_btn_w)  # Bắt buộc không vượt quá sidebar
        
        # Nếu nút vẫn quá rộng, giảm chiều cao để giảm chiều rộng (giữ tỷ lệ)
        if max_width > target_btn_w:
            # Tính lại chiều cao để chiều rộng vừa khít
            ratio = restart_size_temp[0] / restart_size_temp[1] if restart_size_temp[1] > 0 else 1
            target_btn_h = int(target_btn_w / ratio)
            target_btn_h = max(25, target_btn_h)  # Tối thiểu 25px
            restart_size_temp = calculate_button_size(self.btn_assets['restart'], target_height=target_btn_h)
            auto_size_temp = calculate_button_size(self.btn_assets['auto'], target_height=target_btn_h)
            max_width = min(max(restart_size_temp[0], auto_size_temp[0]), target_btn_w)
        
        restart_size = (max_width, target_btn_h)
        auto_size = (max_width, target_btn_h)
        
        # History và back buttons - giới hạn kích thước CHẶT CHẼ
        history_size_temp = calculate_button_size(self.btn_assets['history'], target_height=target_btn_h)
        history_width = min(history_size_temp[0], target_btn_w)
        
        # Nếu vẫn quá rộng, tính lại chiều cao
        if history_size_temp[0] > target_btn_w:
            ratio = history_size_temp[0] / history_size_temp[1] if history_size_temp[1] > 0 else 1
            new_h = int(target_btn_w / ratio)
            new_h = max(25, new_h)
            history_size_temp = calculate_button_size(self.btn_assets['history'], target_height=new_h)
            history_width = min(history_size_temp[0], target_btn_w)
            history_size = (history_width, new_h)
        else:
            history_size = (history_width, target_btn_h)
        
        back_size_temp = calculate_button_size(self.btn_assets['back'], target_height=target_btn_h)
        back_width = min(back_size_temp[0], target_btn_w)
        
        # Nếu vẫn quá rộng, tính lại chiều cao
        if back_size_temp[0] > target_btn_w:
            ratio = back_size_temp[0] / back_size_temp[1] if back_size_temp[1] > 0 else 1
            new_h = int(target_btn_w / ratio)
            new_h = max(25, new_h)
            back_size_temp = calculate_button_size(self.btn_assets['back'], target_height=new_h)
            back_width = min(back_size_temp[0], target_btn_w)
            back_size = (back_width, new_h)
        else:
            back_size = (back_width, target_btn_h)

        # Dòng 1: Restart button (căn giữa trong sidebar card)
        restart_x = sidebar_card_x + (sidebar_card_w - restart_size[0]) // 2
        restart_x = max(sidebar_card_x + side_margin, restart_x)  # Đảm bảo không tràn trái
        # Đảm bảo không tràn phải
        if restart_x + restart_size[0] > sidebar_card_x + sidebar_card_w - side_margin:
            restart_x = sidebar_card_x + sidebar_card_w - side_margin - restart_size[0]
        self.btn_restart.rect = pygame.Rect(restart_x, cur_y, restart_size[0], restart_size[1])
        if self.btn_restart.bg_image:
            self.btn_restart.scaled_bg = pygame.transform.smoothscale(
                self.btn_restart.bg_image, restart_size)
        cur_y += restart_size[1] + row_spacing

        # Dòng 2: Auto button (căn giữa trong sidebar card)
        auto_x = sidebar_card_x + (sidebar_card_w - auto_size[0]) // 2
        auto_x = max(sidebar_card_x + side_margin, auto_x)  # Đảm bảo không tràn trái
        # Đảm bảo không tràn phải
        if auto_x + auto_size[0] > sidebar_card_x + sidebar_card_w - side_margin:
            auto_x = sidebar_card_x + sidebar_card_w - side_margin - auto_size[0]
        self.btn_auto.rect = pygame.Rect(auto_x, cur_y, auto_size[0], auto_size[1])
        if self.btn_auto.bg_image:
            self.btn_auto.scaled_bg = pygame.transform.smoothscale(
                self.btn_auto.bg_image, auto_size)
        cur_y += auto_size[1] + row_spacing

        # Dòng 3: History button (căn giữa trong sidebar card)
        history_x = sidebar_card_x + (sidebar_card_w - history_size[0]) // 2
        history_x = max(sidebar_card_x + side_margin, history_x)  # Đảm bảo không tràn trái
        # Đảm bảo không tràn phải
        if history_x + history_size[0] > sidebar_card_x + sidebar_card_w - side_margin:
            history_x = sidebar_card_x + sidebar_card_w - side_margin - history_size[0]
        self.btn_history.rect = pygame.Rect(history_x, cur_y, history_size[0], history_size[1])
        if self.btn_history.bg_image:
            self.btn_history.scaled_bg = pygame.transform.smoothscale(
                self.btn_history.bg_image, history_size)
        cur_y += history_size[1] + row_spacing

        # Dòng 4: Back button (căn giữa trong sidebar card)
        back_x = sidebar_card_x + (sidebar_card_w - back_size[0]) // 2
        back_x = max(sidebar_card_x + side_margin, back_x)  # Đảm bảo không tràn trái
        # Đảm bảo không tràn phải
        if back_x + back_size[0] > sidebar_card_x + sidebar_card_w - side_margin:
            back_x = sidebar_card_x + sidebar_card_w - side_margin - back_size[0]
        self.btn_back.rect = pygame.Rect(back_x, cur_y, back_size[0], back_size[1])
        if self.btn_back.bg_image:
            self.btn_back.scaled_bg = pygame.transform.smoothscale(
                self.btn_back.bg_image, back_size)

    def hide_window(self):
        """Ẩn cửa sổ xuống taskbar (iconify)"""
        try:
            pygame.display.iconify()
        except:
            pass

    def shrink_window(self):
        """Thu nhỏ cửa sổ về 70% màn hình (giữ tỷ lệ) hoặc phóng to lại fullscreen"""
        global FULLSCREEN

        if self.is_minimized:
            # Đang ở trạng thái thu nhỏ -> phóng to về fullscreen
            FULLSCREEN = True
            self.is_fullscreen = True
            self.is_minimized = False
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            # Đang fullscreen -> thu nhỏ về 70% màn hình (giữ tỷ lệ)
            FULLSCREEN = False
            self.is_fullscreen = False
            self.is_minimized = True

            # Lấy kích thước màn hình sử dụng pygame (cross-platform)
            display_info = pygame.display.Info()
            screen_width = display_info.current_w
            screen_height = display_info.current_h

            # Tính 70% kích thước màn hình nhưng giữ tỷ lệ khung hình
            target_width = int(screen_width * 0.7)
            target_height = int(screen_height * 0.7)

            # Giữ tỷ lệ khung hình của màn hình gốc
            screen_ratio = screen_width / screen_height

            # Tính kích thước cửa sổ giữ nguyên tỷ lệ
            if target_width / target_height > screen_ratio:
                # Giới hạn bởi chiều cao
                window_height = target_height
                window_width = int(window_height * screen_ratio)
            else:
                # Giới hạn bởi chiều rộng
                window_width = target_width
                window_height = int(window_width / screen_ratio)

            # Đảm bảo kích thước tối thiểu
            window_width = max(640, window_width)
            window_height = max(480, window_height)

            # Căn giữa cửa sổ trước khi tạo
            self.center_window(window_width, window_height)

            # Tạo cửa sổ mới với kích thước đã tính
            pygame.display.set_mode((window_width, window_height))

        # Cập nhật sau khi thay đổi kích thước
        self.screen = pygame.display.get_surface()
        self.window_rect = self.screen.get_rect()
        self.compute_layout()
        self.update_window_controls()
        self.prepare_sprites()

    def center_window(self, width, height):
        """Đặt cửa sổ ở giữa màn hình - cross-platform version"""
        try:
            # Lấy kích thước màn hình sử dụng pygame
            display_info = pygame.display.Info()
            screen_width = display_info.current_w
            screen_height = display_info.current_h

            # Tính vị trí căn giữa
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2

            # Đặt vị trí cửa sổ sử dụng environment variable (cross-platform)
            import os
            os.environ['SDL_WINDOW_POS'] = f'{x},{y}'

        except Exception as e:
            # Nếu không thể căn giữa, để pygame tự xử lý
            pass

    def toggle_fullscreen(self):
        global FULLSCREEN
        FULLSCREEN = not FULLSCREEN
        if FULLSCREEN:
            pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        else:
            pygame.display.set_mode((1024,768))
        self.screen = pygame.display.get_surface()
        self.window_rect = self.screen.get_rect()
        self.compute_layout()
        self.update_window_controls()  # Cập nhật vị trí window controls
        self.prepare_sprites()  # Cập nhật sprites với cell size mới

    def quit(self):
        self.running = False

    # ---- Layout
    def compute_layout(self):
        screen = self.window_rect

        # Scale sidebar width theo tỷ lệ cửa sổ
        scale_factor = min(screen.w / 1920, screen.h / 1080)
        scale_factor = max(0.5, min(1.5, scale_factor))  # Tăng max từ 1.2 lên 1.5 để cho phép to hơn nữa
        scaled_panel_w = int(RIGHT_PANEL_W * scale_factor)
        scaled_panel_w = max(180, min(scaled_panel_w, 650))  # Giảm tối thiểu từ 200 xuống 180px
        
        # Đảm bảo sidebar không quá lớn so với màn hình
        max_sidebar_ratio = 0.35  # Sidebar không chiếm quá 35% màn hình
        scaled_panel_w = min(scaled_panel_w, int(screen.w * max_sidebar_ratio))

        # Get current level config
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']

        left_space = screen.w - scaled_panel_w
        margin = max(12, int(24 * scale_factor))
        avail_w = left_space - margin*2
        avail_h = screen.h - margin*2
        
        # Calculate cell size to fit the available space (zoom smaller mazes)
        cell_w = avail_w // maze_cols
        cell_h = avail_h // maze_rows
        self.cell_size = min(cell_w, cell_h)
        
        # Calculate actual maze size
        maze_w = self.cell_size * maze_cols
        maze_h = self.cell_size * maze_rows
        self.maze_rect = pygame.Rect((left_space - maze_w)//2 + margin, (screen.h-maze_h)//2, maze_w, maze_h)

        # Cập nhật lại kích thước và vị trí các nút game (chỉ khi đã khởi tạo)
        if hasattr(self, 'btn_restart'):
            self.update_game_buttons()

    # ---- State transitions
    def goto_start(self):
        self.save_run(label="Manual" if not self.auto_on else f"Auto ({self.selected_algo or 'None'})")
        self.start_transition("game", "start")

    def goto_game(self):
        # Show level select instead of going directly to game
        self.showing_level_select = True
        self.modal_level_select.show(self.unlocked_levels, self.coins)
    
    def start_level(self, level):
        """Start a specific level"""
        # Check if level is unlocked
        if level not in self.unlocked_levels:
            return
        self.current_level = level
        self.showing_level_select = False
        # Reset auto use count for each level
        self.auto_use_count = 0
        # Prepare maze synchronously first (for transition to work)
        self.prepare_maze_for_level()
        # Then start transition with animation
        self.start_transition("start", "game")
    
    def prepare_maze_for_level(self):
        """Prepare maze synchronously without animation (for transition)"""
        import random
        
        # Get current level config
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']
        
        # Chọn thuật toán ngẫu nhiên
        generation_algos = ["DFS", "Kruskal", "Binary_Tree", "Wilson", "Recursive_Division"]
        self.selected_generation_algo = random.choice(generation_algos)
        
        # Tạo model KHÔNG có animation
        self.generation_model = GenerationModel(maze_cols, maze_rows, self.selected_generation_algo)
        self.generation_model.animated_generation = False  # No animation for transition
        
        # Generate maze hoàn chỉnh
        self.generation_model.generate_maze()
        
        # Copy maze hoàn chỉnh
        self.maze = self.generation_model.Maze
        self.MazeGenerated = self.generation_model.Maze
        
        # Rebuild floor map với kích thước đúng của level mới
        import random as rand
        rand.seed(42)
        self.floor_map = [[rand.randrange(len(self.floor_tiles)) for _ in range(maze_cols)] for _ in range(maze_rows)]
        
        # Recompute layout for new level size
        self.compute_layout()
        
        # Prepare sprites
        self.prepare_sprites()
    
    def next_level(self):
        """Move to next level"""
        if self.current_level < self.max_level:
            self.current_level += 1
            # Generate new maze with correct size for the new level before reset
            self.generate_maze()
        else:
            # All levels completed - show game complete modal
            self.showing_game_complete = True
            self.modal_game_complete.show(self.level_stats, self.window_rect.w, self.window_rect.h)
    
    def back_to_menu(self):
        """Go back to start menu and reset game"""
        self.showing_game_complete = False
        self.current_level = 1
        self.level_stats = {}
        # Reset coin system and unlocked levels
        self.coins = 0
        self.auto_use_count = 0
        self.unlocked_levels = {1}
        self.goto_start()
    
    def start_transition(self, from_state, to_state):
        """Bắt đầu hiệu ứng chuyển cảnh circle 2 pha"""
        self.transitioning = True
        self.transition_progress = 0.0
        self.transition_from = from_state
        self.transition_to = to_state
        
        # Capture current screen
        self.transition_surface_from = self.screen.copy()
        
        # Prepare target state (but don't change state yet)
        if to_state == "game":
            # Pre-render game screen
            old_state = self.state
            self.state = "game"
            self.reset_run()
            self.draw_game()
            self.transition_surface_to = self.screen.copy()
            self.state = old_state  # Restore state
        elif to_state == "start":
            old_state = self.state
            self.state = "start"
            self.modal_history.visible = False
            self.draw_start()
            self.transition_surface_to = self.screen.copy()
            self.state = old_state

    def reset_run(self):
        self.steps = 0; self.timer = 0.0; self.start_time = time.time()
        self.paused = False; self.auto_on=False
        self.game_won = False  # Reset game won state
        self.player= [1,1]  # Bắt đầu từ (1,1) thay vì (0,0) vì viền ngoài là tường
        self.maze = self.MazeGenerated
        self.prepare_sprites()
        self.modal_victory.hide()
        
        # Get current level config
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']
        
        # Reset time limit from level config
        self.time_limit = level_config['time_limit']
        self.time_remaining = self.time_limit
        
        # Rebuild floor map for current level size
        import random as rand
        rand.seed(42)
        self.floor_map = [[rand.randrange(len(self.floor_tiles)) for _ in range(maze_cols)] for _ in range(maze_rows)]
        
        # Recompute layout for new level size
        self.compute_layout()
        
        # Spawn collectibles (small bananas) and calculate steps
        self.spawn_collectibles()  # This also sets max_steps and steps_remaining
        self.collected_count = 0

    def restart_level(self): self.reset_run()
    def toggle_play(self): self.paused = not self.paused
    
    def get_auto_cost(self):
        """Get the cost in coins for the next auto use"""
        return self.auto_use_count + 1
    
    def can_use_auto(self):
        """Check if player has enough coins for auto"""
        return self.coins >= self.get_auto_cost()
    
    def toggle_auto(self): 
        import random
        
        # Check if auto is being turned on
        if not self.auto_on:
            # Check if player has enough coins
            cost = self.get_auto_cost()
            if self.coins < cost:
                # Not enough coins - show message (could add a popup later)
                return
            
            # Deduct coins
            self.coins -= cost
            self.auto_use_count += 1
        
        self.auto_on = not self.auto_on
        if self.auto_on:
            # Chọn thuật toán giải ngẫu nhiên
            solving_algos = ["BFS", "DFS", "UCS", "A*", "Bidirectional"]
            self.selected_algo = random.choice(solving_algos)
            
            # Bắt đầu giải mê cung tự động
            self.start_auto_solve()
        else:
            # Dừng auto solve
            self.solving_maze = False
            self.solution_path = []
            self.solution_index = 0

    def start_maze_animation(self):
        """Start maze generation animation after transition"""
        import random
        
        # Get current level config
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']
        
        # Clear old particles
        self.particle_system.clear()
        
        # Tạo model với animation enabled
        self.generation_model = GenerationModel(maze_cols, maze_rows, self.selected_generation_algo)
        self.generation_model.animated_generation = True
        
        # Generate maze để tạo animation steps
        self.generation_model.generate_maze()
        
        # Copy maze trạng thái ban đầu từ model (tường hết)
        self.maze = self.generation_model.Maze
        
        # Bắt đầu animation
        self.generating_maze = True
        self.generation_timer = 0.0
        
        # Game state trong lúc animate
        self.player = [1, 1]
        self.steps = 0
        self.timer = 0.0
        self.start_time = time.time()
        self.paused = True  # Pause trong lúc đang generate
        self.game_won = False
        
        # Invalidate cache
        self.invalidate_maze_surface()
        self.modal_victory.hide()

    def generate_maze(self):
        """Sinh mê cung mới với hiệu ứng animation"""
        import random
        
        # Get current level config
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']
        
        # Reset time limit from level config
        self.time_limit = level_config['time_limit']
        self.time_remaining = self.time_limit
        
        # Chọn thuật toán ngẫu nhiên
        generation_algos = ["DFS", "Kruskal", "Binary_Tree", "Wilson", "Recursive_Division"]
        self.selected_generation_algo = random.choice(generation_algos)

        # Clear old particles
        self.particle_system.clear()
        
        # Tạo model với animation enabled và kích thước từ level config
        self.generation_model = GenerationModel(maze_cols, maze_rows, self.selected_generation_algo)
        self.generation_model.animated_generation = True
        
        # Generate maze để tạo animation steps
        # Model sẽ tự động khởi tạo maze về trạng thái ban đầu khi animated_generation = True
        self.generation_model.generate_maze()
        
        # Copy maze trạng thái ban đầu từ model
        self.maze = self.generation_model.Maze
        
        # Rebuild floor map với kích thước đúng của level mới
        import random as rand
        rand.seed(42)
        self.floor_map = [[rand.randrange(len(self.floor_tiles)) for _ in range(maze_cols)] for _ in range(maze_rows)]
        
        # Bắt đầu animation
        self.generating_maze = True
        self.generation_timer = 0.0
        
        # Reset game state
        self.player = [1, 1]
        self.steps = 0
        self.timer = 0.0
        self.start_time = time.time()
        self.paused = True  # Pause trong lúc đang generate
        self.game_won = False

        # Cập nhật sprites và invalidate cache
        self.prepare_sprites()
        self.invalidate_maze_surface()  # Important for performance optimization
        self.modal_victory.hide()

    def start_auto_solve(self):
        """Bắt đầu giải mê cung tự động với thuật toán đã chọn"""
        if self.game_won:
            return
        
        # Get level config
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']
        
        # Tìm vị trí start và end
        start_pos = None
        end_pos = None
        for y in range(maze_rows):
            for x in range(maze_cols):
                if self.maze[y][x].status == 2:  # Start
                    start_pos = (x, y)
                if self.maze[y][x].status == 3:  # End
                    end_pos = (x, y)
        
        if not start_pos or not end_pos:
            return
        
        # Build path that collects all collectibles using greedy approach
        full_path = []
        current_pos = start_pos
        remaining_collectibles = list(self.collectibles)
        
        # Collect all bananas first using nearest neighbor approach
        while remaining_collectibles:
            # Find nearest collectible
            min_dist = float('inf')
            nearest = None
            nearest_path = None
            
            for collectible in remaining_collectibles:
                # Calculate path to this collectible
                self.solving_model = SolvingModel(self.maze, maze_cols, maze_rows)
                self.solving_model.start_pos = current_pos
                self.solving_model.end_pos = collectible
                
                if self.solving_model.solve_maze(self.selected_algo):
                    path_length = len(self.solving_model.solution_path)
                    if path_length < min_dist:
                        min_dist = path_length
                        nearest = collectible
                        nearest_path = self.solving_model.solution_path
            
            if nearest and nearest_path:
                # Add path to this collectible (excluding start position to avoid duplicates)
                if full_path:
                    full_path.extend(nearest_path[1:])
                else:
                    full_path.extend(nearest_path)
                current_pos = nearest
                remaining_collectibles.remove(nearest)
            else:
                # Can't reach any collectible
                self.auto_on = False
                return
        
        # Finally, go to the end position
        self.solving_model = SolvingModel(self.maze, maze_cols, maze_rows)
        self.solving_model.start_pos = current_pos
        self.solving_model.end_pos = end_pos
        
        if self.solving_model.solve_maze(self.selected_algo):
            # Add final path (excluding start to avoid duplicate)
            full_path.extend(self.solving_model.solution_path[1:])
            
            self.solution_path = full_path
            self.solving_maze = True
            self.solution_index = 0
            self.solve_timer = 0.0
            self.paused = False
        else:
            # Không tìm thấy đường đi
            self.auto_on = False

    def calculate_shortest_path(self, start, end):
        """Calculate shortest path distance using BFS"""
        from collections import deque
        
        if start == end:
            return 0
        
        # Get level config
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']
        
        queue = deque([(start, 0)])
        visited = {start}
        
        while queue:
            (x, y), dist = queue.popleft()
            
            # Check all 4 directions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) == end:
                    return dist + 1
                
                if (0 <= nx < maze_cols and 0 <= ny < maze_rows and
                    (nx, ny) not in visited and
                    self.maze[ny][nx].status != 0):  # Not a wall
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + 1))
        
        return float('inf')  # No path found
    
    def calculate_optimal_steps(self):
        """Calculate optimal steps to collect all bananas and reach goal"""
        if not self.collectibles:
            return 0
        
        # Get level config
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']
        
        start = tuple(self.player)
        goal = (maze_cols - 2, maze_rows - 2)
        
        # Use greedy approach: always go to nearest uncollected banana
        # This is not always optimal but good approximation
        current = start
        remaining = list(self.collectibles)
        total_distance = 0
        
        # Collect all bananas
        while remaining:
            # Find nearest banana
            min_dist = float('inf')
            nearest = None
            
            for banana in remaining:
                dist = self.calculate_shortest_path(current, banana)
                if dist < min_dist:
                    min_dist = dist
                    nearest = banana
            
            if nearest:
                total_distance += min_dist
                current = nearest
                remaining.remove(nearest)
        
        # Finally go to goal
        total_distance += self.calculate_shortest_path(current, goal)
        
        return total_distance
    
    def spawn_collectibles(self):
        """Spawn collectibles (small bananas) in random path cells"""
        self.collectibles = []
        
        # Get current level config
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']
        extra_steps = level_config['extra_steps']
        
        # Find all path cells (status = 1)
        path_cells = []
        for y in range(maze_rows):
            for x in range(maze_cols):
                if self.maze[y][x].status == 1:  # Path cell
                    # Avoid start and end positions
                    if (x, y) != (1, 1) and (x, y) != (maze_cols-2, maze_rows-2):
                        path_cells.append((x, y))
        
        # Spawn exactly 3 small bananas
        if path_cells:
            num_collectibles = 3
            self.collectibles = random.sample(path_cells, min(num_collectibles, len(path_cells)))
            self.total_collectibles = len(self.collectibles)
        
        # Calculate optimal steps and set max steps using level's extra_steps
        optimal_steps = self.calculate_optimal_steps()
        self.max_steps = optimal_steps + extra_steps  # Use extra_steps from level config
        self.steps_remaining = self.max_steps

    def open_history(self): self.modal_history.visible = True

    def save_run(self, label="Manual"):
        if self.start_time is None: return
        duration = self.timer; steps=self.steps
        if duration<=0 and steps<=0: return
        rank = "S" if duration<30 and steps<50 else ("A" if duration<60 else ("B" if duration<120 else "C"))
        mode = label if "Auto" in label else ("Manual" if not self.auto_on else f"Auto ({self.selected_algo or 'None'})")
        self.history.append({"time_str": f"{int(duration//60):02d}:{int(duration%60):02d}", "steps": steps, "rank": rank, "mode": mode})

    # ---- Input
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.quit()

            # Window dragging - chỉ hoạt động khi không fullscreen
            if not self.is_fullscreen:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Kiểm tra xem có click vào vùng title bar không (vùng trên cùng, tránh các nút)
                    if event.pos[1] < 60:  # Vùng title bar
                        # Kiểm tra xem có click vào các nút window control không
                        clicked_button = False
                        for btn in (self.btn_close, self.btn_max, self.btn_min):
                            if btn.rect.collidepoint(event.pos):
                                clicked_button = True
                                break

                        if not clicked_button:
                            self.dragging = True
                            self.drag_offset = event.pos

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging = False

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        # Di chuyển cửa sổ - simplified cross-platform version
                        try:
                            # Lấy vị trí chuột hiện tại
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            # Tính toán vị trí mới
                            new_x = mouse_x - self.drag_offset[0]
                            new_y = mouse_y - self.drag_offset[1]
                            # Đặt lại vị trí cửa sổ cho lần tạo tiếp theo
                            os.environ['SDL_WINDOW_POS'] = f'{new_x},{new_y}'
                        except:
                            pass

            if self.state == "start": self.btn_start.handle_event(event)
            for b in (self.btn_close, self.btn_max, self.btn_min): b.handle_event(event)
            if self.state == "game":
                # Xử lý modal victory trước
                if self.modal_victory.visible:
                    self.modal_victory.handle_event(event)
                else:
                    for b in (self.btn_restart, self.btn_play, self.btn_pause, self.btn_auto, self.btn_history, self.btn_back): b.handle_event(event)
                    if event.type == pygame.KEYDOWN and not self.paused:
                        # Khi nhấn phím lần đầu, di chuyển 1 ô và reset timer
                        if event.key in (pygame.K_LEFT, pygame.K_a): 
                            self.move(-1,0)
                            self.last_move_time = pygame.time.get_ticks() / 1000.0
                        if event.key in (pygame.K_RIGHT, pygame.K_d): 
                            self.move(1,0)
                            self.last_move_time = pygame.time.get_ticks() / 1000.0
                        if event.key in (pygame.K_UP, pygame.K_w): 
                            self.move(0,-1)
                            self.last_move_time = pygame.time.get_ticks() / 1000.0
                        if event.key in (pygame.K_DOWN, pygame.K_s): 
                            self.move(0,1)
                            self.last_move_time = pygame.time.get_ticks() / 1000.0
            if self.modal_history.visible and (event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN)):
                self.modal_history.visible=False
            
            # Handle level select modal
            if self.showing_level_select:
                self.modal_level_select.handle_event(event)
            
            # Handle game complete modal
            if self.showing_game_complete:
                self.modal_game_complete.handle_event(event)

    def move(self, dx, dy):
        if self.game_won: return  # Không cho di chuyển khi đã thắng
        if self.steps_remaining <= 0: return  # Hết bước rồi!

        c, r = self.player; nc, nr = c+dx, r+dy
        if 0 <= nc < MAZE_COLS and 0 <= nr < MAZE_ROWS:
            # Cho phép di chuyển trên Path (1), Start (2), và End (3)
            if self.maze[nr][nc].status in [1, 2, 3]:
                self.player=[nc,nr]; self.steps += 1
                self.steps_remaining -= 1  # Giảm số bước còn lại
                
                # Check for collectible pickup
                if (nc, nr) in self.collectibles:
                    self.collectibles.remove((nc, nr))
                    self.collected_count += 1
                    # Emit particle effect for collection
                    if self.maze_rect and self.cell_size:
                        screen_x = self.maze_rect.x + nc * self.cell_size + self.cell_size // 2
                        screen_y = self.maze_rect.y + nr * self.cell_size + self.cell_size // 2
                        self.particle_system.emit_path_creation(screen_x, screen_y, self.cell_size, 
                                                               path_color=(255, 220, 100))

                # Get level config
                level_config = LEVEL_CONFIGS[self.current_level]
                maze_cols = level_config['cols']
                maze_rows = level_config['rows']
                
                # Kiểm tra chiến thắng (chạm chuối ở vị trí thực tế)
                if nc == maze_cols-2 and nr == maze_rows-2:
                    # Chỉ chiến thắng nếu đã nhặt hết chuối nhỏ
                    if self.collected_count >= self.total_collectibles:
                        self.game_won = True
                        self.paused = True
                        time_str = f"{int(self.timer//60):02d}:{int(self.timer%60):02d}"
                        
                        # Award coin if completed with more than 60% time remaining
                        earned_coin = self.time_remaining > self.time_limit * self.coin_reward_ratio
                        if earned_coin:
                            self.coins += 1
                        
                        # Unlock next level
                        if self.current_level < self.max_level:
                            self.unlocked_levels.add(self.current_level + 1)
                        
                        # Lưu stats cho level này
                        self.level_stats[self.current_level] = {
                            'time': time_str,
                            'steps': self.steps,
                            'completed': True,
                            'coins_earned': 1 if earned_coin else 0
                        }
                        
                        # Kiểm tra nếu đây là level cuối -> hiển thị game complete
                        if self.current_level >= self.max_level:
                            self.showing_game_complete = True
                            self.modal_game_complete.show(self.level_stats, self.window_rect.w, self.window_rect.h)
                        else:
                            # Hiển thị modal victory với nút Next
                            self.modal_victory.show(time_str, self.steps, is_victory=True, show_next=True)
                    # Nếu chưa nhặt hết, không làm gì (không cho chiến thắng)

    # ---- Update / Draw
    def update(self, dt):
        # Update transition
        if self.transitioning:
            self.transition_progress += dt / self.transition_duration
            if self.transition_progress >= 1.0:
                # Transition complete
                self.transition_progress = 1.0
                self.transitioning = False
                self.state = self.transition_to
                
                # Apply final state changes
                if self.state == "start":
                    self.modal_history.visible = False
                elif self.state == "game":
                    # Start maze generation animation after transition completes
                    self.start_maze_animation()
                
                # Clean up
                self.transition_surface_from = None
                self.transition_surface_to = None
            return  # Skip normal update during transition
        
        # Xử lý di chuyển liên tục khi giữ phím
        if self.state == "game" and not self.paused and not self.game_won:
            current_time = pygame.time.get_ticks() / 1000.0
            
            # Kiểm tra nếu đã đủ thời gian delay
            if current_time - self.last_move_time >= self.key_hold_delay:
                keys = pygame.key.get_pressed()
                
                # Kiểm tra phím di chuyển đang được giữ
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.move(-1, 0)
                    self.last_move_time = current_time
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.move(1, 0)
                    self.last_move_time = current_time
                elif keys[pygame.K_UP] or keys[pygame.K_w]:
                    self.move(0, -1)
                    self.last_move_time = current_time
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    self.move(0, 1)
                    self.last_move_time = current_time
        
        # Update particle system
        self.particle_system.update(dt)
        
        # Update game complete modal (for confetti animation)
        if self.showing_game_complete:
            self.modal_game_complete.update(dt)
        
        # Update maze generation animation
        if self.generating_maze:
            self.generation_timer += dt
            
            # Apply multiple steps per frame for smoother animation (giảm xuống để chậm hơn)
            steps_per_frame = max(1, int(0.016 / self.generation_speed)) if self.generation_speed > 0 else 1
            
            for _ in range(steps_per_frame):
                if self.generation_model and self.generation_model.current_step < len(self.generation_model.generation_steps):
                    # Get current step info BEFORE applying
                    current_step_idx = self.generation_model.current_step
                    if current_step_idx < len(self.generation_model.generation_steps):
                        x, y, action = self.generation_model.generation_steps[current_step_idx]
                        
                        # Apply next step
                        has_more = self.generation_model.apply_next_step()
                        
                        # Emit particles based on action
                        if self.maze_rect and self.cell_size:
                            # Calculate screen position
                            screen_x = self.maze_rect.x + x * self.cell_size + self.cell_size // 2
                            screen_y = self.maze_rect.y + y * self.cell_size + self.cell_size // 2
                            
                            if action == 'break_wall':
                                # Wall breaking - dramatic effect
                                self.particle_system.emit_wall_break(screen_x, screen_y, self.cell_size)
                            elif action == 'path':
                                # Path creation - subtle effect
                                self.particle_system.emit_path_creation(screen_x, screen_y, self.cell_size)
                            elif action == 'build_wall':
                                # Building wall - different color particles
                                self.particle_system.emit_path_creation(
                                    screen_x, screen_y, self.cell_size, 
                                    path_color=(150, 100, 100)
                                )
                    
                    # Copy updated maze state
                    self.maze = self.generation_model.Maze
                    
                    if not has_more:
                        # Animation complete - set start and end positions
                        self.generating_maze = False
                        self.paused = False
                        
                        # Get level config for finding start/end
                        level_config = LEVEL_CONFIGS[self.current_level]
                        maze_cols = level_config['cols']
                        maze_rows = level_config['rows']
                        
                        # Find and set start position (first path cell)
                        start_found = False
                        for y in range(maze_rows):
                            for x in range(maze_cols):
                                if self.maze[y][x].status == 1:
                                    self.maze[y][x].status = 2  # Start
                                    self.player = [x, y]
                                    start_found = True
                                    break
                            if start_found:
                                break
                        
                        # Find and set end position (last path cell)
                        end_found = False
                        for y in range(maze_rows - 1, -1, -1):
                            for x in range(maze_cols - 1, -1, -1):
                                if self.maze[y][x].status == 1:
                                    self.maze[y][x].status = 3  # End
                                    end_found = True
                                    break
                            if end_found:
                                break
                        
                        self.MazeGenerated = self.maze
                        self.start_time = time.time()
                        
                        # Recompute layout to adjust cell size for the new maze dimensions
                        self.compute_layout()
                        
                        # Prepare sprites with new cell size to scale tiles correctly
                        self.prepare_sprites()
                        
                        # Spawn collectibles after maze generation complete
                        self.spawn_collectibles()
                        self.collected_count = 0
                        
                        # Clear particles when done
                        self.particle_system.clear()
                        break
                else:
                    self.generating_maze = False
                    break
        
        # Update auto solve animation
        if self.solving_maze and self.auto_on and not self.paused:
            self.solve_timer += dt
            
            if self.solve_timer >= self.solve_speed:
                self.solve_timer = 0.0
                
                if self.solution_index < len(self.solution_path) and self.steps_remaining > 0:
                    # Di chuyển đến vị trí tiếp theo trong đường đi
                    next_pos = self.solution_path[self.solution_index]
                    self.player = list(next_pos)
                    self.steps += 1
                    self.steps_remaining -= 1  # Giảm số bước còn lại
                    self.solution_index += 1
                    
                    # Check for collectible pickup during auto-solve
                    if next_pos in self.collectibles:
                        self.collectibles.remove(next_pos)
                        self.collected_count += 1
                    
                    # Get level config
                    level_config = LEVEL_CONFIGS[self.current_level]
                    maze_cols = level_config['cols']
                    maze_rows = level_config['rows']
                    
                    # Kiểm tra xem đã hết bước
                    if self.steps_remaining <= 0:
                        self.game_won = True
                        self.paused = True
                        self.auto_on = False
                        self.solving_maze = False
                        time_str = "OUT OF STEPS!"
                        self.modal_victory.show(time_str, self.steps, is_victory=False, show_next=False)
                    # Kiểm tra xem đã đến đích chưa
                    elif next_pos[0] == maze_cols-2 and next_pos[1] == maze_rows-2:
                        # Chỉ thắng nếu đã nhặt hết chuối
                        if self.collected_count >= self.total_collectibles:
                            self.game_won = True
                            self.paused = True
                            self.auto_on = False
                            self.solving_maze = False
                            time_str = f"{int(self.timer//60):02d}:{int(self.timer%60):02d}"
                            
                            # Award coin if completed with more than 60% time remaining
                            earned_coin = self.time_remaining > self.time_limit * self.coin_reward_ratio
                            if earned_coin:
                                self.coins += 1
                            
                            # Unlock next level
                            if self.current_level < self.max_level:
                                self.unlocked_levels.add(self.current_level + 1)
                            
                            # Lưu stats cho level này
                            self.level_stats[self.current_level] = {
                                'time': time_str,
                                'steps': self.steps,
                                'completed': True,
                                'coins_earned': 1 if earned_coin else 0
                            }
                            
                            # Kiểm tra nếu đây là level cuối -> hiển thị game complete
                            if self.current_level >= self.max_level:
                                self.showing_game_complete = True
                                self.modal_game_complete.show(self.level_stats, self.window_rect.w, self.window_rect.h)
                            else:
                                # Hiển thị modal victory với nút Next
                                self.modal_victory.show(time_str, self.steps, is_victory=True, show_next=True)
                else:
                    # Đã đi hết đường hoặc hết bước
                    self.solving_maze = False
                    self.auto_on = False
        
        # Update game state
        if self.state=="game" and not self.paused:
            self.timer += dt
            self.monkey_idle.update(dt)
            self.banana.update(dt)
            
            # Update countdown timer
            if not self.game_won and not self.generating_maze:
                self.time_remaining -= dt
                
                # Check for time out
                if self.time_remaining <= 0:
                    self.time_remaining = 0
                    self.game_won = True
                    self.paused = True
                    # Show defeat message
                    time_str = "TIME OUT!"
                    self.modal_victory.show(time_str, self.steps, is_victory=False, show_next=False)
                
                # Check for out of steps
                if self.steps_remaining <= 0 and not self.game_won:
                    self.game_won = True
                    self.paused = True
                    # Show defeat message
                    time_str = "OUT OF STEPS!"
                    self.modal_victory.show(time_str, self.steps, is_victory=False, show_next=False)

    def draw_start(self):
        # background full, no blur
        bg = pygame.transform.smoothscale(self.bg_start, (self.window_rect.w, self.window_rect.h))
        self.screen.blit(bg, (0, 0))

        # Cập nhật kích thước nút START theo tỷ lệ cửa sổ
        base_width = 320  # Kích thước cơ bản (tăng từ 240 lên 320)
        scale_factor = min(self.window_rect.w / 1920, self.window_rect.h / 1080)  # Tỷ lệ so với fullscreen chuẩn
        scale_factor = max(0.5, min(1.0, scale_factor))  # Giới hạn từ 50% đến 100%

        new_width = int(base_width * scale_factor)
        start_size = calculate_button_size(self.btn_assets['start'], target_width=new_width)

        self.btn_start.rect = pygame.Rect(0, 0, start_size[0], start_size[1])
        self.btn_start.scaled_bg = pygame.transform.smoothscale(self.btn_start.bg_image, start_size)

        # place START slightly left and lower (~82% h)
        self.btn_start.rect.center = (int(self.window_rect.centerx * 0.85), int(self.window_rect.h * 0.82))
        self.btn_start.draw(self.screen)

        # Window controls - vẽ cuối cùng để đảm bảo không bị đè
        for b in (self.btn_min, self.btn_max, self.btn_close):
            b.draw(self.screen)
        
        # Draw level select modal if visible
        if self.showing_level_select:
            self.modal_level_select.draw(self.screen, self.window_rect, 
                                         self.font_title, self.font_ui, LEVEL_CONFIGS)

    def draw_game(self):
        # Update performance monitoring
        self.update_performance_mode()

        # Skip frame if in performance mode
        if self.should_skip_frame():
            return

        # jungle background full - use cached version
        bg_scaled = self.get_scaled_background(self.bg_jungle, (self.window_rect.w, self.window_rect.h))
        self.screen.blit(bg_scaled, (0,0))

        # Scale sidebar width theo tỷ lệ cửa sổ
        scale_factor = min(self.window_rect.w / 1920, self.window_rect.h / 1080)
        scale_factor = max(0.5, min(1.5, scale_factor))  # Tăng max từ 1.2 lên 1.5 để cho phép to hơn nữa
        scaled_panel_w = int(RIGHT_PANEL_W * scale_factor)
        scaled_panel_w = max(180, min(scaled_panel_w, 650))  # Giảm tối thiểu từ 200 xuống 180px

        # sidebar card - use optimized drawing for small windows
        sidebar_card_margin = int(10 * scale_factor)
        sidebar_card_margin = max(2, sidebar_card_margin)  # Giảm margin xuống 2px khi màn hình nhỏ
        sidebar = pygame.Rect(
            self.window_rect.w - scaled_panel_w + sidebar_card_margin, 
            60, 
            scaled_panel_w - (sidebar_card_margin * 2), 
            self.window_rect.h - 70
        )

        # Vẽ sidebar bán trong suốt (cả performance mode và normal mode)
        if self.skip_expensive_effects:
            # Simple sidebar với alpha cho performance mode
            sidebar_surface = pygame.Surface(sidebar.size, pygame.SRCALPHA)
            sidebar_surface.fill((18,24,18,80))  # Bán trong suốt trong performance mode
            self.screen.blit(sidebar_surface, sidebar.topleft)
            pygame.draw.rect(self.screen, (110,150,110), sidebar, 2, border_radius=12)
        else:
            # Full quality sidebar - Nền rất trong suốt để thấy rõ background phía sau
            draw_glass_card(self.screen, sidebar, radius=22, bg=(18,24,18,100), border=(110,150,110), border_alpha=90)

        # chips - căn giữa trong sidebar
        # Hiển thị trạng thái generating nếu đang generate maze
        if self.generating_maze and self.generation_model:
            status_text = f"Generating... {self.generation_model.current_step}/{len(self.generation_model.generation_steps)}"
            status_color = (255, 255, 100)  # Màu vàng
            status_label = self.font_small.render(status_text, True, status_color)
            status_x = sidebar.x + (sidebar.width - status_label.get_width()) // 2
            status_y = sidebar.y + int(20*scale_factor)
            self.screen.blit(status_label, (status_x, status_y))
        
        # Hiển thị thời gian còn lại thay vì thời gian đã chơi
        time_left_minutes = int(self.time_remaining // 60)
        time_left_seconds = int(self.time_remaining % 60)
        t = f"{time_left_minutes:02d}:{time_left_seconds:02d}"
        y0 = sidebar.y+int(35*scale_factor)  # Giảm từ 50 xuống 35 để nhích lên
        chip_spacing = int(10*scale_factor)
        
        # Tính kích thước time box dựa trên aspect ratio của asset - TO HƠN
        time_box_img = self.box_assets['time']
        time_box_aspect = time_box_img.get_width() / time_box_img.get_height()
        target_time_h = max(40, int(100 * scale_factor))  # Giảm tối thiểu từ 50 xuống 40px
        target_time_h = min(target_time_h, 120)  # Tối đa 120px
        chip1_w = int(target_time_h * time_box_aspect)  # Chiều rộng giữ tỷ lệ
        chip1_h = target_time_h
        
        # Tính kích thước step box dựa trên aspect ratio của asset - TO HƠN
        step_box_img = self.box_assets['step']
        step_box_aspect = step_box_img.get_width() / step_box_img.get_height()
        target_step_h = target_time_h  # Cùng chiều cao với time box
        chip2_w = int(target_step_h * step_box_aspect)  # Chiều rộng giữ tỷ lệ
        chip2_h = target_step_h
        
        total_chip_w = chip1_w + chip_spacing + chip2_w
        
        # Căn giữa cả 2 chips trong sidebar
        chips_start_x = sidebar.x + (sidebar.width - total_chip_w) // 2
        chip1 = pygame.Rect(chips_start_x, y0, chip1_w, chip1_h)

        # Vẽ time box với background image (giữ tỷ lệ gốc)
        time_box_scaled = pygame.transform.smoothscale(self.box_assets['time'], (chip1_w, chip1_h))
        self.screen.blit(time_box_scaled, chip1.topleft)

        # Font lớn hơn và in đậm cho time với màu đổi theo thời gian còn lại
        if self.time_remaining <= 10:
            time_color = (255, 80, 80)  # Đỏ - nguy hiểm
        elif self.time_remaining <= 30:
            time_color = (255, 200, 80)  # Vàng cam - cảnh báo
        else:
            time_color = (255, 250, 220)  # Vàng kem - bình thường
        
        time_label = self.font_chip.render(t, True, time_color)
        time_x = chip1.x + (chip1.width - time_label.get_width()) // 2  # Căn giữa
        time_y = chip1.y + (chip1.height - time_label.get_height()) // 2  # Căn giữa
        self.screen.blit(time_label, (time_x, time_y))

        chip2 = pygame.Rect(chip1.right + chip_spacing, y0, chip2_w, chip2_h)

        # Vẽ step box với background image (giữ tỷ lệ gốc)
        step_box_scaled = pygame.transform.smoothscale(self.box_assets['step'], (chip2_w, chip2_h))
        self.screen.blit(step_box_scaled, chip2.topleft)

        # Font lớn hơn và in đậm cho steps remaining (jungle theme)
        # Color code based on remaining steps
        if self.steps_remaining > 20:
            steps_color = (100, 255, 100)  # Green
        elif self.steps_remaining > 10:
            steps_color = (255, 220, 100)  # Yellow
        else:
            steps_color = (255, 100, 100)  # Red
        
        steps_label = self.font_chip.render(str(max(0, self.steps_remaining)), True, steps_color)
        steps_x = chip2.x + (chip2.width - steps_label.get_width()) // 2  # Căn giữa
        steps_y = chip2.y + (chip2.height - steps_label.get_height()) // 2  # Căn giữa
        self.screen.blit(steps_label, (steps_x, steps_y))
        
        # Display collectibles count với banana icon
        info_y = chip2.bottom + int(8 * scale_factor)
        
        # Collectibles count - sử dụng hình ảnh banana thay vì emoji
        icon_size = int(20 * scale_factor)
        icon_size = max(14, min(icon_size, 24))
        
        # Scale banana icon
        banana_icon = pygame.transform.smoothscale(self.banana_img, (icon_size, icon_size))
        
        collectibles_text = f"{self.collected_count}/{self.total_collectibles}"
        collectibles_label = self.font_small.render(collectibles_text, True, (255, 220, 100))
        
        # Tính tổng width và căn giữa
        total_width = icon_size + 4 + collectibles_label.get_width()
        start_x = sidebar.x + (sidebar.width - total_width) // 2
        
        # Vẽ banana icon và text
        self.screen.blit(banana_icon, (start_x, info_y + (collectibles_label.get_height() - icon_size) // 2))
        self.screen.blit(collectibles_label, (start_x + icon_size + 4, info_y))
        info_y += collectibles_label.get_height() + int(6 * scale_factor)
        
        # === COIN BOX - Ô hiển thị xu ===
        coin_box_w = int(sidebar.width * 0.85)
        coin_box_h = int(35 * scale_factor)
        coin_box_h = max(28, min(coin_box_h, 45))
        coin_box_x = sidebar.x + (sidebar.width - coin_box_w) // 2
        coin_box_y = info_y
        coin_box = pygame.Rect(coin_box_x, coin_box_y, coin_box_w, coin_box_h)
        
        # Background gradient effect for coin box
        coin_bg_color = (60, 50, 20)  # Dark gold/brown background
        coin_border_color = (255, 200, 50)  # Gold border
        pygame.draw.rect(self.screen, coin_bg_color, coin_box, border_radius=8)
        pygame.draw.rect(self.screen, coin_border_color, coin_box, width=2, border_radius=8)
        
        # Inner highlight
        inner_highlight = pygame.Rect(coin_box.x + 3, coin_box.y + 3, coin_box.width - 6, coin_box.height // 3)
        highlight_surf = pygame.Surface((inner_highlight.width, inner_highlight.height), pygame.SRCALPHA)
        highlight_surf.fill((255, 220, 100, 40))
        self.screen.blit(highlight_surf, inner_highlight.topleft)
        
        # Coin icon (vẽ hình tròn vàng) và text
        coin_icon_size = int(18 * scale_factor)
        coin_icon_size = max(12, min(coin_icon_size, 22))
        
        coin_num_text = str(self.coins)
        coin_label = self.font_chip.render(coin_num_text, True, (255, 215, 0))
        
        # Tính tổng width và căn giữa trong coin box
        coin_total_width = coin_icon_size + 6 + coin_label.get_width()
        coin_start_x = coin_box.x + (coin_box.width - coin_total_width) // 2
        coin_center_y = coin_box.y + coin_box.height // 2
        
        # Vẽ coin icon (hình tròn vàng với viền và chữ $)
        coin_icon_x = coin_start_x + coin_icon_size // 2
        coin_icon_y = coin_center_y
        pygame.draw.circle(self.screen, (255, 200, 50), (coin_icon_x, coin_icon_y), coin_icon_size // 2)  # Vàng đậm
        pygame.draw.circle(self.screen, (218, 165, 32), (coin_icon_x, coin_icon_y), coin_icon_size // 2, 2)  # Viền
        # Vẽ chữ $ nhỏ trong coin
        dollar_font_size = max(10, coin_icon_size - 6)
        dollar_font = pygame.font.SysFont('Arial', dollar_font_size, bold=True)
        dollar_text = dollar_font.render('$', True, (139, 90, 0))
        self.screen.blit(dollar_text, (coin_icon_x - dollar_text.get_width() // 2, coin_icon_y - dollar_text.get_height() // 2))
        
        # Vẽ số coins
        coin_text_x = coin_start_x + coin_icon_size + 6
        coin_text_y = coin_center_y - coin_label.get_height() // 2
        self.screen.blit(coin_label, (coin_text_x, coin_text_y))
        
        info_y = coin_box.bottom + int(6 * scale_factor)
        
        # Auto cost display (smaller, below coin box)
        auto_cost = self.get_auto_cost()
        if self.can_use_auto():
            auto_cost_color = (100, 255, 100)  # Green - can afford
            auto_status = f"Auto: {auto_cost} coins"
        else:
            auto_cost_color = (255, 100, 100)  # Red - can't afford
            auto_status = f"Auto: {auto_cost} coins"
        auto_label = self.font_small.render(auto_status, True, auto_cost_color)
        auto_x = sidebar.x + (sidebar.width - auto_label.get_width()) // 2
        self.screen.blit(auto_label, (auto_x, info_y))
        info_y += auto_label.get_height() + int(8 * scale_factor)

        # buttons - layout mới: mỗi nút chính một hàng riêng, căn giữa, giữ aspect ratio
        side_margin = int(8*scale_factor)  # Margin các nút trong sidebar
        side_margin = max(2, side_margin)  # Giảm margin tối thiểu xuống 2px khi màn hình rất nhỏ
        
        # Tính chiều cao sidebar có sẵn
        sidebar_height = sidebar.height
        
        # Vị trí bắt đầu các nút sau coin box và auto info
        cur_y_start = info_y
        
        # Chiều cao khả dụng cho các nút
        available_height = sidebar_height - (cur_y_start - sidebar.y) - 20  # 20px buffer cuối
        
        full_btn_w = sidebar.width - (side_margin * 2)  # Chiều rộng tối đa - DỰA VÀO SIDEBAR.WIDTH
        full_btn_w = max(80, min(full_btn_w, sidebar.width - 6))  # Giảm từ 100 xuống 80px, margin 6px
        
        # Chiều cao điều chỉnh theo kích thước màn hình - THU NHỎ KHI MÀN HÌNH NHỎ
        target_btn_h = int(120 * scale_factor)
        target_btn_h = max(30, min(target_btn_h, 130))  # Giảm tối thiểu từ 40 xuống 30px
        
        # Tính tổng chiều cao cần thiết cho các nút
        # 4 nút: restart + auto + history + back
        total_elements_height = target_btn_h * 4
        
        # Tính spacing cần thiết
        num_spaces = 3  # Số khoảng cách giữa 4 nút
        min_spacing = 3  # Spacing tối thiểu
        desired_spacing = max(4, int(12 * scale_factor))  # Spacing mong muốn: 4-12px
        
        # Thử với spacing mong muốn trước
        required_height_desired = total_elements_height + (num_spaces * desired_spacing)
        required_height_min = total_elements_height + (num_spaces * min_spacing)
        
        if required_height_desired <= available_height:
            # Đủ chỗ với spacing lớn
            spacing = desired_spacing
        elif required_height_min <= available_height:
            # Đủ chỗ với spacing vừa phải, tính toán spacing chính xác
            spacing = int((available_height - total_elements_height) / num_spaces)
            spacing = max(min_spacing, min(spacing, desired_spacing))
        else:
            # Không đủ chỗ, giảm chiều cao nút để có spacing tối thiểu
            available_for_elements = available_height - (num_spaces * min_spacing)
            reduction_ratio = available_for_elements / total_elements_height
            
            target_btn_h = int(target_btn_h * reduction_ratio * 0.95)  # 0.95 để có buffer
            target_btn_h = max(22, target_btn_h)  # Tối thiểu 22px
            
            spacing = min_spacing  # Dùng spacing tối thiểu
        
        cur_y = cur_y_start

        # Tính kích thước riêng cho từng nút trước
        restart_size_temp = calculate_button_size(self.btn_assets['restart'], target_height=target_btn_h)
        auto_size_temp = calculate_button_size(self.btn_assets['auto'], target_height=target_btn_h)
        
        # Lấy chiều rộng lớn nhất nhưng KHÔNG ĐƯỢC vượt quá full_btn_w
        max_width = max(restart_size_temp[0], auto_size_temp[0])
        max_width = min(max_width, full_btn_w)  # Bắt buộc không vượt quá sidebar
        
        # Nếu nút vẫn quá rộng, giảm chiều cao để giảm chiều rộng (giữ tỷ lệ)
        if max_width > full_btn_w:
            ratio = restart_size_temp[0] / restart_size_temp[1] if restart_size_temp[1] > 0 else 1
            target_btn_h = int(full_btn_w / ratio)
            target_btn_h = max(25, target_btn_h)
            restart_size_temp = calculate_button_size(self.btn_assets['restart'], target_height=target_btn_h)
            auto_size_temp = calculate_button_size(self.btn_assets['auto'], target_height=target_btn_h)
            max_width = min(max(restart_size_temp[0], auto_size_temp[0]), full_btn_w)
        
        restart_size = (max_width, target_btn_h)
        auto_size = (max_width, target_btn_h)
        
        # History và back buttons - giới hạn kích thước CHẶT CHẼ
        history_size_temp = calculate_button_size(self.btn_assets['history'], target_height=target_btn_h)
        history_width = min(history_size_temp[0], full_btn_w)
        
        # Nếu vẫn quá rộng, tính lại chiều cao
        if history_size_temp[0] > full_btn_w:
            ratio = history_size_temp[0] / history_size_temp[1] if history_size_temp[1] > 0 else 1
            new_h = int(full_btn_w / ratio)
            new_h = max(25, new_h)
            history_size_temp = calculate_button_size(self.btn_assets['history'], target_height=new_h)
            history_width = min(history_size_temp[0], full_btn_w)
            history_size = (history_width, new_h)
        else:
            history_size = (history_width, target_btn_h)
        
        back_size_temp = calculate_button_size(self.btn_assets['back'], target_height=target_btn_h)
        back_width = min(back_size_temp[0], full_btn_w)
        
        # Nếu vẫn quá rộng, tính lại chiều cao
        if back_size_temp[0] > full_btn_w:
            ratio = back_size_temp[0] / back_size_temp[1] if back_size_temp[1] > 0 else 1
            new_h = int(full_btn_w / ratio)
            new_h = max(25, new_h)
            back_size_temp = calculate_button_size(self.btn_assets['back'], target_height=new_h)
            back_width = min(back_size_temp[0], full_btn_w)
            back_size = (back_width, new_h)
        else:
            back_size = (back_width, target_btn_h)

        # Dòng 1: Restart button (căn giữa trong sidebar)
        restart_x = sidebar.x + (sidebar.width - restart_size[0]) // 2
        restart_x = max(sidebar.x + side_margin, restart_x)  # Đảm bảo không tràn trái
        self.btn_restart.rect = pygame.Rect(restart_x, cur_y, restart_size[0], restart_size[1])
        self.btn_restart.draw(self.screen)
        cur_y += restart_size[1] + spacing

        # Dòng 2: Auto button (căn giữa trong sidebar)
        auto_x = sidebar.x + (sidebar.width - auto_size[0]) // 2
        auto_x = max(sidebar.x + side_margin, auto_x)  # Đảm bảo không tràn trái
        self.btn_auto.rect = pygame.Rect(auto_x, cur_y, auto_size[0], auto_size[1])
        self.btn_auto.draw(self.screen)
        cur_y += auto_size[1] + spacing

        # Dòng 3: History button (căn giữa trong sidebar)
        history_x = sidebar.x + (sidebar.width - history_size[0]) // 2
        history_x = max(sidebar.x + side_margin, history_x)  # Đảm bảo không tràn trái
        self.btn_history.rect = pygame.Rect(history_x, cur_y, history_size[0], history_size[1])
        self.btn_history.draw(self.screen)
        cur_y += history_size[1] + spacing

        # Dòng 4: Back button (căn giữa trong sidebar)
        back_x = sidebar.x + (sidebar.width - back_size[0]) // 2
        back_x = max(sidebar.x + side_margin, back_x)  # Đảm bảo không tràn trái
        self.btn_back.rect = pygame.Rect(back_x, cur_y, back_size[0], back_size[1])
        self.btn_back.draw(self.screen)

        # maze frame card - simplified for performance mode
        if self.skip_expensive_effects:
            pygame.draw.rect(self.screen, (12,22,12), self.maze_rect, border_radius=8)
        else:
            draw_glass_card(self.screen, self.maze_rect, radius=16, bg=(12,22,12,140), border=(90,120,90), border_alpha=55)

        # Get level config for rendering
        level_config = LEVEL_CONFIGS[self.current_level]
        maze_cols = level_config['cols']
        maze_rows = level_config['rows']
        
        # Use optimized maze rendering for small cells
        if self.cell_size < MIN_CELL_SIZE_FOR_DETAILS:
            # Use pre-rendered maze surface for better performance
            maze_surface = self.get_optimized_maze_surface()
            self.screen.blit(maze_surface, self.maze_rect.topleft)
        else:
            # Standard maze rendering for larger cells
            cell = self.cell_size
            for r in range(maze_rows):
                for c in range(maze_cols):
                    x = self.maze_rect.x + c * cell
                    y = self.maze_rect.y + r * cell
                    idx = self.floor_map[r][c]
                    # Use pre-scaled cached tiles instead of scaling every frame
                    self.screen.blit(self.scaled_floor_tiles[idx], (x,y))

            # draw player (monkey) - VẼ TRƯỚC walls để đứng sau tường
            px = self.maze_rect.x + self.player[0] * cell + (cell - self.monkey_idle.current().get_width())//2
            py = self.maze_rect.y + self.player[1] * cell + (cell - self.monkey_idle.current().get_height())//2
            self.screen.blit(self.monkey_idle.current(), (px, py))

            # draw collectibles (small bananas) - only if not generating maze
            if not self.generating_maze and self.collectibles:
                small_banana_size = max(14, int(cell * 0.45))  # Tăng size lên 14px và 45%
                
                # Always create or update cache if size changed (regardless of performance mode)
                if (self.banana_img and 
                    (self.small_banana_cache is None or self.small_banana_size_cache != small_banana_size)):
                    try:
                        self.small_banana_cache = pygame.transform.smoothscale(
                            self.banana_img, (small_banana_size, small_banana_size))
                        self.small_banana_size_cache = small_banana_size
                        
                        # Clear rotation cache when size changes
                        self.banana_rotation_cache.clear()
                        
                        # Pre-render glow surfaces (2 layers instead of 3 for better performance)
                        self.banana_glow_cache = []
                        for i in range(2):  # Giảm từ 3 xuống 2 layers
                            glow_radius = small_banana_size // 2 + 6 - i * 3
                            alpha = int(70 - i * 25)
                            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                            pygame.draw.circle(glow_surf, (255, 220, 100, alpha), 
                                             (glow_radius, glow_radius), glow_radius)
                            self.banana_glow_cache.append((glow_surf, glow_radius))
                        
                        self.banana_last_cache_size = small_banana_size
                    except Exception as e:
                        print(f"Failed to create banana cache: {e}")
                        self.small_banana_cache = None
                
                for idx, (col_x, col_y) in enumerate(self.collectibles):
                    cx = self.maze_rect.x + col_x * cell + cell // 2
                    cy_base = self.maze_rect.y + col_y * cell + cell // 2
                    
                    # Hiệu ứng lơ lửng (floating effect) - sử dụng float để mượt hơn
                    float_offset = math.sin(self.timer * 2 + idx * 1.5) * 5  # Di chuyển lên xuống 5 pixels
                    cy = cy_base + float_offset  # Giữ nguyên float, không làm tròn
                    
                    # Try to use cached image even in performance mode
                    if self.small_banana_cache is not None:
                        try:
                            if not self.skip_expensive_effects:
                                # Full animation with rotation and glow
                                angle = int((self.timer * 50) % 360)
                                # Cache rotation frames (every 15 degrees)
                                cache_angle = (angle // 15) * 15
                                
                                if cache_angle not in self.banana_rotation_cache:
                                    self.banana_rotation_cache[cache_angle] = pygame.transform.rotate(
                                        self.small_banana_cache, cache_angle)
                                    # Limit cache size
                                    if len(self.banana_rotation_cache) > 24:  # 360/15 = 24 frames
                                        self.banana_rotation_cache.clear()
                                
                                rotated = self.banana_rotation_cache[cache_angle]
                                rot_rect = rotated.get_rect(center=(cx, cy))
                                
                                # Hiệu ứng pulse cho viền (nhấp nháy nhẹ)
                                pulse = abs(math.sin(self.timer * 3))  # 0 đến 1
                                
                                # Vẽ glow effect từ cache (2 layers thay vì 3)
                                for glow_surf, glow_radius in self.banana_glow_cache:
                                    self.screen.blit(glow_surf, (cx - glow_radius, cy - glow_radius))
                                
                                # Vẽ viền tròn vàng với hiệu ứng pulse
                                border_radius = small_banana_size // 2 + int(2 + pulse * 2)
                                border_color = (255, 220 + int(pulse * 35), 0)
                                
                                # Vẽ outer glow cho viền (đơn giản hóa)
                                pygame.draw.circle(self.screen, (255, 235, 100), (int(cx), int(cy)), border_radius + 2, 1)
                                
                                # Vẽ viền chính
                                pygame.draw.circle(self.screen, border_color, (int(cx), int(cy)), border_radius, 2)
                                
                                self.screen.blit(rotated, rot_rect.topleft)
                            else:
                                # Static image without rotation in performance mode (still has floating)
                                # Use cached glow if available
                                if self.banana_glow_cache:
                                    glow_surf, glow_radius = self.banana_glow_cache[0]
                                    self.screen.blit(glow_surf, (int(cx) - glow_radius, int(cy) - glow_radius))
                                
                                # Viền vàng
                                border_radius = small_banana_size // 2 + 2
                                pygame.draw.circle(self.screen, (255, 220, 0), (int(cx), int(cy)), border_radius, 2)
                                
                                img_rect = self.small_banana_cache.get_rect(center=(cx, cy))
                                self.screen.blit(self.small_banana_cache, img_rect.topleft)
                        except Exception as e:
                            # Fallback to simple circle (no glow in fallback for performance)
                            circle_radius = max(5, cell // 4)
                            pygame.draw.circle(self.screen, (255, 220, 100), (int(cx), int(cy)), circle_radius)
                            pygame.draw.circle(self.screen, (255, 200, 0), (int(cx), int(cy)), circle_radius + 2, 2)
                    else:
                        # Image not loaded - use circle with border (no glow for performance)
                        circle_radius = max(5, cell // 4)
                        pygame.draw.circle(self.screen, (255, 220, 100), (int(cx), int(cy)), circle_radius)
                        pygame.draw.circle(self.screen, (255, 200, 0), (int(cx), int(cy)), circle_radius + 2, 2)
            
            # draw banana goal - VẼ TRƯỚC walls để đứng sau tường
            gx = self.maze_rect.x + (maze_cols - 2)*cell + (cell - self.banana.base_image.get_width())//2
            gy = self.maze_rect.y + (maze_rows - 2)*cell + (cell - self.banana.base_image.get_height())//2

            if self.skip_expensive_effects:
                # Static banana without animation
                self.screen.blit(self.banana.base_image, (gx, gy))
            else:
                # Animated floating banana
                self.banana.draw(self.screen, (gx, gy))

            # draw walls using cached scaled tile - VẼ SAU player và banana để che chúng
            for r in range(maze_rows):
                for c in range(maze_cols):
                    if self.maze[r][c].status == 0:
                        x = self.maze_rect.x + c*cell; y = self.maze_rect.y + r*cell
                        # Use pre-scaled cached wall tile
                        self.screen.blit(self.scaled_wall_tile, (x, y))
            
            # Hiệu ứng cho đường đi đang được tạo
            if self.generating_maze and self.generation_model:
                current_step = self.generation_model.current_step - 1
                if current_step >= 0:
                    # Tạo hiệu ứng sáng cho các ô vừa phá tường
                    highlight_range = 8  # Số ô được highlight
                    for i in range(max(0, current_step - highlight_range), current_step + 1):
                        if i < len(self.generation_model.generation_steps):
                            step_x, step_y, action = self.generation_model.generation_steps[i]
                            
                            if action in ['break_wall', 'path']:
                                # Vẽ hiệu ứng cho path và break_wall
                                x = self.maze_rect.x + step_x * cell
                                y = self.maze_rect.y + step_y * cell
                                
                                # Tính độ sáng giảm dần theo thời gian
                                age = current_step - i
                                intensity = 1 - (age / highlight_range)
                                
                                # Màu vàng sáng cho ô vừa phá
                                if age == 0:
                                    # Ô hiện tại - sáng nhất với viền sáng
                                    overlay = pygame.Surface((cell, cell), pygame.SRCALPHA)
                                    overlay.fill((255, 255, 150, 220))
                                    self.screen.blit(overlay, (x, y))
                                    # Viền sáng
                                    pygame.draw.rect(self.screen, (255, 255, 200), (x, y, cell, cell), 2)
                                else:
                                    # Ô cũ hơn - gradient màu từ vàng sang xanh nhạt
                                    alpha = int(180 * intensity)
                                    r = int(255 * intensity + 100 * (1 - intensity))
                                    g = int(255 * intensity + 200 * (1 - intensity))
                                    b = int(150 * intensity + 150 * (1 - intensity))
                                    overlay = pygame.Surface((cell, cell), pygame.SRCALPHA)
                                    overlay.fill((r, g, b, alpha))
                                    self.screen.blit(overlay, (x, y))
                            
                            elif action == 'build_wall':
                                # Hiệu ứng xây tường (cho Recursive Division)
                                x = self.maze_rect.x + step_x * cell
                                y = self.maze_rect.y + step_y * cell
                                age = current_step - i
                                if age < 5:
                                    alpha = int(150 * (1 - age / 5))
                                    overlay = pygame.Surface((cell, cell), pygame.SRCALPHA)
                                    overlay.fill((200, 100, 100, alpha))
                                    self.screen.blit(overlay, (x, y))

        # Draw particles (vẽ SAU maze và player để particles nằm trên cùng)
        if self.generating_maze:
            self.particle_system.draw(self.screen)

        # window buttons - vẽ cuối cùng để đảm bảo không bị đè
        for b in (self.btn_min, self.btn_max, self.btn_close):
            b.draw(self.screen)

        # history modal
        self.modal_history.draw(self.screen, self.window_rect, self.font_ui, self.font_small)

        # victory modal
        self.modal_victory.draw(self.screen, self.window_rect, self.font_title, self.font_ui)
        
        # game complete modal
        if self.showing_game_complete:
            self.modal_game_complete.draw(self.screen, self.window_rect, self.font_title, self.font_ui)

    def get_cached_surface(self, key, creator_func):
        """Cache system for expensive surface operations"""
        if key not in self._surface_cache:
            self._surface_cache[key] = creator_func()
        return self._surface_cache[key]

    def clear_size_dependent_cache(self):
        """Clear cache when window size changes"""
        self._image_cache.clear()
        self._surface_cache.clear()
        self._bg_cache.clear()

    def get_scaled_image(self, image, size):
        """Cache scaled images to avoid repeated scaling"""
        cache_key = (id(image), size)
        if cache_key not in self._image_cache:
            self._image_cache[cache_key] = pygame.transform.smoothscale(image, size)
        return self._image_cache[cache_key]

    def get_scaled_background(self, image, size):
        """Cache scaled backgrounds"""
        cache_key = (id(image), size)
        if cache_key not in self._bg_cache:
            self._bg_cache[cache_key] = pygame.transform.smoothscale(image, size)
        return self._bg_cache[cache_key]

    # ---- Performance optimization methods
    def update_performance_mode(self):
        """Monitor FPS and automatically enable performance optimizations when needed"""
        current_time = time.time()

        # Calculate current FPS
        if hasattr(self, 'last_frame_time'):
            frame_time = current_time - self.last_frame_time
            if frame_time > 0:
                fps = 1.0 / frame_time
                self.fps_samples.append(fps)

                # Keep only last 30 samples for rolling average
                if len(self.fps_samples) > 30:
                    self.fps_samples.pop(0)

                avg_fps = sum(self.fps_samples) / len(self.fps_samples)

                # Enable performance mode if FPS drops below threshold
                if avg_fps < MIN_FPS_THRESHOLD and not self.performance_mode:
                    self.performance_mode = True
                    self.current_fps = PERFORMANCE_FPS

                # Disable performance mode if FPS is stable above threshold
                elif avg_fps > MIN_FPS_THRESHOLD + 10 and self.performance_mode:
                    self.performance_mode = False
                    self.current_fps = FPS

        self.last_frame_time = current_time

        # Enable additional optimizations for very small windows
        window_area = self.window_rect.w * self.window_rect.h
        small_window_threshold = 800 * 600  # Small window threshold

        self.skip_expensive_effects = (
            self.performance_mode or
            window_area < small_window_threshold or
            self.cell_size < MIN_CELL_SIZE_FOR_DETAILS
        )

    def should_skip_frame(self):
        """Determine if we should skip this frame for performance"""
        if not self.performance_mode:
            return False

        self.frame_skip_counter += 1
        # Skip every 2nd frame in performance mode
        if self.frame_skip_counter >= 2:
            self.frame_skip_counter = 0
            return False
        return True

    def get_optimized_maze_surface(self):
        """Create a pre-rendered maze surface for better performance"""
        if self._maze_surface is None or self._maze_surface_dirty:
            # Create surface for the entire maze
            maze_surface = pygame.Surface(self.maze_rect.size)

            cell = self.cell_size

            # Draw floor tiles
            for r in range(MAZE_ROWS):
                for c in range(MAZE_COLS):
                    x = c * cell
                    y = r * cell
                    idx = self.floor_map[r][c]
                    maze_surface.blit(self.scaled_floor_tiles[idx], (x, y))

            # Draw walls
            for r in range(MAZE_ROWS):
                for c in range(MAZE_COLS):
                    if self.maze[r][c].status == 0:
                        x = c * cell
                        y = r * cell
                        maze_surface.blit(self.scaled_wall_tile, (x, y))

            self._maze_surface = maze_surface
            self._maze_surface_dirty = False

        return self._maze_surface

    def invalidate_maze_surface(self):
        """Mark maze surface as dirty when maze changes"""
        self._maze_surface_dirty = True
        self._ui_surface_dirty = True

    def draw_optimized_ui(self, sidebar):
        """Draw UI elements with performance optimizations"""
        if self._ui_surface is None or self._ui_surface_dirty:
            # Pre-render UI elements that don't change often
            scale_factor = min(self.window_rect.w / 1920, self.window_rect.h / 1080)
            scale_factor = max(0.5, min(1.0, scale_factor))

            ui_surface = pygame.Surface(sidebar.size, pygame.SRCALPHA)

            # Draw sidebar background
            draw_glass_card(ui_surface, pygame.Rect(0, 0, sidebar.w, sidebar.h),
                          radius=22, bg=(18,24,18,190), border=(110,150,110), border_alpha=70)

            self._ui_surface = ui_surface
            self._ui_surface_dirty = False

        return self._ui_surface

    def draw_simplified_effects(self):
        """Draw simplified visual effects for performance mode"""
        if self.skip_expensive_effects:
            # Use simple rectangles instead of complex shadows and effects
            return True
        return False

    def draw_transition(self):
        """Vẽ hiệu ứng chuyển cảnh circle 2 pha"""
        if not self.transitioning or not self.transition_surface_from or not self.transition_surface_to:
            return
        
        t = self.transition_progress
        max_radius = int(((self.window_rect.w ** 2 + self.window_rect.h ** 2) ** 0.5) / 2)
        center = (self.window_rect.w // 2, self.window_rect.h // 2)
        
        # Vẽ nền đen
        self.screen.fill((0, 0, 0))
        
        if t < 0.5:
            # Phase 1: Thu nhỏ màn hình cũ vào giữa
            phase_t = t * 2  # Map 0.0-0.5 -> 0.0-1.0
            phase_eased = phase_t * phase_t * (3.0 - 2.0 * phase_t)  # Smoothstep
            current_radius = int(max_radius * (1 - phase_eased))
            
            if current_radius > 0:
                mask_surface = pygame.Surface((self.window_rect.w, self.window_rect.h))
                mask_surface.fill((0, 0, 0))
                pygame.draw.circle(mask_surface, (255, 255, 255), center, current_radius)
                
                temp_surface = self.transition_surface_from.copy()
                temp_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self.screen.blit(temp_surface, (0, 0))
        else:
            # Phase 2: Mở rộng màn hình mới từ giữa
            phase_t = (t - 0.5) * 2  # Map 0.5-1.0 -> 0.0-1.0
            phase_eased = phase_t * phase_t * (3.0 - 2.0 * phase_t)  # Smoothstep
            current_radius = int(max_radius * phase_eased)
            
            if current_radius > 0:
                mask_surface = pygame.Surface((self.window_rect.w, self.window_rect.h))
                mask_surface.fill((0, 0, 0))
                pygame.draw.circle(mask_surface, (255, 255, 255), center, current_radius)
                
                temp_surface = self.transition_surface_to.copy()
                temp_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self.screen.blit(temp_surface, (0, 0))

    def run(self):
        while self.running:
            # Use adaptive FPS based on performance mode
            target_fps = self.current_fps if hasattr(self, 'current_fps') else FPS
            dt = self.clock.tick(target_fps)/1000.0

            self.handle_events()
            self.update(dt)

            # Draw transition or normal screens
            if self.transitioning:
                self.draw_transition()
            elif self.state=="start":
                self.draw_start()
            else:
                self.draw_game()

            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    App().run()