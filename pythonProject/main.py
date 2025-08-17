import pgzrun
import random
import pygame
import time
import os

WIDTH = 800
HEIGHT = 600
TITLE = "植物大战僵尸"
FONT_NAME = "s.ttf"

random.seed(time.time())

# 初始化音效系统
pygame.mixer.init()

# 设置背景音乐循环播放
if hasattr(sounds, 'background_music'):
    sounds.background_music.play(-1)  # -1表示循环播放

GAME_STATE = {
    'sunlight': 0,
    'lives': 5,
    'zombies_killed': 0,
    'level': 1,
    'last_zombie_time': 0,
    'game_over': False,
    'victory': False,
    'chomping': False,  # 跟踪是否有僵尸正在啃食植物
    'last_lives': 5,    # 跟踪上次的生命值，用于检测生命值减少
    'game_started': False,  # 添加游戏开始状态
    'zombies_spawned': 0    # 跟踪已生成的僵尸数量
}

# 加载单张图片的Actor
sun = Actor('太阳')
pea = Actor('豌豆')

# 为需要动画的角色创建动画帧
PEASHOOTER_FRAMES = [Actor(f'豌豆射手{i}') for i in range(13)]
CHERRY_BOMB_FRAMES = [Actor(f'樱桃炸弹{i}') for i in range(7)]
ZOMBIE_FRAMES = [Actor(f'僵尸{i}') for i in range(22)]
CONEHEAD_ZOMBIE_FRAMES = [Actor(f'铁桶僵尸{i}') for i in range(15)]
NEWSPAPER_ZOMBIE_FRAMES = [Actor(f'读报僵尸{i}') for i in range(19)]
ANGRY_NEWSPAPER_ZOMBIE_FRAMES = [Actor(f'愤怒的读报僵尸{i}') for i in range(14)]

# 加载僵尸攻击动画帧
NORMAL_ZOMBIE_ATTACK_FRAMES = [Actor(f'僵尸攻击{i}') for i in range(21)]
CONEHEAD_ZOMBIE_ATTACK_FRAMES = [Actor(f'铁桶僵尸攻击{i}') for i in range(11)]
NEWSPAPER_ZOMBIE_ATTACK_FRAMES = [Actor(f'读报僵尸攻击{i}') for i in range(8)]
ANGRY_NEWSPAPER_ZOMBIE_ATTACK_FRAMES = [Actor(f'愤怒的读报僵尸攻击{i}') for i in range(7)]

class Plant:
    def __init__(self, x, y, plant_type, grid_x, grid_y):
        self.plant_type = plant_type
        # 植物位置设为格子中央
        self.x = x + 80  # 格子宽度160的一半
        self.y = y + 60  # 格子高度120的一半
        self.grid_x = grid_x  # 存储网格坐标
        self.grid_y = grid_y  # 存储网格坐标
        self.frame_index = 0
        self.animation_counter = 0
        self.animation_speed = 4  # 控制动画速度（每几帧更新一次）

        # 根据植物类型设置不同生命值
        if plant_type == "peashooter":
            self.health = 300
            self.cooldown = 0
            self.cooldown_max = 30
            self.frames = PEASHOOTER_FRAMES
            self.width = self.frames[0].width
            self.height = self.frames[0].height
        elif plant_type == "cherry_bomb":
            self.health = 1000
            self.explosion_radius = 150
            self.explosion_damage = 1000
            self.exploded = False
            self.frames = CHERRY_BOMB_FRAMES
            self.explosion_time = 0
            self.width = self.frames[0].width
            self.height = self.frames[0].height
            self.explosion_animation = False
            self.explosion_size = 0
            self.explosion_max_size = 160
            # 爆炸中心设为植物中心
            self.explosion_center = (self.x, self.y)
            self.animation_complete = False  # 跟踪樱桃炸弹动画是否完成

    def update_animation(self):
        # 更新动画帧
        self.animation_counter += 1
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

            # 检查樱桃炸弹动画是否完成
            if self.plant_type == "cherry_bomb" and not self.exploded:
                if self.frame_index == len(self.frames) - 1:
                    self.animation_complete = True

    def draw(self):
        if self.plant_type == "peashooter" or (self.plant_type == "cherry_bomb" and not self.exploded):
            # 绘制当前动画帧
            frame = self.frames[self.frame_index]
            frame.pos = (self.x, self.y)
            frame.draw()
        elif self.plant_type == "cherry_bomb" and self.exploded:
            if self.explosion_animation:
                size = self.explosion_size
                left = self.explosion_center[0] - size // 2
                top = self.explosion_center[1] - size // 2
                screen.draw.filled_rect(Rect((left, top), (size, size)), "white")

    def update(self):
        # 更新动画
        self.update_animation()

        if self.plant_type == "peashooter":
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.cooldown = self.cooldown_max
                # 从植物中心偏右发射豌豆
                return Pea(self.x + 30, self.y)
        elif self.plant_type == "cherry_bomb" and not self.exploded:
            # 樱桃炸弹只有在动画完成后才会爆炸
            if self.animation_complete:
                self.exploded = True
                self.explosion_animation = True
                # 播放爆炸音效
                sounds.explosion.play()
                return "explode"

        elif self.plant_type == "cherry_bomb" and self.exploded and self.explosion_animation:
            self.explosion_size += 10
            if self.explosion_size >= self.explosion_max_size:
                self.explosion_animation = False
                return "explode_final"
        return None

    def take_damage(self, amount):
        if self.plant_type == "cherry_bomb":
            return False
        self.health -= amount
        return self.health <= 0

class Zombie:
    ZOMBIE_TYPES = {
        "normal": {"health": 150, "damage": 100, "speed": 0.8},
        "conethead": {"health": 250, "damage": 80, "speed": 0.6},
        "newspaper": {"health": 150, "damage": 120, "speed": 0.7, "anger_speed": 1.2, "anger_damage": 180}
    }

    def __init__(self, lane, zombie_type="normal", reward=False):
        self.type = zombie_type
        base_stats = self.ZOMBIE_TYPES[zombie_type]

        # 根据关卡调整僵尸属性
        level_factor = 1 + (GAME_STATE['level'] - 1) * 0.2
        self.health = base_stats["health"] * level_factor
        self.damage = base_stats["damage"] * level_factor
        self.speed = base_stats["speed"] * (0.8 + (GAME_STATE['level'] - 1) * 0.1)

        self.x = WIDTH + 50
        self.lane = lane
        # 僵尸位置与植物在同一水平线上 (第0行不再使用)
        self.y = 180 + lane * 120  # 修正为格子中心位置
        self.attacking = False
        self.target = None
        self.attack_cooldown = 0
        self.reward = reward
        self.reward_type = random.choice(["sun", "attack_speed", "lives"])
        self.newspaper_intact = True
        self.attack_prepare_time = 0

        # 动画相关属性
        self.frame_index = 0
        self.animation_counter = 0
        self.animation_speed = 4  # 控制动画速度（每几帧更新一次）
        self.attack_animation_frame = 0  # 攻击动画专用帧

        # 设置行走动画帧
        if zombie_type == "newspaper":
            self.anger_speed = base_stats["anger_speed"] * level_factor
            self.anger_damage = base_stats["anger_damage"] * level_factor
            self.frames = NEWSPAPER_ZOMBIE_FRAMES
            self.angry_frames = ANGRY_NEWSPAPER_ZOMBIE_FRAMES
            # 设置攻击动画帧
            self.attack_frames = NEWSPAPER_ZOMBIE_ATTACK_FRAMES
            self.angry_attack_frames = ANGRY_NEWSPAPER_ZOMBIE_ATTACK_FRAMES
            self.width = self.frames[0].width
            self.height = self.frames[0].height
        elif zombie_type == "conethead":
            self.frames = CONEHEAD_ZOMBIE_FRAMES
            self.attack_frames = CONEHEAD_ZOMBIE_ATTACK_FRAMES
            self.width = self.frames[0].width
            self.height = self.frames[0].height
        else:  # normal
            self.frames = ZOMBIE_FRAMES
            self.attack_frames = NORMAL_ZOMBIE_ATTACK_FRAMES
            self.width = self.frames[0].width
            self.height = self.frames[0].height

    def update_animation(self):
        # 更新动画帧
        self.animation_counter += 1
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0

            # 攻击时使用攻击动画帧
            if self.attacking and self.attack_prepare_time <= 0:
                if self.type == "newspaper" and not self.newspaper_intact:
                    # 愤怒的读报僵尸攻击动画
                    self.attack_animation_frame = (self.attack_animation_frame + 1) % len(self.angry_attack_frames)
                else:
                    # 普通攻击动画
                    self.attack_animation_frame = (self.attack_animation_frame + 1) % len(self.attack_frames)
            else:
                # 行走动画
                self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self):
        # 绘制当前动画帧
        if self.attacking and self.attack_prepare_time <= 0:
            # 攻击动画
            if self.type == "newspaper" and not self.newspaper_intact:
                frame = self.angry_attack_frames[self.attack_animation_frame]
            else:
                frame = self.attack_frames[self.attack_animation_frame]
        elif self.type == "newspaper" and not self.newspaper_intact:
            # 愤怒的读报僵尸行走
            frame = self.angry_frames[self.frame_index]
        else:
            # 普通行走
            frame = self.frames[self.frame_index]

        frame.pos = (self.x, self.y)
        frame.draw()

    def update(self, plants):
        # 更新动画
        self.update_animation()

        if self.attacking:
            # 检查是否处于攻击准备阶段
            if self.attack_prepare_time > 0:
                self.attack_prepare_time -= 1
                return False

            # 检查目标植物是否仍然存在
            if self.target not in plants:
                self.attacking = False
                self.target = None
                return False

            # 如果目标是樱桃炸弹，僵尸不会攻击它
            if self.target.plant_type == "cherry_bomb":
                self.attacking = False
                self.target = None
                return False

            # 降低攻击速度，使植物能存活更久
            self.attack_cooldown -= 1
            if self.attack_cooldown <= 0:
                # 对植物造成伤害并检查是否死亡
                damage = self.damage
                if self.type == "newspaper" and not self.newspaper_intact:
                    damage = self.anger_damage

                if self.target.take_damage(damage):
                    # 植物死亡，返回死亡信号和植物对象
                    dead_plant = self.target
                    self.attacking = False
                    self.target = None
                    return "plant_died", dead_plant
                # 重置攻击冷却 - 使攻击间隔约为1秒（60帧）
                self.attack_cooldown = 60
            return False

        # 移动僵尸
        self.x -= self.speed

        # 检查是否到达地图左边界
        if self.x <= -self.width:
            GAME_STATE['lives'] -= 1
            # 播放生命值减少音效
            sounds.scream.play()
            return "reached_left"

        # 精确的碰撞检测
        self.target = None
        for plant in plants:
            # 跳过樱桃炸弹 - 僵尸不会攻击它
            if plant.plant_type == "cherry_bomb":
                continue

            # 使用更精确的矩形碰撞检测
            plant_rect = Rect(plant.x - plant.width/2, plant.y - plant.height/2, plant.width, plant.height)
            zombie_rect = Rect(self.x - self.width/2, self.y - self.height/2, self.width, self.height)

            if plant_rect.colliderect(zombie_rect):
                self.target = plant
                self.attacking = True
                self.attack_cooldown = 60  # 初始攻击冷却
                self.attack_prepare_time = 30  # 新增0.5秒攻击准备时间（30帧）
                # 重置攻击动画帧
                self.attack_animation_frame = 0
                return False

        return False

    def take_damage(self, amount):
        if self.type == "newspaper" and self.newspaper_intact:
            if self.health > self.ZOMBIE_TYPES["newspaper"]["health"] * 0.5:
                self.health -= amount
            else:
                self.newspaper_intact = False
                self.speed = self.anger_speed
                # 切换到愤怒状态动画
                self.frames = self.angry_frames
                self.frame_index = 0
                self.animation_counter = 0
                self.width = self.frames[0].width
                self.height = self.frames[0].height
        else:
            self.health -= amount
        if self.health <= 0:
            if self.reward:
                self.apply_reward()
            return True
        return False

    def apply_reward(self):
        if self.reward_type == "sun":
            GAME_STATE['sunlight'] = min(10, GAME_STATE['sunlight'] + 2)
        elif self.reward_type == "attack_speed":
            for plant in PLANTS:
                if plant.plant_type == "peashooter":
                    plant.cooldown_max = max(15, plant.cooldown_max - 5)
        elif self.reward_type == "lives":
            GAME_STATE['lives'] = min(10, GAME_STATE['lives'] + 1)

class Pea:
    def __init__(self, x, y):
        # 豌豆从植物中心偏右位置发射
        self.x = x
        self.y = y
        self.speed = 5
        self.image = pea.image

        base_damage = 5
        level_bonus = (GAME_STATE['level'] - 1) * 1
        self.damage = base_damage + level_bonus

        self.width = pea.width
        self.height = pea.height

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

    def update(self):
        self.x += self.speed
        return self.x > WIDTH

class Map:
    def __init__(self):
        self.tiles = [[False for _ in range(5)] for _ in range(5)]
        self.update_background()

    def update_background(self):
        # 根据当前关卡设置背景
        level = GAME_STATE['level']
        if level == 1:
            self.background = Actor('背景0')
        elif level == 2:
            self.background = Actor('背景1')
        elif level == 3:
            self.background = Actor('背景2')
        else:
            self.background = Actor('背景0')  # 默认背景

    def draw(self):
        self.background.draw()
        for i in range(5):
            for j in range(5):
                if not self.tiles[i][j]:
                    rect = Rect((i * 160, 120 + j * 120), (160, 120))
                    screen.draw.rect(rect, (0, 255, 0))

MAP = Map()
PEAS = []
ZOMBIES = []
PEASHOOTERS = []
PLANTS = PEASHOOTERS

def generate_map():
    for i in range(5):
        for j in range(5):
            MAP.tiles[i][j] = False

def spawn_zombie():
    if not hasattr(spawn_zombie, 'last_zombie_time'):
        spawn_zombie.last_zombie_time = 0
    current_ticks = pygame.time.get_ticks()

    # 根据关卡调整僵尸生成速度
    base_interval = 3000
    level_penalty = min(1000, GAME_STATE['level'] * 200)
    spawn_interval = max(1000, base_interval - level_penalty)

    # 检查是否达到关卡目标
    if GAME_STATE['zombies_killed'] >= 50:
        return

    if current_ticks - spawn_zombie.last_zombie_time > spawn_interval:
        spawn_zombie.last_zombie_time = current_ticks
        level = GAME_STATE['level']
        GAME_STATE['zombies_spawned'] += 1

        # 根据关卡调整僵尸类型概率
        # 普通僵尸比例随关卡下降，特殊僵尸比例上升
        normal_weight = max(0.1, 0.7 - (level - 1) * 0.15)
        conehead_weight = min(0.5, 0.2 + (level - 1) * 0.1)
        newspaper_weight = min(0.4, 0.1 + (level - 1) * 0.05)

        # 确保权重总和为1
        total = normal_weight + conehead_weight + newspaper_weight
        normal_weight /= total
        conehead_weight /= total
        newspaper_weight /= total

        weights = [normal_weight, conehead_weight, newspaper_weight]
        zombie_type = random.choices(["normal", "conethead", "newspaper"], weights=weights, k=1)[0]

        reward = random.random() < (0.15 + min(0.1, (level - 1) * 0.02))
        # 僵尸在1-4行出现，跳过第0行
        lane = random.randint(0, 3)
        ZOMBIES.append(Zombie(lane, zombie_type, reward))

def update():
    global GAME_STATE
    # 如果游戏未开始，不进行更新
    if not GAME_STATE['game_started']:
        return

    if GAME_STATE['game_over'] or GAME_STATE['victory']:
        return

    # 阳光生成速度随关卡提高
    sunlight_gain = 0.0125 * (1 + (GAME_STATE['level'] - 1) * 0.2)
    if GAME_STATE['sunlight'] < 10:
        GAME_STATE['sunlight'] += sunlight_gain
        if GAME_STATE['sunlight'] > 10:
            GAME_STATE['sunlight'] = 10

    spawn_zombie()
    peas_to_remove = []
    plants_to_remove = []

    # 检查是否有僵尸正在啃食植物
    any_chomping = False
    for zombie in ZOMBIES:
        if zombie.attacking:
            any_chomping = True
            break

    # 更新啃食音效状态 - 修复了音效播放问题
    if any_chomping:
        if not GAME_STATE['chomping']:
            sounds.chomp.play(-1)  # 开始播放啃食音效
            GAME_STATE['chomping'] = True
    else:
        if GAME_STATE['chomping']:
            sounds.chomp.stop()  # 停止啃食音效
            GAME_STATE['chomping'] = False

    # 豌豆更新
    for pea in PEAS:
        if pea.update():
            peas_to_remove.append(pea)
            continue

        # 精确的豌豆与僵尸碰撞检测
        for zombie in ZOMBIES:
            # 使用矩形碰撞检测
            pea_rect = Rect(pea.x, pea.y, pea.width, pea.height)
            zombie_rect = Rect(zombie.x - zombie.width/2, zombie.y - zombie.height/2, zombie.width, zombie.height)

            if pea_rect.colliderect(zombie_rect):
                peas_to_remove.append(pea)
                # 播放豌豆命中音效
                sounds.pea_hit.play()
                if zombie.take_damage(pea.damage):
                    ZOMBIES.remove(zombie)
                    GAME_STATE['zombies_killed'] += 1
                    # 检查是否达到当前关卡目标
                    if GAME_STATE['zombies_killed'] >= 50:
                        if GAME_STATE['level'] >= 3:
                            GAME_STATE['victory'] = True
                            # 播放胜利音效
                            sounds.victory.play()
                        else:
                            next_level()
                break

    # 植物更新
    for plant in PLANTS[:]:
        result = plant.update()
        if plant.plant_type == "cherry_bomb" and result == "explode_final":
            # 使用存储的网格坐标
            grid_x = plant.grid_x
            grid_y = plant.grid_y

            # 爆炸范围覆盖整个格子及相邻区域
            explosion_left = grid_x * 160
            explosion_top = 120 + grid_y * 120  # 修正：考虑顶部工具栏
            explosion_right = (grid_x + 1) * 160
            explosion_bottom = 120 + (grid_y + 1) * 120

            # 精确的爆炸区域检测
            zombies_to_remove = []
            for zombie in ZOMBIES:
                # 使用矩形碰撞检测
                explosion_rect = Rect(explosion_left - 20, explosion_top - 20,
                                      explosion_right - explosion_left + 40,
                                      explosion_bottom - explosion_top + 40)
                zombie_rect = Rect(zombie.x - zombie.width/2, zombie.y - zombie.height/2, zombie.width, zombie.height)

                if explosion_rect.colliderect(zombie_rect):
                    zombies_to_remove.append(zombie)
                    GAME_STATE['zombies_killed'] += 1

            for zombie in zombies_to_remove:
                if zombie in ZOMBIES:
                    ZOMBIES.remove(zombie)

            # 检查是否达到当前关卡目标
            if GAME_STATE['zombies_killed'] >= 50:
                if GAME_STATE['level'] >= 3:
                    GAME_STATE['victory'] = True
                    # 播放胜利音效
                    sounds.victory.play()
                else:
                    next_level()

            plants_to_remove.append(plant)
            if 0 <= grid_x < 5 and 0 <= grid_y < 5:
                MAP.tiles[grid_x][grid_y] = False
            continue

        elif plant.plant_type == "cherry_bomb" and plant.exploded and not plant.explosion_animation:
            plants_to_remove.append(plant)
            # 使用存储的网格坐标
            grid_x = plant.grid_x
            grid_y = plant.grid_y
            if 0 <= grid_x < 5 and 0 <= grid_y < 5:
                MAP.tiles[grid_x][grid_y] = False
            continue

        elif isinstance(result, Pea):
            PEAS.append(result)

    # 僵尸更新
    zombies_to_remove = []
    for zombie in ZOMBIES[:]:
        result = zombie.update(PLANTS)
        if result == "reached_left":
            zombies_to_remove.append(zombie)
            # 生命值减少音效已经在Zombie.update中播放
            continue
        elif isinstance(result, tuple) and result[0] == "plant_died":
            dead_plant = result[1]
            if dead_plant in PLANTS and dead_plant not in plants_to_remove:
                plants_to_remove.append(dead_plant)

    # 移除死亡的豌豆
    for pea in peas_to_remove:
        if pea in PEAS:
            PEAS.remove(pea)

    # 移除死亡的僵尸
    for zombie in zombies_to_remove:
        if zombie in ZOMBIES:
            ZOMBIES.remove(zombie)

    # 移除死亡的植物并释放地图格子
    for plant in plants_to_remove:
        if plant in PLANTS:
            PLANTS.remove(plant)
            # 使用存储的网格坐标
            grid_x = plant.grid_x
            grid_y = plant.grid_y
            # 确保网格坐标有效
            if 0 <= grid_x < 5 and 0 <= grid_y < 5:
                # 释放地图格子
                MAP.tiles[grid_x][grid_y] = False

    if GAME_STATE['lives'] <= 0:
        GAME_STATE['game_over'] = True
        # 播放失败音效
        sounds.lose.play()

def draw():
    # 如果游戏未开始，显示开始界面
    if not GAME_STATE['game_started']:
        screen.fill((0, 0, 0))
        screen.draw.text("植物大战僵尸", (WIDTH//2 - 150, HEIGHT//3 - 50), color="green", fontsize=60, fontname=FONT_NAME)
        screen.draw.text("点击任意位置开始游戏", (WIDTH//2 - 180, HEIGHT//2), color="white", fontsize=40, fontname=FONT_NAME)
        screen.draw.text(f"当前关卡: {GAME_STATE['level']}", (WIDTH//2 - 100, HEIGHT//2 + 60), color="yellow", fontsize=30, fontname=FONT_NAME)
        return

    MAP.update_background()  # 确保背景随关卡更新
    MAP.draw()

    # 绘制生命值（红心）在右上角
    for i in range(GAME_STATE['lives']):
        rect = Rect((WIDTH - 50 - i * 30, 20), (25, 25))
        screen.draw.filled_rect(rect, (255, 0, 0))

    # 绘制阳光在右下角（生命值下方）
    sun_x = WIDTH - 50
    for _ in range(min(int(GAME_STATE['sunlight']), 10)):
        screen.blit(sun.image, (sun_x, 50))
        sun_x -= 25

    # 绘制植物
    for plant in PLANTS:
        plant.draw()

    # 绘制豌豆
    for pea in PEAS:
        pea.draw()

    # 绘制僵尸
    for zombie in ZOMBIES:
        zombie.draw()

    # 左上角显示游戏信息
    level_text = f"第{GAME_STATE['level']}关"
    kills_text = f"已击败: {GAME_STATE['zombies_killed']}/50"
    screen.draw.text(level_text, (20, 20), color="white", fontsize=30, fontname=FONT_NAME)
    screen.draw.text(kills_text, (20, 50), color="white", fontsize=30, fontname=FONT_NAME)

    # 在右上角显示特殊僵尸比例信息
    level = GAME_STATE['level']
    normal_weight = max(0.1, 0.7 - (level - 1) * 0.15)
    conehead_weight = min(0.5, 0.2 + (level - 1) * 0.1)
    newspaper_weight = min(0.4, 0.1 + (level - 1) * 0.05)
    ratio_text = f"僵尸比例: 普通:{normal_weight*100:.0f}% 铁桶:{conehead_weight*100:.0f}% 读报:{newspaper_weight*100:.0f}%"
    screen.draw.text(ratio_text, (WIDTH - 450, 80), color="yellow", fontsize=20, fontname=FONT_NAME)

    if GAME_STATE['game_over']:
        screen.draw.text("游戏结束!", (WIDTH//2 - 100, HEIGHT//2 - 50), color="red", fontsize=50, fontname=FONT_NAME)
        screen.draw.text("点击任意位置重新开始", (WIDTH//2 - 150, HEIGHT//2), color="white", fontsize=30, fontname=FONT_NAME)
    if GAME_STATE['victory']:
        screen.draw.text("恭喜通关!", (WIDTH//2 - 100, HEIGHT//2 - 50), color="yellow", fontsize=50, fontname=FONT_NAME)
        screen.draw.text("点击任意位置重新开始", (WIDTH//2 - 150, HEIGHT//2), color="white", fontsize=30, fontname=FONT_NAME)

def on_mouse_down(pos):
    global GAME_STATE
    # 如果游戏未开始，点击后开始游戏
    if not GAME_STATE['game_started']:
        GAME_STATE['game_started'] = True
        return

    if GAME_STATE['game_over'] or GAME_STATE['victory']:
        reset_game()
        return

    x, y = pos
    # 只允许在草坪区域放置植物
    if 0 <= x < 800 and 120 <= y < 600:
        grid_x = int(x // 160)
        grid_y = int((y - 120) // 120)  # 考虑顶部120像素的工具栏

        # 确保在有效网格范围内
        if 0 <= grid_x < 5 and 0 <= grid_y < 5:
            if MAP.tiles[grid_x][grid_y]:
                return

            # 植物位置设为格子中央
            plant_x = grid_x * 160
            plant_y = 120 + grid_y * 120  # 考虑顶部工具栏

            # 根据关卡调整植物成本
            peashooter_cost = max(1, 2 - (GAME_STATE['level'] - 1) // 2)
            cherry_bomb_cost = max(3, 5 - (GAME_STATE['level'] - 1))

            if GAME_STATE['sunlight'] >= peashooter_cost and len(PEASHOOTERS) < 5:
                GAME_STATE['sunlight'] -= peashooter_cost
                MAP.tiles[grid_x][grid_y] = True
                new_plant = Plant(plant_x, plant_y, "peashooter", grid_x, grid_y)
                PEASHOOTERS.append(new_plant)
                # 播放种植音效
                sounds.plant.play()
            elif GAME_STATE['sunlight'] >= cherry_bomb_cost:
                GAME_STATE['sunlight'] -= cherry_bomb_cost
                MAP.tiles[grid_x][grid_y] = True
                new_plant = Plant(plant_x, plant_y, "cherry_bomb", grid_x, grid_y)
                PEASHOOTERS.append(new_plant)
                # 播放种植音效
                sounds.plant.play()

def next_level():
    global MAP, ZOMBIES, PEASHOOTERS, PLANTS, PEAS, GAME_STATE
    current_level = GAME_STATE['level']
    current_sun = GAME_STATE['sunlight']

    sun_bonus = min(10, current_sun + 2)

    GAME_STATE = {
        'sunlight': sun_bonus,
        'lives': 5,
        'zombies_killed': 0,
        'level': current_level + 1,
        'last_zombie_time': pygame.time.get_ticks(),
        'game_over': False,
        'victory': False,
        'chomping': False,
        'last_lives': 5,
        'game_started': True,  # 保持游戏开始状态
        'zombies_spawned': 0
    }
    ZOMBIES = []
    PEASHOOTERS = []
    PLANTS = PEASHOOTERS
    PEAS = []
    MAP = Map()
    generate_map()
    # 播放关卡升级音效
    sounds.victory.play()

def reset_game():
    global GAME_STATE, MAP, ZOMBIES, PEASHOOTERS, PLANTS, PEAS
    # 停止所有音效
    sounds.chomp.stop()

    # 重新开始背景音乐
    if hasattr(sounds, 'background_music'):
        sounds.background_music.stop()
        sounds.background_music.play(-1)

    GAME_STATE = {
        'sunlight': 0,
        'lives': 5,
        'zombies_killed': 0,
        'level': 1,
        'last_zombie_time': pygame.time.get_ticks(),
        'game_over': False,
        'victory': False,
        'chomping': False,
        'last_lives': 5,
        'game_started': False,  # 重置为未开始状态
        'zombies_spawned': 0
    }
    MAP = Map()
    ZOMBIES = []
    PEASHOOTERS = []
    PLANTS = PEASHOOTERS
    PEAS = []
    generate_map()

generate_map()
pgzrun.go()