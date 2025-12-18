# 🐵 Monkey's Treasure - Maze Solver Game

Trò chơi giải mê cung với chú khỉ tìm kho báu, sử dụng các thuật toán AI thông minh. Game được phát triển bằng Python và Pygame với giao diện đồ họa hấp dẫn theo phong cách rừng nhiệt đới.

## 📋 Mục lục
- [Giới thiệu](#-giới-thiệu)
- [Tính năng](#-tính-năng)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Cài đặt](#-cài-đặt)
- [Hướng dẫn chơi](#-hướng-dẫn-chơi)
- [Thuật toán](#-thuật-toán)
- [Tài liệu tham khảo](#-tài-liệu-tham-khảo)

## 🎯 Giới thiệu

**Monkey's Treasure** là game giải mê cung kết hợp giải trí và học thuật. Người chơi điều khiển chú khỉ di chuyển qua các mê cung được sinh ngẫu nhiên để tìm kho báu (quả chuối vàng). Game tích hợp nhiều thuật toán AI để sinh mê cung và tìm đường đi tối ưu.

### Điểm nổi bật
- 🎮 **3 cấp độ** với độ khó tăng dần
- 🪙 **Hệ thống xu** thưởng khi hoàn thành nhanh
- 🤖 **Auto-play** với chi phí xu tăng dần
- ⏱️ **Giới hạn thời gian** và số bước
- 🏆 **Mở khóa level** theo tiến trình

## ✨ Tính năng

### 🎮 Hệ thống Level
| Level | Kích thước | Thời gian | Bước dư |
|-------|-----------|-----------|---------|
| 1 | 13×7 | 30 giây | +10 bước |
| 2 | 19×13 | 90 giây | +5 bước |
| 3 | 25×19 | 75 giây | +3 bước |

### 🪙 Hệ thống Xu (Coin)
- **Nhận xu**: Hoàn thành level với thời gian còn lại > 60% thời gian giới hạn
- **Chi tiêu xu**: Sử dụng tính năng Auto-play
- **Chi phí Auto-play**: 
  - Lần 1: 5 xu
  - Lần 2: 10 xu  
  - Lần 3: 15 xu
  - ... (tăng 5 xu mỗi lần)

### 🏗️ Thuật toán sinh mê cung
- **DFS** (Depth-First Search) - Sinh mê cung theo chiều sâu
- **Kruskal** - Sử dụng cấu trúc Union-Find
- **Binary Tree** - Mê cung có cấu trúc cây nhị phân
- **Wilson** - Thuật toán random walk
- **Recursive Division** - Chia đệ quy tạo tường

### 🎯 Thuật toán giải mê cung
- **BFS** (Breadth-First Search) - Tìm đường đi ngắn nhất
- **DFS** (Depth-First Search) - Tìm đường theo chiều sâu
- **UCS** (Uniform Cost Search) - Tìm kiếm chi phí đồng nhất
- **A*** (A-Star) - Tối ưu với heuristic Manhattan
- **Bidirectional Search** - Tìm kiếm hai chiều

### 🎨 Giao diện
- Thiết kế jungle theme với đồ họa sinh động
- Hiệu ứng particle cho chiến thắng/thất bại
- Animation mượt mà với FPS tối ưu
- Glassmorphism UI hiện đại
- Responsive với chế độ fullscreen

## 📁 Cấu trúc dự án

```
MazeSolverGame/
├── main.py                    # Entry point - Khởi chạy game
├── config.py                  # Cấu hình game (constants, settings)
├── BÁO_CÁO_ĐỒ_ÁN.md          # Báo cáo chi tiết đồ án
│
├── Model/                     # Tầng Model - Dữ liệu & Logic
│   ├── __init__.py           # Export các model
│   ├── node_cell.py          # Class Cell cho ô mê cung
│   ├── maze_generator.py     # Các thuật toán sinh mê cung
│   └── maze_solver.py        # Các thuật toán giải mê cung
│
├── View/                      # Tầng View - Giao diện người dùng
│   ├── __init__.py           # Class App chính (game logic)
│   ├── utils.py              # Hàm tiện ích (load image, draw,...)
│   ├── particle.py           # Hệ thống particle effects
│   │
│   ├── components/           # UI Components
│   │   ├── button.py         # Component Button
│   │   ├── dropdown.py       # Component Dropdown menu
│   │   ├── modals.py         # Modal History & Victory
│   │   └── level_modals.py   # Modal Level Select & Game Complete
│   │
│   ├── sprites/              # Game sprites
│   │   └── __init__.py       # FloatingBanana, MonkeyIdle
│   │
│   └── assets/               # Tài nguyên đồ họa
│       ├── bg_jungle.png     # Background gameplay
│       ├── bg_start.png      # Background menu
│       ├── monkey.png        # Sprite khỉ
│       ├── banana_rainbow.png # Sprite chuối (đích)
│       ├── tile_wall.png     # Texture tường
│       ├── button/           # Hình ảnh các nút
│       ├── box/              # UI boxes (time, step, algo)
│       ├── tiles/            # Floor tiles
│       └── monkey_stand/     # Idle animation frames
│
└── Controller/                # Tầng Controller
    ├── __init__.py
    └── game_controller.py    # Xử lý input & game flow
```

## 🔧 Cài đặt

### Yêu cầu hệ thống
- **Python**: 3.9 trở lên
- **Pygame**: 2.0 trở lên
- **RAM**: 512MB+
- **Màn hình**: 1024x768 trở lên

### Cài đặt dependencies
```bash
pip install pygame
```

### Clone và chạy
```bash
# Clone từ GitHub
git clone https://github.com/SolosamH/ITproject.git
cd ITproject/MazeSolverGame

# Chạy game
python main.py
```

## 🎮 Hướng dẫn chơi

### Điều khiển
| Phím | Chức năng |
|------|-----------|
| ↑ / W | Di chuyển lên |
| ↓ / S | Di chuyển xuống |
| ← / A | Di chuyển trái |
| → / D | Di chuyển phải |
| ESC | Quay lại menu |

### Luật chơi
1. **Mục tiêu**: Điều khiển khỉ đến quả chuối vàng
2. **Thời gian**: Hoàn thành trước khi hết giờ
3. **Số bước**: Không vượt quá giới hạn cho phép
4. **Mở khóa**: Hoàn thành level trước để mở level sau
5. **Thưởng xu**: Hoàn thành nhanh (>60% thời gian còn lại) được thưởng xu

### Tính năng Auto-play
- Nhấn nút **Auto** để AI tự động giải mê cung
- Chi phí xu tăng theo số lần sử dụng
- Hữu ích khi bị kẹt hoặc muốn xem đường đi tối ưu

## 🧠 Thuật toán

### Sinh mê cung
| Thuật toán | Đặc điểm | Độ phức tạp |
|------------|----------|-------------|
| DFS | Đường đi dài, ít rẽ nhánh | O(V + E) |
| Kruskal | Phân bố đều, nhiều ngã rẽ | O(E log E) |
| Binary Tree | Đơn giản, bias về góc | O(V) |
| Wilson | Hoàn toàn ngẫu nhiên | O(V²) trung bình |
| Recursive Division | Cấu trúc phòng, đường thẳng | O(V log V) |

### Giải mê cung
| Thuật toán | Đặc điểm | Tối ưu | Độ phức tạp |
|------------|----------|--------|-------------|
| BFS | Tìm đường ngắn nhất | ✅ | O(V + E) |
| DFS | Nhanh, không tối ưu | ❌ | O(V + E) |
| UCS | Chi phí đồng nhất | ✅ | O(V + E log V) |
| A* | Heuristic Manhattan | ✅ | O(E) |
| Bidirectional | Tìm từ 2 đầu | ✅ | O(b^(d/2)) |

### Hiệu năng thực tế (mê cung 25×19)
```
BFS:           ~0.010s | Nodes: ~500
DFS:           ~0.008s | Nodes: ~300
UCS:           ~0.012s | Nodes: ~450
A*:            ~0.007s | Nodes: ~200 (nhanh nhất)
Bidirectional: ~0.009s | Nodes: ~350
```

## 📊 Screenshots

### Màn hình chính
- Menu Start với animation khỉ idle
- Background rừng nhiệt đới

### Gameplay
- Mê cung với texture tiles
- Sidebar hiển thị thông tin (time, steps, coins)
- Dropdown chọn thuật toán

### Kết thúc game
- Modal Victory với confetti effect
- Modal Game Over khi hết thời gian/bước
- Modal hoàn thành tất cả level

## 🛠️ Công nghệ sử dụng

- **Python 3.13** - Ngôn ngữ lập trình
- **Pygame 2.6** - Framework game 2D
- **MVC Pattern** - Kiến trúc phần mềm
- **Git** - Quản lý phiên bản

## 📜 License

Dự án học tập - Môn Trí tuệ nhân tạo

## 👥 Thông tin

- **Repository**: [SolosamH/ITproject](https://github.com/SolosamH/ITproject)
- **Ngôn ngữ**: Python
- **Framework**: Pygame
- **Cập nhật**: Tháng 12/2025

## 📚 Tài liệu tham khảo

- [Maze Generation Algorithms - Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [A* Search Algorithm - Wikipedia](https://en.wikipedia.org/wiki/A*_search_algorithm)
- [Pygame Documentation](https://www.pygame.org/docs/)
- [Python Documentation](https://docs.python.org/3/)

---

**🎮 Chúc bạn chơi game vui vẻ!**
