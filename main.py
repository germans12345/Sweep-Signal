import pygame
import random
import math
import os

pygame.init()

# =========================
# 1. 音频初始化
# =========================
sound_enabled = True
try:
    pygame.mixer.init()
except Exception as e:
    print("音频系统初始化失败：", e)
    sound_enabled = False

# =========================
# 2. 基本参数（竖屏 + 黑底）
# =========================
WIDTH = 720
HEIGHT = 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Project 4 - Sweep Signal Music Version")

clock = pygame.time.Clock()

# =========================
# 3. 颜色（暖色演出版）
# =========================
BG_COLOR = (0, 0, 0)

RING_COLOR_1 = (255, 180, 70)
RING_COLOR_2 = (255, 90, 50)

TIMER_WHITE = (255, 245, 230)
TIMER_WARNING = (255, 120, 100)

UI_WHITE = (245, 235, 220)
GAP_MARK_COLOR = (255, 250, 230)

SUCCESS_FLASH_COLOR = (255, 235, 150)

START_TEXT_COLOR = (245, 240, 230)
SUB_TEXT_COLOR = (185, 170, 155)
RULE_TEXT_COLOR = (255, 215, 120)

FREEZE_TEXT_COLOR = (120, 220, 255)
SUCCESS_TEXT_COLOR = (255, 240, 130)

BALL_COLOR_POOL = [
    (255, 240, 60),
    (255, 210, 70),
    (255, 170, 70),
    (255, 130, 60),
    (255, 90, 90),
    (255, 90, 150),
    (255, 120, 220),
    (220, 110, 255),
    (170, 120, 255),
    (120, 160, 255),
    (90, 220, 255),
    (80, 255, 210),
    (120, 255, 140),
]

# =========================
# 4. 场地参数
# =========================
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2 - 30

RING_RADIUS = 185
RING_THICKNESS = 12

BALL_RADIUS = 12
BALL_SPEED = 4.2

GAP_SIZE_DEG = 36
COUNTDOWN_SECONDS = 5.0
SPAWN_SAFE_MARGIN = 4

# =========================
# 5. 项目4核心：摆动缺口
# =========================
gap_base_angle = 0.0
gap_center_angle = 0.0
gap_swing_direction = 1

GAP_SWING_RANGE_DEG = 70
GAP_SWING_SPEED_MIN_DEG = 80
GAP_SWING_SPEED_MAX_DEG = 220

GAP_EDGE_PAUSE_FRAMES = 12
ROUND_END_PAUSE_MS = 3000

# =========================
# 6. 游戏状态
# =========================
active_ball = None
frozen_balls = []
ball_index = 0

game_over = False
game_success = False

ball_start_time = 0

freeze_effects = []
success_flash_timer = 0

waiting_to_start = True
round_end_time = None

center_message = ""
center_message_color = UI_WHITE
center_message_timer = 0
CENTER_MESSAGE_MAX_TIMER = 36

gap_pause_timer = 0

# =========================
# 7. 字体
# =========================
title_font = pygame.font.Font(None, 36)
title_font.set_bold(True)

sub_font = pygame.font.Font(None, 24)

rule_font = pygame.font.Font(None, 30)
rule_font.set_bold(True)

small_font = pygame.font.Font(None, 26)

center_message_font = pygame.font.Font(None, 84)
center_message_font.set_bold(True)

success_text_font = pygame.font.Font(None, 96)
success_text_font.set_bold(True)

# =========================
# 8. 音效加载
# =========================
freeze_sound = None
success_sound = None
ring_hit_sound = None
frozen_hit_sound = None

def load_sound(filename, volume=0.4):
    if not sound_enabled:
        return None

    if not os.path.exists(filename):
        print("没找到音效文件：", filename)
        return None

    try:
        sound = pygame.mixer.Sound(filename)
        sound.set_volume(volume)
        print("音效加载成功：", filename)
        return sound
    except Exception as e:
        print("音效加载失败：", filename, e)
        return None

freeze_sound = load_sound("freeze.wav", 0.40)
success_sound = load_sound("success.wav", 0.50)

# 方案A：轻碰撞音效
ring_hit_sound = load_sound("ring_hit.wav", 0.22)
frozen_hit_sound = load_sound("frozen_hit.wav", 0.18)

def play_sound(sound_obj):
    if sound_obj is not None:
        sound_obj.play()

# =========================
# 9. 碰撞长音乐系统（核心）
# =========================
COLLISION_BGM_FILE = "collision_bgm.ogg"

# 每次碰撞推动长音乐播放多少秒
MUSIC_SEGMENT_SECONDS = 0.35

# 你的音乐总长度，按实际改
MUSIC_TOTAL_LENGTH_SECONDS =35.0

music_position = 0.0
music_is_playing_segment = False
music_segment_start_tick = 0
music_segment_start_position = 0.0

collision_bgm_loaded = False

def load_collision_bgm():
    global collision_bgm_loaded

    if not sound_enabled:
        print("音频系统未启用")
        collision_bgm_loaded = False
        return

    if not os.path.exists(COLLISION_BGM_FILE):
        print("没找到音乐文件：", COLLISION_BGM_FILE)
        collision_bgm_loaded = False
        return

    try:
        pygame.mixer.music.load(COLLISION_BGM_FILE)
        pygame.mixer.music.set_volume(0.62)
        collision_bgm_loaded = True
        print("长音乐加载成功：", COLLISION_BGM_FILE)
    except Exception as e:
        collision_bgm_loaded = False
        print("长音乐加载失败：", e)

def stop_collision_music_immediately():
    global music_is_playing_segment

    if sound_enabled and collision_bgm_loaded:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    music_is_playing_segment = False

def normalize_music_position():
    global music_position

    if MUSIC_TOTAL_LENGTH_SECONDS <= 0:
        music_position = 0.0
        return

    while music_position >= MUSIC_TOTAL_LENGTH_SECONDS:
        music_position -= MUSIC_TOTAL_LENGTH_SECONDS

    while music_position < 0:
        music_position += MUSIC_TOTAL_LENGTH_SECONDS

def trigger_collision_music():
    global music_is_playing_segment
    global music_segment_start_tick
    global music_segment_start_position
    global music_position

    if not sound_enabled:
        return

    if not collision_bgm_loaded:
        return

    if music_is_playing_segment:
        return

    normalize_music_position()

    try:
        pygame.mixer.music.play(loops=0, start=music_position)
        music_is_playing_segment = True
        music_segment_start_tick = pygame.time.get_ticks()
        music_segment_start_position = music_position
    except Exception as e:
        print("长音乐开始播放失败：", e)
        music_is_playing_segment = False

def update_collision_music():
    global music_is_playing_segment
    global music_position

    if not sound_enabled:
        return

    if not collision_bgm_loaded:
        return

    if not music_is_playing_segment:
        return

    now = pygame.time.get_ticks()
    elapsed_sec = (now - music_segment_start_tick) / 1000.0

    if elapsed_sec >= MUSIC_SEGMENT_SECONDS:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        music_position = music_segment_start_position + MUSIC_SEGMENT_SECONDS
        normalize_music_position()
        music_is_playing_segment = False

# =========================
# 10. 方案A：碰撞音效冷却
# =========================
ring_hit_cooldown_ms = 45
frozen_hit_cooldown_ms = 55

last_ring_hit_tick = -999999
last_frozen_hit_tick = -999999

def play_ring_hit_sound():
    global last_ring_hit_tick

    now = pygame.time.get_ticks()
    if now - last_ring_hit_tick < ring_hit_cooldown_ms:
        return

    last_ring_hit_tick = now
    play_sound(ring_hit_sound)

def play_frozen_hit_sound():
    global last_frozen_hit_tick

    now = pygame.time.get_ticks()
    if now - last_frozen_hit_tick < frozen_hit_cooldown_ms:
        return

    last_frozen_hit_tick = now
    play_sound(frozen_hit_sound)

# =========================
# 11. 七段数码管
# =========================
DIGIT_MAP = {
    "0": [1, 1, 1, 1, 1, 1, 0],
    "1": [0, 1, 1, 0, 0, 0, 0],
    "2": [1, 1, 0, 1, 1, 0, 1],
    "3": [1, 1, 1, 1, 0, 0, 1],
    "4": [0, 1, 1, 0, 0, 1, 1],
    "5": [1, 0, 1, 1, 0, 1, 1],
    "6": [1, 0, 1, 1, 1, 1, 1],
    "7": [1, 1, 1, 0, 0, 0, 0],
    "8": [1, 1, 1, 1, 1, 1, 1],
    "9": [1, 1, 1, 1, 0, 1, 1],
}

def draw_segment_digit(surface, x, y, scale, char, color):
    if char not in DIGIT_MAP:
        return 0

    w = int(44 * scale)
    h = int(78 * scale)
    t = max(2, int(7 * scale))

    rects = [
        pygame.Rect(x + t,     y,              w - 2 * t, t),
        pygame.Rect(x + w - t, y + t,          t, h // 2 - t),
        pygame.Rect(x + w - t, y + h // 2,     t, h // 2 - t),
        pygame.Rect(x + t,     y + h - t,      w - 2 * t, t),
        pygame.Rect(x,         y + h // 2,     t, h // 2 - t),
        pygame.Rect(x,         y + t,          t, h // 2 - t),
        pygame.Rect(x + t,     y + h // 2 - t // 2, w - 2 * t, t),
    ]

    for on, rect in zip(DIGIT_MAP[char], rects):
        if on:
            pygame.draw.rect(surface, color, rect, border_radius=max(1, t // 2))

    return w

def draw_number_string(surface, text, center_x, center_y, scale, color, spacing=10):
    total_width = 0

    for ch in text:
        if ch.isdigit():
            total_width += int(44 * scale)
        else:
            total_width += int(20 * scale)

    total_width += spacing * (len(text) - 1)
    start_x = center_x - total_width // 2

    x = start_x
    for i, ch in enumerate(text):
        if ch.isdigit():
            w = draw_segment_digit(surface, x, center_y - int(39 * scale), scale, ch, color)
            x += w
        else:
            x += int(20 * scale)

        if i != len(text) - 1:
            x += spacing

# =========================
# 12. 工具函数
# =========================
def normalize_angle(angle):
    while angle < 0:
        angle += 2 * math.pi
    while angle >= 2 * math.pi:
        angle -= 2 * math.pi
    return angle

def angle_diff(a, b):
    d = abs(a - b)
    return min(d, 2 * math.pi - d)

def point_distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

def get_remaining_time():
    current_time = pygame.time.get_ticks()
    elapsed = (current_time - ball_start_time) / 1000.0
    return COUNTDOWN_SECONDS - elapsed

def get_display_countdown_number():
    remaining = max(0.0, get_remaining_time())
    if remaining <= 0:
        return "0"
    return str(math.ceil(remaining))

def get_random_ball_color(exclude_colors=None):
    if exclude_colors is None:
        exclude_colors = []

    candidates = [c for c in BALL_COLOR_POOL if c not in exclude_colors]
    if not candidates:
        candidates = BALL_COLOR_POOL[:]

    return random.choice(candidates)

def draw_center_text(text, font, color, center_x, center_y):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(center_x, center_y))
    screen.blit(surf, rect)

def set_center_message(text, color, duration):
    global center_message, center_message_color, center_message_timer
    center_message = text
    center_message_color = color
    center_message_timer = duration

# =========================
# 13. 缺口摆动
# =========================
def reset_round_gap():
    global gap_base_angle, gap_center_angle, gap_swing_direction, gap_pause_timer

    gap_base_angle = random.uniform(0, 2 * math.pi)
    gap_center_angle = gap_base_angle
    gap_swing_direction = random.choice([-1, 1])
    gap_pause_timer = 0

def get_gap_swing_speed_deg():
    remaining = max(0.0, get_remaining_time())
    progress = 1.0 - (remaining / COUNTDOWN_SECONDS)
    eased_progress = progress * progress

    speed_deg = GAP_SWING_SPEED_MIN_DEG + (
        GAP_SWING_SPEED_MAX_DEG - GAP_SWING_SPEED_MIN_DEG
    ) * eased_progress

    return speed_deg

def update_gap_swing():
    global gap_center_angle, gap_swing_direction, gap_pause_timer

    if gap_pause_timer > 0:
        gap_pause_timer -= 1
        return

    current_speed_deg = get_gap_swing_speed_deg()
    move_rad = math.radians(current_speed_deg) / 60.0

    old_angle = gap_center_angle
    new_angle = gap_center_angle + move_rad * gap_swing_direction

    max_offset = math.radians(GAP_SWING_RANGE_DEG)
    offset = angle_diff(new_angle, gap_base_angle)

    if offset > max_offset:
        gap_center_angle = old_angle
        gap_swing_direction *= -1
        gap_pause_timer = GAP_EDGE_PAUSE_FRAMES
    else:
        gap_center_angle = new_angle

    gap_center_angle = normalize_angle(gap_center_angle)

# =========================
# 14. 安全出生点
# =========================
def find_safe_spawn_position(max_attempts=120):
    for _ in range(max_attempts):
        spawn_r = random.randint(0, 40)
        spawn_angle = random.uniform(0, 2 * math.pi)

        x = CENTER_X + math.cos(spawn_angle) * spawn_r
        y = CENTER_Y + math.sin(spawn_angle) * spawn_r

        ok = True
        for frozen in frozen_balls:
            need_dist = BALL_RADIUS + frozen["radius"] + SPAWN_SAFE_MARGIN
            if point_distance(x, y, frozen["x"], frozen["y"]) < need_dist:
                ok = False
                break

        if ok:
            return x, y

    return CENTER_X, CENTER_Y

# =========================
# 15. 创建新球
# =========================
def create_new_ball():
    global ball_index, ball_start_time

    ball_index += 1
    ball_start_time = pygame.time.get_ticks()

    x, y = find_safe_spawn_position()

    move_angle = random.uniform(0, 2 * math.pi)
    vx = math.cos(move_angle) * BALL_SPEED
    vy = math.sin(move_angle) * BALL_SPEED

    init_color = get_random_ball_color()

    return {
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "radius": BALL_RADIUS,
        "color": init_color,
        "recent_colors": [init_color]
    }

# =========================
# 16. 新一轮
# =========================
def start_new_round():
    global active_ball, frozen_balls, ball_index
    global game_over, game_success
    global freeze_effects, success_flash_timer
    global round_end_time
    global center_message, center_message_timer

    frozen_balls = []
    ball_index = 0

    game_over = False
    game_success = False

    freeze_effects = []
    success_flash_timer = 0
    round_end_time = None

    center_message = ""
    center_message_timer = 0

    # 新一轮只停止当前小段，不清空音乐推进进度
    stop_collision_music_immediately()

    reset_round_gap()
    active_ball = create_new_ball()

# =========================
# 17. 成功判定
# =========================
def check_ball_escape(ball):
    dx = ball["x"] - CENTER_X
    dy = ball["y"] - CENTER_Y
    dist = math.hypot(dx, dy)

    angle = normalize_angle(math.atan2(dy, dx))
    gap_half = math.radians(GAP_SIZE_DEG / 2)

    passed_outside = dist > (RING_RADIUS + RING_THICKNESS / 2 + ball["radius"] + 8)
    in_gap = angle_diff(angle, gap_center_angle) <= gap_half

    return passed_outside and in_gap

# =========================
# 18. 活动球移动 + 圆环碰撞
# =========================
def move_active_ball(ball):
    ball["x"] += ball["vx"]
    ball["y"] += ball["vy"]

    dx = ball["x"] - CENTER_X
    dy = ball["y"] - CENTER_Y
    dist = math.hypot(dx, dy)

    if dist == 0:
        dist = 0.0001

    angle = normalize_angle(math.atan2(dy, dx))
    gap_half = math.radians(GAP_SIZE_DEG / 2)
    in_gap = angle_diff(angle, gap_center_angle) <= gap_half

    boundary_radius = RING_RADIUS - RING_THICKNESS / 2

    if dist + ball["radius"] >= boundary_radius:
        if in_gap:
            return
        else:
            nx = dx / dist
            ny = dy / dist

            target_dist = boundary_radius - ball["radius"] - 1
            ball["x"] = CENTER_X + nx * target_dist
            ball["y"] = CENTER_Y + ny * target_dist

            vx = ball["vx"]
            vy = ball["vy"]
            dot = vx * nx + vy * ny

            ball["vx"] = vx - 2 * dot * nx
            ball["vy"] = vy - 2 * dot * ny

            exclude_colors = [ball["color"]] + ball["recent_colors"][-2:]
            new_color = get_random_ball_color(exclude_colors)
            ball["color"] = new_color
            ball["recent_colors"].append(new_color)

            if len(ball["recent_colors"]) > 3:
                ball["recent_colors"].pop(0)

            # 方案A：轻碰撞音效 + 长音乐推进
            play_ring_hit_sound()
            trigger_collision_music()

# =========================
# 19. 与冻结球碰撞
# =========================
def handle_collision_with_frozen_balls(ball):
    collided = False

    for frozen in frozen_balls:
        dx = ball["x"] - frozen["x"]
        dy = ball["y"] - frozen["y"]
        dist = math.hypot(dx, dy)

        min_dist = ball["radius"] + frozen["radius"]

        if dist == 0:
            angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(angle)
            dy = math.sin(angle)
            dist = 0.0001

        if dist < min_dist:
            collided = True

            nx = dx / dist
            ny = dy / dist

            push_dist = min_dist - dist + 1.0
            ball["x"] += nx * push_dist
            ball["y"] += ny * push_dist

            vx = ball["vx"]
            vy = ball["vy"]
            dot = vx * nx + vy * ny

            if dot < 0:
                ball["vx"] = vx - 2 * dot * nx
                ball["vy"] = vy - 2 * dot * ny
            else:
                ball["vx"] += nx * 0.2
                ball["vy"] += ny * 0.2

    if collided:
        # 方案A：轻碰撞音效 + 长音乐推进
        play_frozen_hit_sound()
        trigger_collision_music()

# =========================
# 20. 冻结与特效
# =========================
def add_freeze_effect(x, y, color):
    freeze_effects.append({
        "x": x,
        "y": y,
        "color": color,
        "timer": 0,
        "max_timer": 22
    })

def update_freeze_effects():
    alive = []
    for effect in freeze_effects:
        effect["timer"] += 1
        if effect["timer"] <= effect["max_timer"]:
            alive.append(effect)
    freeze_effects[:] = alive

def update_center_message():
    global center_message_timer, center_message
    if center_message_timer > 0:
        center_message_timer -= 1
        if center_message_timer <= 0:
            center_message = ""

def freeze_current_ball():
    global active_ball

    frozen_balls.append({
        "x": active_ball["x"],
        "y": active_ball["y"],
        "radius": active_ball["radius"],
        "color": active_ball["color"]
    })

    add_freeze_effect(active_ball["x"], active_ball["y"], active_ball["color"])
    play_sound(freeze_sound)

    set_center_message("FROZEN", FREEZE_TEXT_COLOR, CENTER_MESSAGE_MAX_TIMER)
    active_ball = create_new_ball()

# =========================
# 21. 圆环与缺口
# =========================
def draw_ring_with_gap():
    gap_half = math.radians(GAP_SIZE_DEG / 2)

    angle = 0
    step = math.radians(2)

    while angle < 2 * math.pi:
        next_angle = angle + step
        mid = normalize_angle((angle + next_angle) / 2)

        if angle_diff(mid, gap_center_angle) > gap_half:
            t = (math.cos(mid) + 1) / 2
            r = int(RING_COLOR_1[0] * (1 - t) + RING_COLOR_2[0] * t)
            g = int(RING_COLOR_1[1] * (1 - t) + RING_COLOR_2[1] * t)
            b = int(RING_COLOR_1[2] * (1 - t) + RING_COLOR_2[2] * t)
            color = (r, g, b)

            p1 = (
                int(CENTER_X + math.cos(angle) * RING_RADIUS),
                int(CENTER_Y + math.sin(angle) * RING_RADIUS)
            )
            p2 = (
                int(CENTER_X + math.cos(next_angle) * RING_RADIUS),
                int(CENTER_Y + math.sin(next_angle) * RING_RADIUS)
            )

            pygame.draw.line(screen, color, p1, p2, RING_THICKNESS)

        angle = next_angle

def draw_gap_markers():
    gap_half = math.radians(GAP_SIZE_DEG / 2)
    a1 = gap_center_angle - gap_half
    a2 = gap_center_angle + gap_half

    for a in [a1, a2]:
        x = int(CENTER_X + math.cos(a) * RING_RADIUS)
        y = int(CENTER_Y + math.sin(a) * RING_RADIUS)
        pygame.draw.circle(screen, GAP_MARK_COLOR, (x, y), 4)

# =========================
# 22. UI
# =========================
def draw_frozen_ball_icons():
    start_x = 35
    y = 40
    gap = 18

    max_show = 20
    count = min(len(frozen_balls), max_show)

    for i in range(count):
        pygame.draw.circle(screen, UI_WHITE, (start_x + i * gap, y), 6, 1)

    if len(frozen_balls) > max_show:
        extra_x = start_x + max_show * gap
        pygame.draw.circle(screen, UI_WHITE, (extra_x, y), 2)
        pygame.draw.circle(screen, UI_WHITE, (extra_x + 8, y), 2)
        pygame.draw.circle(screen, UI_WHITE, (extra_x + 16, y), 2)

def draw_ball_index():
    text = str(ball_index)
    draw_number_string(screen, text, WIDTH - 70, 46, 0.55, UI_WHITE, spacing=6)

def draw_countdown():
    text = get_display_countdown_number()
    remaining = max(0.0, get_remaining_time())

    if remaining <= 2.0:
        main_color = TIMER_WARNING
        shadow_color = (255, 120, 100, 45)
    else:
        main_color = TIMER_WHITE
        shadow_color = (255, 240, 220, 35)

    temp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    draw_number_string(temp, text, CENTER_X, CENTER_Y, 2.95, shadow_color, spacing=14)
    screen.blit(temp, (0, 0))

    draw_number_string(screen, text, CENTER_X, CENTER_Y, 2.7, main_color, spacing=14)

def draw_project_rule_text():
    direction_text = "RIGHT" if gap_swing_direction == 1 else "LEFT"
    text = f"PROJECT 4  |  SWEEP SIGNAL  |  {direction_text}"
    surf = rule_font.render(text, True, RULE_TEXT_COLOR)
    rect = surf.get_rect(center=(CENTER_X, 92))
    screen.blit(surf, rect)

def draw_status_text():
    if game_over:
        return

    remaining = max(0.0, get_remaining_time())
    current_speed = int(get_gap_swing_speed_deg())

    music_percent = 0
    if MUSIC_TOTAL_LENGTH_SECONDS > 0:
        music_percent = int((music_position / MUSIC_TOTAL_LENGTH_SECONDS) * 100)

    if music_is_playing_segment:
        text = f"Music on  {music_percent}%"
        color = RULE_TEXT_COLOR
    elif gap_pause_timer > 0:
        text = f"Edge pause  {music_percent}%"
        color = RULE_TEXT_COLOR
    else:
        if remaining > 3.0:
            text = f"Window scanning {current_speed}"
            color = SUB_TEXT_COLOR
        elif remaining > 2.0:
            text = f"Signal rising {current_speed}"
            color = RULE_TEXT_COLOR
        else:
            text = f"Final window {current_speed}"
            color = TIMER_WARNING

    surf = small_font.render(text, True, color)
    rect = surf.get_rect(center=(CENTER_X, CENTER_Y + 110))
    screen.blit(surf, rect)

def draw_center_message():
    if center_message_timer <= 0 or center_message == "":
        return

    alpha = int(255 * (center_message_timer / max(1, CENTER_MESSAGE_MAX_TIMER)))
    temp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    shadow_surf = center_message_font.render(center_message, True, (0, 0, 0))
    shadow_surf.set_alpha(max(0, alpha // 2))
    shadow_rect = shadow_surf.get_rect(center=(CENTER_X + 3, CENTER_Y + 4))
    temp.blit(shadow_surf, shadow_rect)

    main_surf = center_message_font.render(center_message, True, center_message_color)
    main_surf.set_alpha(alpha)
    main_rect = main_surf.get_rect(center=(CENTER_X, CENTER_Y))
    temp.blit(main_surf, main_rect)

    screen.blit(temp, (0, 0))

# =========================
# 23. 特效绘制
# =========================
def draw_freeze_effects():
    for effect in freeze_effects:
        t = effect["timer"]
        max_t = effect["max_timer"]

        radius = 14 + t * 2
        alpha = max(0, 180 - int(180 * (t / max_t)))

        temp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(
            temp,
            (effect["color"][0], effect["color"][1], effect["color"][2], alpha),
            (int(effect["x"]), int(effect["y"])),
            radius,
            3
        )
        screen.blit(temp, (0, 0))

def draw_success_effect():
    radius = 50 + success_flash_timer * 9
    alpha_strength = max(0, 220 - success_flash_timer * 10)

    if alpha_strength > 0:
        temp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        pygame.draw.circle(
            temp,
            (SUCCESS_FLASH_COLOR[0], SUCCESS_FLASH_COLOR[1], SUCCESS_FLASH_COLOR[2], alpha_strength),
            (CENTER_X, CENTER_Y),
            radius,
            8
        )

        pygame.draw.circle(
            temp,
            (255, 255, 255, max(0, alpha_strength // 2)),
            (CENTER_X, CENTER_Y),
            max(10, radius // 2),
            2
        )

        success_text = "ESCAPED"
        text_alpha = max(0, alpha_strength)

        shadow = success_text_font.render(success_text, True, (0, 0, 0))
        shadow.set_alpha(max(0, text_alpha // 2))
        shadow_rect = shadow.get_rect(center=(CENTER_X + 4, CENTER_Y + 6))
        temp.blit(shadow, shadow_rect)

        text_surf = success_text_font.render(success_text, True, SUCCESS_TEXT_COLOR)
        text_surf.set_alpha(text_alpha)
        text_rect = text_surf.get_rect(center=(CENTER_X, CENTER_Y))
        temp.blit(text_surf, text_rect)

        screen.blit(temp, (0, 0))

# =========================
# 24. 开始页 / 过场
# =========================
def draw_start_overlay():
    draw_center_text("PRESS SPACE TO START", title_font, START_TEXT_COLOR, CENTER_X, CENTER_Y - 18)
    draw_center_text("Project 4 : Sweep Signal", sub_font, SUB_TEXT_COLOR, CENTER_X, CENTER_Y + 24)
    draw_center_text("Collision pushes the music forward", sub_font, RULE_TEXT_COLOR, CENTER_X, CENTER_Y + 58)

def draw_next_round_overlay():
    if round_end_time is None:
        return

    now = pygame.time.get_ticks()
    left_ms = max(0, ROUND_END_PAUSE_MS - (now - round_end_time))
    left_sec = math.ceil(left_ms / 1000.0)

    draw_center_text("ROUND COMPLETE", title_font, START_TEXT_COLOR, CENTER_X, CENTER_Y - 10)
    draw_center_text(f"Next round in {left_sec}", sub_font, SUB_TEXT_COLOR, CENTER_X, CENTER_Y + 38)

# =========================
# 25. 绘制场景
# =========================
def draw_scene():
    screen.fill(BG_COLOR)

    draw_ring_with_gap()
    draw_gap_markers()

    if not waiting_to_start and not game_over:
        draw_countdown()

    for ball in frozen_balls:
        pygame.draw.circle(
            screen,
            ball["color"],
            (int(ball["x"]), int(ball["y"])),
            ball["radius"]
        )

    if active_ball is not None and not game_over:
        pygame.draw.circle(
            screen,
            active_ball["color"],
            (int(active_ball["x"]), int(active_ball["y"])),
            active_ball["radius"]
        )

    draw_freeze_effects()

    if not game_success:
        draw_center_message()

    if not waiting_to_start:
        draw_frozen_ball_icons()
        draw_ball_index()
        draw_project_rule_text()

        if not game_over:
            draw_status_text()

    if game_over and game_success:
        draw_success_effect()

    if waiting_to_start:
        draw_start_overlay()

    if game_over and round_end_time is not None:
        draw_next_round_overlay()

    pygame.display.flip()

# =========================
# 26. 初始化
# =========================
load_collision_bgm()
reset_round_gap()
active_ball = None

# =========================
# 27. 主循环
# =========================
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if waiting_to_start and event.key == pygame.K_SPACE:
                waiting_to_start = False
                start_new_round()

    if not waiting_to_start:
        if not game_over and active_ball is not None:
            update_gap_swing()

            move_active_ball(active_ball)

            # 连续处理两次，减少穿模
            handle_collision_with_frozen_balls(active_ball)
            handle_collision_with_frozen_balls(active_ball)

            if check_ball_escape(active_ball):
                stop_collision_music_immediately()
                play_sound(success_sound)

                game_over = True
                game_success = True
                success_flash_timer = 0
                active_ball = None
                round_end_time = pygame.time.get_ticks()

                set_center_message("ESCAPED", SUCCESS_TEXT_COLOR, CENTER_MESSAGE_MAX_TIMER * 2)

            else:
                if get_remaining_time() <= 0:
                    stop_collision_music_immediately()
                    freeze_current_ball()

        if game_over and game_success:
            success_flash_timer += 1

            if round_end_time is not None:
                now = pygame.time.get_ticks()
                if now - round_end_time >= ROUND_END_PAUSE_MS:
                    start_new_round()

    update_collision_music()
    update_freeze_effects()
    update_center_message()

    draw_scene()

stop_collision_music_immediately()
pygame.quit()