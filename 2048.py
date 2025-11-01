import pygame
import sys
import os
import json
import random
import math
from collections import deque


# =========== part 1 ===========
class block_body(pygame.sprite.Sprite):
    def __init__(self, Color, X, Y, Value, anim):
        pygame.sprite.Sprite.__init__(self)

        self.anim = anim
        self.color = Color
        self.value = Value

        self.base_image = get_tile_surface(self.value, self.color)
        self.image = self.base_image.copy()
        pygame.draw.rect(
            self.base_image, self.color,
            pygame.Rect(0, 0, block_big, block_big),
            border_radius=int(screen_size / 53)
        )

        font_sm = pygame.font.SysFont(
            "comingsoon", int(block_big*0.5)
        )
        font_sm.set_bold(True)
        text = font_sm.render(
            str(self.value), True, (60, 58, 50)
        )
        text_rect = text.get_rect(
            center=(block_big/2, block_big/2)
        )
        self.base_image.blit(text, text_rect)

        self.rect = self.base_image.get_rect()
        self.X = grid - grid_big + X * block_width
        self.Y = block_width + block - grid_big + Y * block_width
        self.start_pos = pygame.Vector2(self.X, self.Y)
        self.target_pos = pygame.Vector2(self.X, self.Y)

        self.move_progress = 1.0
        self.move_speed = 0.48

        self.anim_size = int(block_big * 0.4)
        self.font_anim = 0.71

        self.board_pos = (X, Y)
        sprite_map[(X, Y)] = self

    def update(self):
        moved = False

        for start, end in list(path_dict.items()):
            sprite = find_sprite_at(*start)
            sprite2 = find_sprite_at(*end)
            if sprite is None:
                del path_dict[start]
                continue
            if sprite2:
                del path_dict[start]
                value = sprite2.value * 2
                color = tile_colors.get(value, (60, 58, 50))

                sprite.kill()
                all.remove(sprite)
                board[end[0]][end[1]] = value
                sprite2.color = color
                sprite2.value = value
                sprite2.anim_size = int(block_big * 0.4)
                sprite2.font_anim = 0.71
                sprite2.anim = True
                sprite2.board_pos = (end[0], end[1])
                empty_positions.append((start[0], start[1]))
                sprite2.base_image = get_tile_surface(
                    sprite2.value, sprite2.color
                )

                del sprite_map[(start[0], start[1])]
                sprite_map[(end[0], end[1])] = sprite2
                moved = True
                continue

            board[start[0]][start[1]] = 0
            board[end[0]][end[1]] = sprite.value
            tpx = grid - grid_big + end[0] * block_width
            tpy = block_width + block - grid_big + end[1] * block_width
            sprite.board_pos = (end[0], end[1])
            sprite.prev_X = sprite.X
            sprite.prev_Y = sprite.Y
            sprite.move_to(tpx, tpy)
            del sprite_map[(start[0], start[1])]
            sprite_map[(end[0], end[1])] = sprite

            empty_positions.append((start[0], start[1]))
            empty_positions.remove((end[0], end[1]))
            moved = True

            del path_dict[start]

        if moved:
            global pending_new_tile, move_times
            move_times += 1
            pending_new_tile = True
            save_data()

        if self.move_progress < 1.0:
            self.move_progress += self.move_speed
            if self.move_progress > 1.0:
                self.move_progress = 1.0
            now_pos = self.start_pos.lerp(self.target_pos, self.move_progress)
        else:
            now_pos = self.target_pos

        self.X, self.Y = now_pos.x, now_pos.y

        if self.anim:
            if self.anim_size < block_big:
                self.anim_size += 30
                if self.anim_size >= block_big:
                    self.anim_size = block_big
                    self.anim = False
            scaled_image = pygame.transform.smoothscale(
                self.base_image,
                (self.anim_size, self.anim_size)
            )
            self.image = scaled_image
            self.rect = self.image.get_rect(
                center=(
                    self.X + block_big / 2,
                    self.Y + block_big / 2
                )
            )
        else:
            self.image = self.base_image
            self.rect = self.image.get_rect(
                topleft=(self.X, self.Y)
            )

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
            self.image.get_rect(), border_radius=8
        )
        pygame.draw.polygon(
            self.image, (30, 30, 30), pos[self.dir]
        )


pygame.init()
clock = pygame.time.Clock()


def find_sprite_at(board_x, board_y):
    return sprite_map.get((board_x, board_y))


def resize(set_row, set_screen):
    global row, screen_size, block, grid, grid_big
    global block_width, sc_w, sc_h, screen, asize
    global t, agrid, apos, a, b, b1, c, d, pos, block_big
    global dir_pos, font_size_small, font, font_big

    arrow.empty()

    row = set_row
    screen_size = set_screen
    block = int(screen_size / row)
    grid = int(block / 7)
    grid_big = grid * 0.14
    block_big = block + grid_big * 2
    block_width = block + grid
    sc_w = row * block_width + grid
    sc_h = sc_w + 2 * block
    screen = pygame.display.set_mode((sc_w, sc_h))

    asize = screen_size / 5
    t = asize * 0.6
    agrid = asize / 10
    apos = sc_h + 2 * grid
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
        (3 * asize + 2 * agrid, apos + asize + agrid),
        (2 * asize + agrid, apos + asize + agrid),
        (asize, apos + asize + agrid),
        (2 * asize + agrid, apos)
    ]

    font_size_small = int(screen_size / 20)
    font_size_big = int(screen_size / 6)
    font = pygame.font.SysFont(
        "comingsoon", font_size_small
    )
    font_big = pygame.font.SysFont(
        "comingsoon", font_size_big
    )
    font.set_bold(True)
    font_big.set_bold(True)

    all.empty()
    sprite_map.clear()
    anim_list.clear()
    path_dict.clear()
    empty_positions.clear()
    text_cache.clear()

    empty_positions.extend(
        (x, y) for x in range(row)
        for y in range(row) if board[x][y] == 0
    )

    for i in range(row):
        for j in range(row):
            if board[i][j] != 0:
                color = tile_colors.get(board[i][j], (60, 58, 50))
                p1 = block_body(color, i, j, board[i][j], False)
                all.add(p1)
                sprite_map[(i, j)] = p1

    for i in range(4):
        p2 = arrow_keys(i)
        arrow.add(p2)


background = (155, 135, 118)
block_back = (189, 172, 152)
tile_colors = {
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}

dx = [1, 0, -1, 0]
dy = [0, 1, 0, -1]

mouse_released, mouse_pressed = False, False
any_keydown = False

row, screen_size, block, grid, grid_big = 4, 0, 0, 0, 0
block_width, sc_w, sc_h, block_big = 0, 0, 0, 0

asize, t, agrid, apos = 0, 0, 0, 0
a, b, b1, c, d = 0, 0, 0, 0, 0
pos = []
dir_pos = []
board = [[0]*row for _ in range(row)]
font_size_small = 0
font = pygame.font.SysFont(None, 0)
font_big = pygame.font.SysFont(None, 0)

score = 0
best_score = 0
move_times = 0

first_moved = False
game_over = False
pending_new_tile = False

all = pygame.sprite.Group()
arrow = pygame.sprite.Group()

empty_positions = [(x, y) for x in range(row) for y in range(row)]
anim_list = deque()
path_dict = {}
sprite_map = {}
text_cache = {}


def get_tile_surface(value, color):
    if value in text_cache:
        return text_cache[value]

    surf = pygame.Surface(
        (block_big, block_big), pygame.SRCALPHA
    )
    pygame.draw.rect(
        surf, color, pygame.Rect(
            0, 0, block_big, block_big
        ),
        border_radius=int(screen_size / 53)
    )

    font_sm = pygame.font.SysFont("comingsoon", int(block_big * 0.5))
    font_sm.set_bold(True)
    text = font_sm.render(
        str(value), True, (60, 58, 50)
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
        p1 = block_body(color, x, y, num, anim)
        all.add(p1)
        anim_list.append((x, y))


def any_block_moving():
    for sprite in all:
        if isinstance(sprite, block_body) and sprite.move_progress < 1.0:
            return True

    return False


def check_death():
    place = False

    for x in range(row):
        for y in range(row):
            if board[x][y] == 0:
                place = True

    if not place:
        death()


def death():
    global game_over

    for i in range(row):
        for j in range(row):
            for k in range(4):
                x, y = i + dx[k], j + dy[k]
                if 0 <= x < row and 0 <= y < row:
                    if board[i][j] == board[x][y]:
                        return

    game_over = True


def moving(step):
    global first_moved
    first_moved = True

    q = deque()
    visited = [[False]*row for _ in range(row)]

    for i in get_scan_order(step):
        for j in range(row):
            x, y = (i, j) if step in [0, 2] else (j, i)
            if board[x][y] != 0:
                q.append((x, y))

    while q:
        x, y = q.popleft()
        nx, ny = x + dx[step], y + dy[step]
        global score

        if 0 <= nx < row and 0 <= ny < row:
            if board[nx][ny] == 0:
                board[nx][ny] = board[x][y]
                board[x][y] = 0

                start = (x, y)
                end = (nx, ny)
                find = False
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

                start = (x, y)
                end = (nx, ny)
                find = False
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
        return range(row-1, -1, -1)
    else:
        return range(row)


# =========== part 2 ===========
def update_score_label(text, text1, kind):
    text = font.render(text, True, (151, 138, 118))
    text_sc = font.render(text1, True, (151, 138, 118))
    popup = pygame.Rect(
        grid + sc_w / 2 * kind, block * 1.3,
        sc_w / 2 - 2 * grid,
        block / 2, border_radius=8
    )
    pygame.draw.rect(
        screen, (233, 231, 217),
        popup, width=3 * kind,
        border_radius=10
    )
    text_rect = text.get_rect()
    text_sc_rect = text_sc.get_rect()

    text_rect.right = popup.right - 10
    text_rect.centery = popup.centery
    text_sc_rect.left = popup.left + 10
    text_sc_rect.centery = popup.centery

    screen.blit(text, text_rect)
    screen.blit(text_sc, text_sc_rect)


def update_screen():
    global best_score

    screen.fill((252, 248, 240))

    rect = pygame.Rect(0, 2 * block, sc_w, sc_w)
    pygame.draw.rect(
        screen, background, rect,
        border_radius=int(screen_size / 16)
    )
    best_score = max(score, best_score)
    update_score_label(f"{score}", "SCORE", 0)
    update_score_label(f"{best_score}", "BEST", 1)

    r2 = int(screen_size / 11)
    reload_rect = pygame.Rect(
        sc_w * 0.88, block / 1.8, r2, r2
    )
    draw_reload_icon(reload_rect.center, r2 / 2)
    resize_rect = pygame.Rect(
        sc_w * 0.05, block / 1.9, r2, r2
    )
    draw_resize_icon(resize_rect.center, r2)
    draw_grid()

    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()[0]
    if (
        reload_rect.collidepoint(mouse_pos) and
        mouse_click and
        not game_over
    ):
        restart_game()
    elif (
        resize_rect.collidepoint(mouse_pos) and
        mouse_click and
        not game_over
    ):
        s = choose_screen_size()
        resize(4, s)


def restart_game():
    global board, score, first_moved
    global empty_positions, move_times

    if first_moved:
        board = [[0]*row for _ in range(row)]
        empty_positions = [(x, y) for x in range(row) for y in range(row)]
        sprite_map.clear()
        anim_list.clear()
        path_dict.clear()
        all.empty()

        score = 0
        move_times = 0

        for _ in range(2):
            generate_block(True)

        first_moved = False


def get_save_path(filename="2048_data.json"):
    folder = os.path.dirname(__file__)
    return os.path.join(folder, filename)


def save_data():
    file = get_save_path()
    game_data = {
        "board": board,
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
    global first_moved, move_times

    if os.path.exists(file) and os.path.getsize(file) > 0:
        with open(file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                board = data.get("board", 0)
                score = data.get("score", 0)
                best_score = data.get("best score", 0)
                screen_size = data.get("screen_size", 0)
                first_moved = data.get("first_moved", 0)
                move_times = data.get("move_times", 0)
            except json.JSONDecodeError:
                board = [[0]*4 for _ in range(4)]
                score = 0
                best_score = 0
                screen_size = 0
                first_moved = False
                move_times = 0

    else:
        board = [[0]*4 for _ in range(4)]
        score = 0
        best_score = 0
        screen_size = 0
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


def draw_game_over_overlay():
    overlay = pygame.Surface((sc_w, sc_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    screen.blit(overlay, (0, 0))

    r2 = int(screen_size / 8)
    reload_rect = pygame.Rect(
        sc_w / 2 - r2 / 2, sc_h / 1.8, r2, r2
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


def draw_grid():
    for i in range(block_width + block, sc_h - grid, block_width):
        for j in range(grid, sc_w - grid, block_width):
            rect_block = pygame.Rect(j, i, block, block)
            pygame.draw.rect(
                screen, block_back, rect_block,
                border_radius=int(screen_size / 53)
            )


def choose_screen_size():
    sizes = [300, 400, 500, 600]
    word = [
         "For mobile phones, recommend 500px;",
         "for computers, 300 or 400px."
     ]
    label_y = [270, 300]
    cols = 2
    spacing = 20
    btn_w, btn_h = 240, 100
    margin_x, margin_y = 60, 60
    screen = pygame.display.set_mode((620, 380))
    font = pygame.font.SysFont("cutivemono", 50)
    font.set_bold(True)
    font_small = pygame.font.SysFont("cutivemono", 18)
    font.set_bold(True)
    last = pygame.time.get_ticks()

    while True:
        screen.fill((252, 248, 240))
        for i, s in enumerate(sizes):
            row = i // cols
            col = i % cols
            x = margin_x + col * (btn_w + spacing)
            y = margin_y + row * (btn_h + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            now = pygame.time.get_ticks()

            label = font.render(
                f"{s} px", True, (60, 58, 50)
            )
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)

            if i in [0, 1]:
                rect1 = pygame.Rect(
                    0, label_y[i], 620, 100
                )
                rect1.centerx = label_y[i] * 0.78 + 20 * i
                label1 = font_small.render(
                    word[i], True, (60, 58, 50)
                )
                label_rect1 = label.get_rect(
                    center=rect1.center
                )
                screen.blit(label1, label_rect1)

            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (200, 200, 200), rect, 2)
                if (
                    now - last > 300 and
                    pygame.mouse.get_pressed()[0]
                ):
                    return s
            else:
                pygame.draw.rect(screen, (180, 180, 180), rect, 1)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.update()


load_data()
if screen_size == 0:
    s = choose_screen_size()
    for _ in range(2):
        generate_block(True)
else:
    s = screen_size
    check_death()
resize(4, s)

while True:
    mouse_released, mouse_pressed = False, False
    any_keydown = False
    clock.tick(60)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            save_data()
            pygame.quit()
            sys.exit()
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
    else:
        check_death()
        save_data()

    pygame.display.update()
