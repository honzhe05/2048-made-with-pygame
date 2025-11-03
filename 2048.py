import pygame
import sys
import os
import json
import random
import math
from collections import deque
from datetime import datetime


# =========== part 1 ===========
class Block(pygame.sprite.Sprite):
    def __init__(self, color, x, y, value, anim):
        super().__init__()
        self.color = color
        self.value = value
        self.anim = anim

        self.X = grid - grid_big + x * block_width
        self.Y = 2 * block_width - grid_big + grid + y * block_width
        self.start_pos = pygame.Vector2(self.X, self.Y)
        self.target_pos = pygame.Vector2(self.X, self.Y)
        self.move_progress = 1.0
        self.move_speed = screen_size * 0.00085
        self.board_pos = (x, y)

        self.anim_size = int(block_big * 0.4)
        self.font_anim = screen_size / 704.2

        self.base_image = self._make_tile_surface()
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(topleft=(self.X, self.Y))

        sprite_map[(x, y)] = self

    def _make_tile_surface(self):
        surf = get_tile_surface(self.value, self.color)
        pygame.draw.rect(
            surf, self.color,
            pygame.Rect(0, 0, block_big, block_big),
            border_radius=int(screen_size / 53)
        )

        font = pygame.font.SysFont(
            font_style, int(block_big * 0.45)
        )
        font.set_bold(True)

        text_color = (255, 255, 255) if self.value >= 8 else (117, 100, 82)
        text = font.render(str(self.value), True, text_color)
        text_rect = text.get_rect(
            center=(block_big / 2, block_big / 2)
        )
        surf.blit(text, text_rect)
        return surf

    def update(self):
        self._process_path_moves()
        self._update_position()
        self._update_animation()

    def _process_path_moves(self):
        global pending_new_tile, move_times

        moved = False
        for start, end in list(path_dict.items()):
            sprite = find_sprite_at(*start)
            sprite2 = find_sprite_at(*end)

            if sprite is None:
                del path_dict[start]
                continue

            if sprite2:
                self._merge_blocks(
                    sprite, sprite2, start, end
                )
                moved = True
                continue

            self._move_block(sprite, start, end)
            moved = True

        if moved:
            move_times += 1
            pending_new_tile = True
            save_data()
        else:
            check_death()

    def _merge_blocks(self, sprite, sprite2, start, end):
        del path_dict[start]
        value = sprite2.value * 2
        color = tile_colors.get(value, (60, 58, 50))

        sprite.kill()
        all.remove(sprite)
        board[end[0]][end[1]] = value
        sprite2.color = color
        sprite2.value = value
        sprite2.anim_size = int(block_big * 0.4)
        sprite2.font_anim = screen_size / 704.2
        sprite2.anim = True
        sprite2.board_pos = end
        empty_positions.append(start)

        sprite2.base_image = get_tile_surface(value, color)
        del sprite_map[start]
        sprite_map[end] = sprite2

    def _move_block(self, sprite, start, end):
        board[start[0]][start[1]] = 0
        board[end[0]][end[1]] = sprite.value

        target_x = grid - grid_big + end[0] * block_width
        target_y = 2 * block_width - grid_big + grid + end[1] * block_width

        sprite.board_pos = end
        sprite.prev_X = sprite.X
        sprite.prev_Y = sprite.Y
        sprite.move_to(target_x, target_y)

        del sprite_map[start]
        sprite_map[end] = sprite

        empty_positions.append(start)
        if end in empty_positions:
            empty_positions.remove(end)

        del path_dict[start]

    def _update_position(self):
        if self.move_progress < 1.0:
            self.move_progress += self.move_speed
            if self.move_progress > 1.0:
                self.move_progress = 1.0
            pos = self.start_pos.lerp(
                self.target_pos, self.move_progress
            )
        else:
            pos = self.target_pos

        self.X, self.Y = pos.x, pos.y

    def _update_animation(self):
        if self.anim:
            if self.anim_size < block_big:
                self.anim_size += screen_size / 16.7
                if self.anim_size >= block_big:
                    self.anim_size = block_big
                    self.anim = False

            scaled_image = pygame.transform.smoothscale(
                self.base_image,
                (self.anim_size, self.anim_size)
            )
            self.image = scaled_image
            self.rect = self.image.get_rect(center=(
                self.X + block_big / 2,
                self.Y + block_big / 2
            ))
        else:
            self.image = self.base_image
            self.rect = self.image.get_rect(topleft=(
                self.X, self.Y
            ))

    def move_to(self, new_x, new_y):
        self.start_pos = pygame.Vector2(self.X, self.Y)
        self.target_pos = pygame.Vector2(new_x, new_y)
        self.move_progress = 0.0


class arrow_keys(pygame.sprite.Sprite):
    def __init__(self, Dir):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((asize, asize), pygame.SRCALPHA)
        self.dir = Dir
        self.rect = self.image.get_rect()
        self.rect.x = dir_pos[self.dir][0]
        self.rect.y = dir_pos[self.dir][1]

    def update(self):
        self.image.fill((0, 0, 0, 0))
        color = (180, 180, 180)
        mouse_pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(mouse_pos):
            color = (150, 150, 150)
            if mouse_pressed:
                color = (160, 160, 160)
            elif mouse_released:
                color = (180, 180, 180)
                moving(self.dir)

        pygame.draw.rect(
            self.image, color,
            self.image.get_rect(),
            border_radius=int(screen_size / 63)
        )
        pygame.draw.polygon(
            self.image, (30, 30, 30), pos[self.dir]
        )


pygame.init()
clock = pygame.time.Clock()


def find_sprite_at(board_x, board_y):
    return sprite_map.get((board_x, board_y))


def resize(set_screen):
    global row, screen_size, block, grid, grid_big
    global block_width, sc_w, sc_h, screen, asize
    global t, agrid, apos, a, b, b1, c, d, pos, block_big
    global dir_pos, font_size_small, font, font_big
    global font_size_big, font_arrow, text_arrow

    arrow.empty()
    all.empty()
    sprite_map.clear()
    anim_list.clear()
    path_dict.clear()
    empty_positions.clear()
    text_cache.clear()

    row = 4  # screen and block
    screen_size = set_screen
    set_screen = set_screen * 28.2 / 33
    block = int(set_screen / row)
    grid = int(block / 7)
    grid_big = grid * 0.15
    block_big = block + grid_big * 2
    block_width = block + grid
    sc_w = row * block_width + grid
    sc_h = sc_w + 2 * block_width
    screen = pygame.display.set_mode((sc_w, sc_h))

    asize = screen_size / 5  # arrow buttons
    t = asize * 0.6
    agrid = asize / 10
    apos = sc_h + 2 * grid
    p = sc_w / 2 + asize / 2 + agrid

    a = t / 2 * math.sqrt(3)
    b = (asize - a) / 2.0 + (asize / 50)
    b1 = (asize - a) / 2.0 - (asize / 50)
    c = (asize - t) / 2
    d = c + t / 2
    pos = [
        [(b, c), (a + b, d), (b, t + c)],
        [(c, b), (t + c, b), (d, a + b)],
        [(a + b1, c), (a + b1, t + c), (b1, d)],
        [(c, a + b1), (t + c, a + b1), (d, b1)]
    ]
    dir_pos = [
        (p, apos + asize + agrid),
        (p - asize - agrid, apos + asize + agrid),
        (p - 2 * asize - 2 * agrid, apos + asize + agrid),
        (p - asize - agrid, apos)
    ]
    for i in range(4):
        p2 = arrow_keys(i)
        arrow.add(p2)

    font_size_small = int(screen_size / 20)  # fonts
    font_size_big = int(screen_size / 6.5)
    font = pygame.font.SysFont(
        font_style, font_size_small
    )
    font_big = pygame.font.SysFont(
        font_style, font_size_big
    )
    font_arrow = pygame.font.SysFont(
        "arial", int(screen_size / 12)
    )
    font_arrow.set_bold(True)
    font.set_bold(True)
    font_big.set_bold(True)

    text_arrow = font_arrow.render(
        "<", True, (255, 255, 255)
    )

    check_death()
    empty_positions.extend(  # redraw
        (x, y) for x in range(4)
        for y in range(4) if board[x][y] == 0
    )

    for i in range(4):
        for j in range(4):
            if board[i][j] != 0:
                color = tile_colors.get(
                    board[i][j], (60, 58, 50)
                )
                p1 = Block(color, i, j, board[i][j], False)
                all.add(p1)
                sprite_map[(i, j)] = p1


background = (155, 135, 118)
block_back = (189, 172, 152)
tile_colors = {
    2: (238, 228, 218), 4: (237, 224, 200),
    8: (242, 177, 121), 16: (245, 149, 99),
    32: (246, 124, 95), 64: (246, 94, 59),
    128: (237, 207, 114), 256: (237, 204, 97),
    512: (237, 200, 80), 1024: (237, 197, 63),
    2048: (237, 194, 46),
}

dx = [1, 0, -1, 0]
dy = [0, 1, 0, -1]

mouse_released, mouse_pressed = False, False
any_keydown = False

row, screen_size, block, grid, grid_big = 4, 0, 0, 0, 0
block_width, sc_w, sc_h, block_big = 0, 0, 0, 0
time = "None"

asize, t, agrid, apos = 0, 0, 0, 0
a, b, b1, c, d, p = 0, 0, 0, 0, 0, 0
pos, dir_pos = [], []

font_size_small, font_size_big = 0, 0
font = pygame.font.SysFont(None, 0)
font_big = pygame.font.SysFont(None, 0)
font_arrow = pygame.font.SysFont("arial", 0)
font_arrow.set_bold(True)
text_arrow = font.render("<", True, (255, 255, 255))
font_style = "comingsoon"

score, best_score, move_times = 0, 0, 0

first_moved, game_over = False, False
pending_new_tile, undo_touch = False, False

all = pygame.sprite.Group()
arrow = pygame.sprite.Group()

board = [[0]*4 for _ in range(4)]
board_prev = [[0]*4 for _ in range(4)]
empty_positions = [(x, y) for x in range(4) for y in range(4)]
anim_list = deque()
path_dict, sprite_map, text_cache = {}, {}, {}


def get_tile_surface(value, color):
    if value in text_cache:
        return text_cache[value]

    surf = pygame.Surface(
        (block_big, block_big), pygame.SRCALPHA
    )
    pygame.draw.rect(
        surf, color, pygame.Rect(
            0, 0, block_big, block_big
        ), border_radius=int(screen_size / 53)
    )

    font_sm = pygame.font.SysFont(font_style, int(block_big * 0.45))
    font_sm.set_bold(True)

    if value >= 8:
        text_color = (255, 255, 255)
    else:
        text_color = (117, 100, 82)
    text = font_sm.render(
        str(value), True, text_color
    )
    text_rect = text.get_rect(
        center=(block_big / 2, block_big / 2)
    )
    surf.blit(text, text_rect)

    text_cache[value] = surf
    return surf


def generate_block(anim=False):
    x, y = random.choice(empty_positions)
    empty_positions.remove((x, y))

    num = 4 if random.randint(0, 10) == 0 else 2
    board[x][y] = num
    color = tile_colors.get(num, (60, 58, 50))

    if find_sprite_at(x, y) is None:
        p1 = Block(color, x, y, num, anim)
        all.add(p1)
        anim_list.append((x, y))


def any_block_moving():
    for sprite in all:
        if isinstance(sprite, Block) and sprite.move_progress < 1.0:
            return True

    return False


def check_death():
    place = False

    for x in range(4):
        for y in range(4):
            if board[x][y] == 0:
                place = True

    if not place:
        death()


def death():
    global game_over

    for i in range(4):
        for j in range(4):
            for k in range(4):
                x, y = i + dx[k], j + dy[k]
                if 0 <= x < row and 0 <= y < row:
                    if board[i][j] == board[x][y]:
                        return

    game_over = True


def moving(step):
    global first_moved, board_prev, undo_touch
    first_moved, undo_touch = True, True

    board_prev = [row[:] for row in board]
    q = deque()
    visited = [[False]*4 for _ in range(4)]

    for i in get_scan_order(step):
        for j in range(4):
            x, y = (i, j) if step in [0, 2] else (j, i)
            if board[x][y] != 0:
                q.append((x, y))

    while q:
        x, y = q.popleft()
        nx, ny = x + dx[step], y + dy[step]
        start, end = (x, y), (nx, ny)
        find = False
        global score

        if 0 <= nx < row and 0 <= ny < row:
            if board[nx][ny] == 0:
                board[nx][ny] = board[x][y]
                board[x][y] = 0

                for k, v in path_dict.items():
                    if v == start:
                        path_dict[k] = end
                        find = True
                        break
                if not find:
                    path_dict[start] = end

                q.append((nx, ny))

            elif (
                board[nx][ny] == board[x][y] and
                not visited[nx][ny]
            ):
                board[nx][ny] *= 2
                board[x][y] = 0

                for k, v in path_dict.items():
                    if v == start:
                        path_dict[k] = end
                        find = True
                        break
                if not find:
                    path_dict[start] = end

                score += board[nx][ny]
                visited[nx][ny] = True


def get_scan_order(step):
    if step in [0, 1]:
        return range(3, -1, -1)
    else:
        return range(4)


def redraw_prev():
    global board, undo_touch, move_times
    board = [row[:] for row in board_prev]
    undo_touch = False
    move_times -= 1

    all.empty()
    sprite_map.clear()
    anim_list.clear()
    path_dict.clear()
    empty_positions.clear()

    empty_positions.extend(
        (x, y) for x in range(4)
        for y in range(4) if board[x][y] == 0
    )

    for i in range(4):
        for j in range(4):
            if board[i][j] != 0:
                color = tile_colors.get(
                    board[i][j], (60, 58, 50)
                )
                p1 = Block(color, i, j, board[i][j], False)
                all.add(p1)
                sprite_map[(i, j)] = p1


# =========== part 2 ===========
def update_score_label(text, text1, kind):
    color = (151, 138, 118)
    text = font.render(text, True, color)
    text_sc = font.render(text1, True, color)
    popup = pygame.Rect(
        grid + sc_w / 2 * kind, block_width * 1.36,
        sc_w / 2 - 2 * grid, block / 2
    )
    pygame.draw.rect(
        screen, (233, 231, 217),
        popup, width=3 * kind,
        border_radius=int(screen_size / 30)
    )
    text_rect = text.get_rect()
    text_sc_rect = text_sc.get_rect()

    text_grid = screen_size / 30
    text_rect.right = popup.right - text_grid
    text_rect.centery = popup.centery
    text_sc_rect.left = popup.left + text_grid
    text_sc_rect.centery = popup.centery

    screen.blit(text, text_rect)
    screen.blit(text_sc, text_sc_rect)


def update_screen():
    global best_score, undo_touch

    screen.fill((243, 239, 229))
    pygame.draw.rect(
        screen, (252, 248, 240),
        (0, grid, sc_w, sc_h - grid)
    )

    rx = screen_size / 4.5
    rect_p = pygame.Rect(rx, 2 * grid, screen_size / 1.8, rx)
    pygame.draw.rect(
        screen, (232, 230, 216), rect_p,
        border_radius=int(screen_size / 20)
    )

    rect = pygame.Rect(0, 2 * block_width, sc_w, sc_w)
    pygame.draw.rect(
        screen, background, rect,
        border_radius=int(screen_size / 16)
    )
    best_score = max(score, best_score)
    update_score_label(f"{score}", "SCORE", 0)
    update_score_label(f"{best_score}", "BEST", 1)

    r2 = int(screen_size / 11)
    r3 = r2 + int(screen_size / 27)
    reload_rect = pygame.Rect(
        sc_w * 0.85, block / 1.5, r2, r2
    )
    draw_reload_icon(reload_rect.center, r2 / 2)
    resize_rect = pygame.Rect(
        sc_w * 0.05, block / 1.5, r2, r2
    )
    draw_resize_icon(resize_rect.center, r2)
    undo_rect = pygame.Rect(
        sc_w * 0.25, block / 2.4, r3, r3
    )

    if (
        set(c for r in board_prev for c in r) == {0} or
        not undo_touch
    ):
        color = (220, 213, 197)
        undo_touch = False
    else:
        color = (187, 171, 154)
        undo_touch = True
    pygame.draw.rect(
        screen, color, undo_rect,
        border_radius=int(screen_size / 30)
    )
    px = screen_size / 36
    draw_undo_arrow(
        (undo_rect.x + px, undo_rect.y + px), r2 * 0.8
    )

    undo1_rect = pygame.Rect(
        sc_w * 0.434, block / 2.4, r3, r3
    )
    pygame.draw.rect(
        screen, (187, 171, 154), undo1_rect,
        border_radius=int(screen_size / 30)
    )
    undo2_rect = pygame.Rect(
        sc_w * 0.622, block / 2.4, r3, r3
    )
    pygame.draw.rect(
        screen, (187, 171, 154), undo2_rect,
        border_radius=int(screen_size / 30)
    )

    draw_grid()

    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()[0]
    if (
        reload_rect.collidepoint(mouse_pos) and
        mouse_click and not game_over
    ):
        restart_game()
    elif (
        resize_rect.collidepoint(mouse_pos) and
        mouse_click and not game_over
    ):
        s = choose_screen_size()
        resize(s)
    elif (
        undo_rect.collidepoint(mouse_pos) and
        mouse_click and not game_over and
        undo_touch
    ):
        redraw_prev()


def restart_game():
    global board, score, first_moved, board_prev
    global empty_positions, move_times

    if first_moved:
        board = [[0]*4 for _ in range(4)]
        board_prev = [[0]*4 for _ in range(4)]
        empty_positions = [(x, y) for x in range(4) for y in range(4)]
        sprite_map.clear()
        anim_list.clear()
        path_dict.clear()
        all.empty()

        score, move_times = 0, 0

        for _ in range(2):
            generate_block(True)

        first_moved = False


def get_save_path(filename="2048_data.json"):
    folder = os.path.dirname(__file__)
    return os.path.join(folder, filename)


def save_data():
    global time

    file = get_save_path()
    if not game_over:
        n = datetime.now()
        time = str(n.strftime("%Y-%m-%d %H:%M"))
    game_data = {
        "save time": time,
        "board_prev": board_prev,
        "board": board,
        "undo_touch": undo_touch,
        "score": score,
        "best score": best_score,
        "screen_size": screen_size,
        "first_moved": first_moved,
        "move_times": move_times
    }

    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(
                game_data, f, ensure_ascii=False)
        print("Game data saved!")
    except Exception as e:
        print(f"Failed to save game data: {e}")


def load_data():
    file = get_save_path()
    global board, score, best_score, screen_size
    global first_moved, move_times, time
    global board_prev, undo_touch

    if os.path.exists(file) and os.path.getsize(file) > 0:
        with open(file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                time = data.get("save time", 0)
                board_prev = data.get("board_prev", 0)
                board = data.get("board", 0)
                undo_touch = data.get("undo_touch", 0)
                score = data.get("score", 0)
                best_score = data.get("best score", 0)
                screen_size = data.get("screen_size", 0)
                first_moved = data.get("first_moved", 0)
                move_times = data.get("move_times", 0)
            except json.JSONDecodeError:
                init_game_state()

    else:
        init_game_state()


def init_game_state():
    global board, score, best_score, screen_size
    global first_moved, move_times, time
    global board_prev, undo_touch

    time = "None"
    board_prev = [[0]*4 for _ in range(4)]
    board = [[0]*4 for _ in range(4)]
    undo_touch = False
    score, best_score, screen_size = 0, 0, 0
    first_moved = False
    move_times = 0


def draw_resize_icon(center, size, color=(117, 100, 82)):
    x, y = center
    box_rect = pygame.Rect(0, 0, size, size)
    box_rect.center = center
    line = int(screen_size / 100)

    pygame.draw.rect(
        screen, color, box_rect,
        width=line, border_radius=8
    )

    ax = box_rect.right - 2 * line
    ay = box_rect.bottom - 2 * line
    pygame.draw.line(screen, color, (ax - line, ay), (ax, ay - 8), line)

    bx = box_rect.left + 2 * line
    by = box_rect.top + 2 * line
    pygame.draw.line(screen, color, (bx + 8, by), (bx, by + 8), line)


def draw_reload_icon(center, r, color=(117, 100, 82)):
    arc = pygame.Rect(0, 0, r * 2, r * 2)
    arc.center = center
    line = int(screen_size / 100)
    a1, a2 = math.radians(30), math.radians(330)
    pygame.draw.arc(screen, color, arc, a1, a2, line)

    tip = (
        center[0] + r * math.cos(a2),
        center[1] + r * math.sin(a2)
    )
    for s in [-1, 1]:
        a = a2 + s * math.radians(75)
        dx = r * 0.25 * math.cos(a)
        dy = r * 0.25 * math.sin(a)
        end = (
            tip[0] - dx * 1.5 - 5,
            tip[1] + dy * 1.1 - 5
        )
        pygame.draw.line(screen, color, tip, end, line)


def draw_undo_arrow(center, size, color=(255, 255, 255)):
    x, y = center
    x += 2
    y += 2
    r = size / 2
    thickness = int(size / 10) + 2

    rect = pygame.Rect(x + 2, y - thickness / 3, size, size)
    pygame.draw.arc(
        screen, color, rect, math.radians(270),
        math.radians(100), thickness - 1
    )
    pygame.draw.line(
        screen, color, (x + thickness, y), (x + r, y), thickness - 1
    )
    pygame.draw.line(
        screen, color, (x + thickness, y + size - thickness * 0.7),
        (x + r, y + size - thickness * 0.7), thickness + 1
    )
    screen.blit(text_arrow, (x - thickness / 2, y - size / 1.5))


def draw_grid():
    for i in range(2 * block_width + grid, sc_h - grid, block_width):
        for j in range(grid, sc_w - grid, block_width):
            rect_block = pygame.Rect(j, i, block, block)
            pygame.draw.rect(
                screen, block_back, rect_block,
                border_radius=int(screen_size / 53)
            )


def draw_game_over_overlay():
    overlay = pygame.Surface((sc_w, sc_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    screen.blit(overlay, (0, 0))

    r2 = int(screen_size / 8)
    reload_rect = pygame.Rect(
        sc_w / 2 - r2 / 2, sc_h / 1.6, r2, r2
    )

    s = pygame.Surface(
        (r2 * 1.5, r2 * 1.5), pygame.SRCALPHA
    )
    pygame.draw.rect(
        s, (0, 0, 0, 70), s.get_rect(),
        border_radius=int(screen_size / 20)
    )
    s_rect = s.get_rect(center=reload_rect.center)
    screen.blit(s, s_rect)

    draw_reload_icon(reload_rect.center, r2 / 2, (255, 255, 255))

    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()[0]
    if (
        any_keydown or (
            reload_rect.collidepoint(mouse_pos) and
            mouse_click
        )
    ):
        restart_game()
        global game_over
        game_over = False

    text = font_big.render(
        "GAME OVER", True, (255, 255, 255)
    )
    text_move = font.render(
        f"this time u moved {move_times} times!",
        True, (255, 255, 255)
    )
    screen.blit(
        text, text.get_rect(
            center=(sc_w / 2, sc_h / 2 - r2 * 1.3))
    )
    screen.blit(
        text_move, text_move.get_rect(
            center=(sc_w / 2, sc_h / 2.1 + r2 / 4))
    )


def choose_screen_size():
    sizes = [360, 480, 540, 720, 1080, 1440]
    word = [
        "For mobile phones, we recommend 540px.",
        "For computers, 360 or 480px is ideal.",
        "If you want the ultimate experience and flawless smoothness,",
        "feel free to choose 1080 or even 1440px:)",
        "", ""
    ]

    label_y = 380
    spacing = 20
    btn_w, btn_h = 240, 100
    margin_x, margin_y = 100, 60
    screen = pygame.display.set_mode((720, 550))

    font = pygame.font.SysFont("cutivemono", 50)
    font.set_bold(True)
    font_small = pygame.font.SysFont("cutivemono", 17)
    font.set_bold(True)

    while True:
        screen.fill((252, 248, 240))

        for i, s in enumerate(sizes):
            row = i // 2
            col = i % 2
            x = margin_x + col * (btn_w + spacing)
            y = margin_y + row * (btn_h + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)

            label = font.render(
                f"{s} px", True, (60, 58, 50)
            )
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)

            rect1 = pygame.Rect(
                0, label_y + i * 25, 720, 100
            )
            rect1.centerx = 360
            label1 = font_small.render(
                word[i], True, (60, 58, 50)
            )
            label_rect1 = label1.get_rect(
                center=rect1.center
            )
            screen.blit(label1, label_rect1)

            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (200, 200, 200), rect, 2)
                if pygame.mouse.get_pressed()[0]:
                    return s
            else:
                pygame.draw.rect(screen, (180, 180, 180), rect, 1)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.update()


load_data()
if not screen_size:
    s = choose_screen_size()
    for _ in range(2):
        generate_block(True)
else:
    s = screen_size
    check_death()
resize(s)

running = True
while running:
    mouse_released, mouse_pressed = False, False
    any_keydown = False
    clock.tick(60)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            save_data()
            running = False
        elif e.type == pygame.KEYDOWN:
            any_keydown = True

            if any_block_moving():
                break

            if e.key in [pygame.K_RIGHT, pygame.K_d]:
                moving(0)
            elif e.key in [pygame.K_DOWN, pygame.K_s]:
                moving(1)
            elif e.key in [pygame.K_LEFT, pygame.K_a]:
                moving(2)
            elif e.key in [pygame.K_UP, pygame.K_w]:
                moving(3)

        mouse_click = pygame.mouse.get_pressed()[0]
        if mouse_click:
            mouse_pressed = True
        else:
            mouse_released = True

    update_screen()

    all.update()
    all.draw(screen)
    arrow.update()
    arrow.draw(screen)

    if game_over:
        draw_game_over_overlay()

    if pending_new_tile:
        generate_block(True)
        pending_new_tile = False

    pygame.display.update()

pygame.quit()
sys.exit()
