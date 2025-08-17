# 导入必要的库和模块
import pgzrun  # Pygame Zero运行库
import random  # 随机数生成
import pygame  # Pygame游戏库
import time  # 时间相关功能
import os  # 操作系统相关功能

# 游戏窗口设置
WIDTH = 800  # 窗口宽度
HEIGHT = 600  # 窗口高度
TITLE = "植物大战僵尸"  # 窗口标题
FONT_NAME = "s.ttf"  # 字体文件名称

# 初始化随机数生成器
random.seed(time.time())

# 初始化Pygame混音器用于音频播放
pygame.mixer.init()

# 尝试播放背景音乐（假设已加载声音资源）
if hasattr(sounds, 'background_music'):
    sounds.background_music.play(-1)  # -1表示循环播放

# 游戏状态管理字典
GAME_STATE = {
    'sunlight': 0,          # 阳光数量
    'lives': 5,             # 剩余生命数
    'zombies_killed': 0,    # 已消灭的僵尸数量
    'level': 1,             # 当前关卡
    'last_zombie_time': 0,  # 上一次生成僵尸的时间
    'game_over': False,     # 游戏是否结束
    'victory': False,       # 是否胜利
    'chomping': False,      # 是否正在咀嚼
    'last_lives': 5,        # 上一次的生命数
    'game_started': False,  # 游戏是否已开始
    'zombies_spawned': 0    # 已生成的僵尸数量
}

# 加载基础资源图像
sun = Actor('太阳')     # 阳光图像
pea = Actor('豌豆')     # 豌豆图像

# 加载植物和僵尸的动画帧
PEASHOOTER_FRAMES = [Actor(f'豌豆射手{i}') for i in range(13)]  # 豌豆射手动画帧
CHERRY_BOMB_FRAMES = [Actor(f'樱桃炸弹{i}') for i in range(7)]  # 樱桃炸弹动画帧
ZOMBIE_FRAMES = [Actor(f'僵尸{i}') for i in range(22)]          # 普通僵尸动画帧
CONEHEAD_ZOMBIE_FRAMES = [Actor(f'铁桶僵尸{i}') for i in range(15)]  # 铁桶僵尸动画帧
NEWSPAPER_ZOMBIE_FRAMES = [Actor(f'读报僵尸{i}') for i in range(19)]  # 读报僵尸动画帧
ANGRY_NEWSPAPER_ZOMBIE_FRAMES = [Actor(f'愤怒的读报僵尸{i}') for i in range(14)]  # 愤怒读报僵尸动画帧

# 僵尸攻击动画帧
NORMAL_ZOMBIE_ATTACK_FRAMES = [Actor(f'僵尸攻击{i}') for i in range(21)]  # 普通僵尸攻击动画
CONEHEAD_ZOMBIE_ATTACK_FRAMES = [Actor(f'铁桶僵尸攻击{i}') for i in range(11)]  # 铁桶僵尸攻击动画
NEWSPAPER_ZOMBIE_ATTACK_FRAMES = [Actor(f'读报僵尸攻击{i}') for i in range(8)]  # 读报僵尸攻击动画
ANGRY_NEWSPAPER_ZOMBIE_ATTACK_FRAMES = [Actor(f'愤怒的读报僵尸攻击{i}') for i in range(7)]  # 愤怒读报僵尸攻击动画

# 植物基类
class Plant:
    def __init__(self, x, y, plant_type, grid_x, grid_y):
        self.plant_type = plant_type  # 植物类型
        self.x = x + 80              # 植物x坐标
        self.y = y + 60              # 植物y坐标
        self.grid_x = grid_x          # 植物在网格中的x位置
        self.grid_y = grid_y          # 植物在网格中的y位置
        self.frame_index = 0          # 当前动画帧索引
        self.animation_counter = 0    # 动画计数器
        self.animation_speed = 4      # 动画速度

        # 根据植物类型设置不同属性
        if plant_type == "peashooter":
            self.health = 300           # 豌豆射手生命值
            self.cooldown = 0           # 冷却时间
            self.cooldown_max = 30      # 最大冷却时间
            self.frames = PEASHOOTER_FRAMES  # 动画帧列表
            self.width = self.frames[0].width  # 宽度
            self.height = self.frames[0].height  # 高度
        elif plant_type == "cherry_bomb":
            self.health = 1000          # 樱桃炸弹生命值
            self.explosion_radius = 150 # 爆炸半径
            self.explosion_damage = 1000 # 爆炸伤害
            self.exploded = False       # 是否已爆炸
            self.frames = CHERRY_BOMB_FRAMES  # 动画帧列表
            self.explosion_time = 0     # 爆炸时间
            self.width = self.frames[0].width  # 宽度
            self.height = self.frames[0].height  # 高度
            self.explosion_animation = False  # 爆炸动画是否播放
            self.explosion_size = 0     # 爆炸大小
            self.explosion_max_size = 160  # 最大爆炸大小
            self.explosion_center = (self.x, self.y)  # 爆炸中心

    def update_animation(self):
        """更新植物动画"""
        self.animation_counter += 1
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

            # 樱桃炸弹特殊处理：动画播放到最后一帧时标记为完成
            if self.plant_type == "cherry_bomb" and not self.exploded:
                if self.frame_index == len(self.frames) - 1:
                    self.animation_complete = True

    def draw(self):
        """绘制植物"""
        if self.plant_type == "peashooter" or (self.plant_type == "cherry_bomb" and not self.exploded):
            frame = self.frames[self.frame_index]
            frame.pos = (self.x, self.y)
            frame.draw()
        elif self.plant_type == "cherry_bomb" and self.exploded:
            # 绘制樱桃炸弹爆炸效果
            if self.explosion_animation:
                size = self.explosion_size
                left = self.explosion_center[0] - size // 2
                top = self.explosion_center[1] - size // 2
                screen.draw.filled_rect(Rect((left, top), (size, size)), "white")

    def update(self):
        """更新植物状态"""
        self.update_animation()

        # 豌豆射手更新逻辑：冷却完成后发射豌豆
        if self.plant_type == "peashooter":
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.cooldown = self.cooldown_max
                return Pea(self.x + 30, self.y)  # 返回新生成的豌豆
        # 樱桃炸弹更新逻辑：动画完成后爆炸
        elif self.plant_type == "cherry_bomb" and not self.exploded:
            if self.animation_complete:
                self.exploded = True
                self.explosion_animation = True
                sounds.explosion.play()  # 播放爆炸音效
                return "explode"  # 返回爆炸标记
        # 樱桃炸弹爆炸动画更新
        elif self.plant_type == "cherry_bomb" and self.exploded and self.explosion_animation:
            self.explosion_size += 10
            if self.explosion_size >= self.explosion_max_size:
                self.explosion_animation = False
                return "explode_final"  # 返回爆炸结束标记
        return None

    def take_damage(self, amount):
        """植物受到伤害"""
        if self.plant_type == "cherry_bomb":
            return False  # 樱桃炸弹不受伤害
        self.health -= amount
        return self.health <= 0  # 返回是否死亡

# 僵尸基类
class Zombie:
    # 僵尸类型及基础属性
    ZOMBIE_TYPES = {
        "normal": {"health": 150, "damage": 100, "speed": 0.8},        # 普通僵尸
        "conethead": {"health": 250, "damage": 80, "speed": 0.6},     # 铁桶僵尸
        "newspaper": {"health": 150, "damage": 120, "speed": 0.7, "anger_speed": 1.2, "anger_damage": 180}  # 读报僵尸
    }

    def __init__(self, lane, zombie_type="normal", reward=False):
        self.type = zombie_type  # 僵尸类型
        base_stats = self.ZOMBIE_TYPES[zombie_type]  # 获取基础属性

        # 根据关卡调整属性
        level_factor = 1 + (GAME_STATE['level'] - 1) * 0.2
        self.health = base_stats["health"] * level_factor  # 生命值
        self.damage = base_stats["damage"] * level_factor  # 伤害值
        self.speed = base_stats["speed"] * (0.8 + (GAME_STATE['level'] - 1) * 0.1)  # 移动速度

        self.x = WIDTH + 50  # 初始x坐标（屏幕外右侧）
        self.lane = lane    # 所在车道
        self.y = 180 + lane * 120  # y坐标根据车道计算
        self.attacking = False  # 是否正在攻击
        self.target = None  # 攻击目标
        self.attack_cooldown = 0  # 攻击冷却时间
        self.reward = reward  # 是否是奖励僵尸
        self.reward_type = random.choice(["sun", "attack_speed", "lives"])  # 奖励类型
        self.newspaper_intact = True  # 读报僵尸报纸是否完好
        self.attack_prepare_time = 0  # 攻击准备时间

        # 动画相关属性
        self.frame_index = 0
        self.animation_counter = 0
        self.animation_speed = 4
        self.attack_animation_frame = 0

        # 根据僵尸类型设置不同属性和动画帧
        if zombie_type == "newspaper":
            self.anger_speed = base_stats["anger_speed"] * level_factor  # 愤怒时速度
            self.anger_damage = base_stats["anger_damage"] * level_factor  # 愤怒时伤害
            self.frames = NEWSPAPER_ZOMBIE_FRAMES  # 普通动画帧
            self.angry_frames = ANGRY_NEWSPAPER_ZOMBIE_FRAMES  # 愤怒动画帧
            self.attack_frames = NEWSPAPER_ZOMBIE_ATTACK_FRAMES  # 攻击动画帧
            self.angry_attack_frames = ANGRY_NEWSPAPER_ZOMBIE_ATTACK_FRAMES  # 愤怒攻击动画帧
            self.width = self.frames[0].width
            self.height = self.frames[0].height
        elif zombie_type == "conethead":
            self.frames = CONEHEAD_ZOMBIE_FRAMES
            self.attack_frames = CONEHEAD_ZOMBIE_ATTACK_FRAMES
            self.width = self.frames[0].width
            self.height = self.frames[0].height
        else:
            self.frames = ZOMBIE_FRAMES
            self.attack_frames = NORMAL_ZOMBIE_ATTACK_FRAMES
            self.width = self.frames[0].width
            self.height = self.frames[0].height

    def update_animation(self):
        """更新僵尸动画"""
        self.animation_counter += 1
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0

            # 攻击状态播放攻击动画
            if self.attacking and self.attack_prepare_time <= 0:
                if self.type == "newspaper" and not self.newspaper_intact:
                    self.attack_animation_frame = (self.attack_animation_frame + 1) % len(self.angry_attack_frames)
                else:
                    self.attack_animation_frame = (self.attack_animation_frame + 1) % len(self.attack_frames)
            else:
                self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self):
        """绘制僵尸"""
        # 根据状态选择要绘制的动画帧
        if self.attacking and self.attack_prepare_time <= 0:
            if self.type == "newspaper" and not self.newspaper_intact:
                frame = self.angry_attack_frames[self.attack_animation_frame]
            else:
                frame = self.attack_frames[self.attack_animation_frame]
        elif self.type == "newspaper" and not self.newspaper_intact:
            frame = self.angry_frames[self.frame_index]
        else:
            frame = self.frames[self.frame_index]

        frame.pos = (self.x, self.y)
        frame.draw()

    def update(self, plants):
        """更新僵尸状态"""
        self.update_animation()

        # 攻击状态处理
        if self.attacking:
            if self.attack_prepare_time > 0:
                self.attack_prepare_time -= 1
                return False  # 攻击准备中，不做其他操作

            # 检查目标是否存在
            if self.target not in plants:
                self.attacking = False
                self.target = None
                return False

            # 跳过樱桃炸弹目标
            if self.target.plant_type == "cherry_bomb":
                self.attacking = False
                self.target = None
                return False

            # 攻击冷却处理
            self.attack_cooldown -= 1
            if self.attack_cooldown <= 0:
                damage = self.damage
                # 读报僵尸愤怒状态增加伤害
                if self.type == "newspaper" and not self.newspaper_intact:
                    damage = self.anger_damage

                # 攻击植物
                if self.target.take_damage(damage):
                    dead_plant = self.target
                    self.attacking = False
                    self.target = None
                    return "plant_died", dead_plant  # 返回植物死亡事件
                self.attack_cooldown = 60  # 重置攻击冷却
            return False

        # 移动逻辑
        self.x -= self.speed

        # 到达屏幕左侧，减少生命
        if self.x <= -self.width:
            GAME_STATE['lives'] -= 1
            sounds.scream.play()  # 播放尖叫音效
            return "reached_left"  # 返回到达左侧事件

        # 寻找攻击目标
        self.target = None
        for plant in plants:
            if plant.plant_type == "cherry_bomb":
                continue

            # 检测僵尸与植物碰撞
            plant_rect = Rect(plant.x - plant.width/2, plant.y - plant.height/2, plant.width, plant.height)
            zombie_rect = Rect(self.x - self.width/2, self.y - self.height/2, self.width, self.height)

            if plant_rect.colliderect(zombie_rect):
                self.target = plant
                self.attacking = True
                self.attack_cooldown = 60
                self.attack_prepare_time = 30
                self.attack_animation_frame = 0
                return False

        return False

    def take_damage(self, amount):
        """僵尸受到伤害"""
        # 读报僵尸特殊处理：报纸破损后进入愤怒状态
        if self.type == "newspaper" and self.newspaper_intact:
            if self.health > self.ZOMBIES_TYPES["newspaper"]["health"] * 0.5:
                self.health -= amount
            else:
                self.newspaper_intact = False
                self.speed = self.anger_speed
                self.frames = self.angry_frames
                self.frame_index = 0
                self.animation_counter = 0
                self.width = self.frames[0].width
                self.height = self.frames[0].height
        else:
            self.health -= amount
        # 返回是否死亡
        if self.health <= 0:
            if self.reward:
                self.apply_reward()  # 应用奖励
            return True
        return False

    def apply_reward(self):
        """应用奖励效果"""
        if self.reward_type == "sun":
            GAME_STATE['sunlight'] = min(10, GAME_STATE['sunlight'] + 2)  # 增加阳光
        elif self.reward_type == "attack_speed":
            # 增加豌豆射手攻击速度
            for plant in PLANTS:
                if plant.plant_type == "peashooter":
                    plant.cooldown_max = max(15, plant.cooldown_max - 5)
        elif self.reward_type == "lives":
            GAME_STATE['lives'] = min(10, GAME_STATE['lives'] + 1)  # 增加生命

# 豌豆类
class Pea:
    def __init__(self, x, y):
        self.x = x            # 豌豆x坐标
        self.y = y            # 豌豆y坐标
        self.speed = 5        # 豌豆速度
        self.image = pea.image  # 豌豆图像

        # 根据关卡调整豌豆伤害
        base_damage = 5
        level_bonus = (GAME_STATE['level'] - 1) * 1
        self.damage = base_damage + level_bonus  # 豌豆伤害值

        self.width = pea.width  # 宽度
        self.height = pea.height  # 高度

    def draw(self):
        """绘制豌豆"""
        screen.blit(self.image, (self.x, self.y))

    def update(self):
        """更新豌豆状态"""
        self.x += self.speed  # 豌豆移动
        return self.x > WIDTH  # 返回是否超出屏幕

# 地图类
class Map:
    def __init__(self):
        self.tiles = [[False for _ in range(5)] for _ in range(5)]  # 地图网格状态
        self.update_background()  # 更新背景

    def update_background(self):
        """根据关卡更新背景"""
        level = GAME_STATE['level']
        if level == 1:
            self.background = Actor('背景0')
        elif level == 2:
            self.background = Actor('背景1')
        elif level == 3:
            self.background = Actor('背景2')
        else:
            self.background = Actor('背景0')

    def draw(self):
        """绘制地图"""
        self.background.draw()  # 绘制背景
        # 绘制可种植区域网格
        for i in range(5):
            for j in range(5):
                if not self.tiles[i][j]:
                    rect = Rect((i * 160, 120 + j * 120), (160, 120))
                    screen.draw.rect(rect, (0, 255, 0))  # 绿色框表示可种植区域

# 初始化游戏对象
MAP = Map()  # 地图对象
PEAS = []    # 豌豆列表
ZOMBIES = [] # 僵尸列表
PEASHOOTERS = []  # 豌豆射手列表
PLANTS = PEASHOOTERS  # 植物列表（当前只有豌豆射手）

def generate_map():
    """生成地图"""
    for i in range(5):
        for j in range(5):
            MAP.tiles[i][j] = False  # 初始所有格子都不可种植

def spawn_zombie():
    """生成僵尸"""
    if not hasattr(spawn_zombie, 'last_zombie_time'):
        spawn_zombie.last_zombie_time = 0
    current_ticks = pygame.time.get_ticks()  # 获取当前时间（毫秒）

    # 计算僵尸生成间隔（随关卡提升而缩短）
    base_interval = 3000
    level_penalty = min(1000, GAME_STATE['level'] * 200)
    spawn_interval = max(1000, base_interval - level_penalty)

    # 限制僵尸生成数量
    if GAME_STATE['zombies_killed'] >= 50:
        return

    # 达到生成间隔时间则生成新僵尸
    if current_ticks - spawn_zombie.last_zombie_time > spawn_interval:
        spawn_zombie.last_zombie_time = current_ticks
        level = GAME_STATE['level']
        GAME_STATE['zombies_spawned'] += 1

        # 根据关卡调整不同类型僵尸的生成概率
        normal_weight = max(0.1, 0.7 - (level - 1) * 0.15)
        conehead_weight = min(0.5, 0.2 + (level - 1) * 0.1)
        newspaper_weight = min(0.4, 0.1 + (level - 1) * 0.05)

        # 计算概率权重
        total = normal_weight + conehead_weight + newspaper_weight
        normal_weight /= total
        conehead_weight /= total
        newspaper_weight /= total

        # 根据概率选择僵尸类型
        weights = [normal_weight, conehead_weight, newspaper_weight]
        zombie_type = random.choices(["normal", "conethead", "newspaper"], weights=weights, k=1)[0]

        # 概率生成奖励僵尸
        reward = random.random() < (0.15 + min(0.1, (level - 1) * 0.02))
        lane = random.randint(0, 3)  # 随机选择车道
        ZOMBIES.append(Zombie(lane, zombie_type, reward))  # 添加新僵尸到列表

def update():
    """游戏逻辑更新函数"""
    global GAME_STATE
    if not GAME_STATE['game_started']:
        return  # 游戏未开始，不更新

    if GAME_STATE['game_over'] or GAME_STATE['victory']:
        return  # 游戏结束或胜利，不更新

    # 自动生成阳光（随关卡增加）
    sunlight_gain = 0.0125 * (1 + (GAME_STATE['level'] - 1) * 0.2)
    if GAME_STATE['sunlight'] < 10:
        GAME_STATE['sunlight'] += sunlight_gain
        if GAME_STATE['sunlight'] > 10:
            GAME_STATE['sunlight'] = 10  # 阳光上限为10

    spawn_zombie()  # 生成僵尸

    peas_to_remove = []  # 要移除的豌豆列表
    plants_to_remove = []  # 要移除的植物列表

    # 检查是否有僵尸在攻击（用于播放咀嚼音效）
    any_chomping = False
    for zombie in ZOMBIES:
        if zombie.attacking:
            any_chomping = True
            break

    # 控制咀嚼音效播放
    if any_chomping:
        if not GAME_STATE['chomping']:
            sounds.chomp.play(-1)  # 循环播放咀嚼音效
            GAME_STATE['chomping'] = True
    else:
        if GAME_STATE['chomping']:
            sounds.chomp.stop()  # 停止咀嚼音效
            GAME_STATE['chomping'] = False

    # 更新豌豆状态
    for pea in PEAS:
        if pea.update():
            peas_to_remove.append(pea)  # 超出屏幕则标记为移除
            continue

        # 豌豆与僵尸碰撞检测
        for zombie in ZOMBIES:
            pea_rect = Rect(pea.x, pea.y, pea.width, pea.height)
            zombie_rect = Rect(zombie.x - zombie.width/2, zombie.y - zombie.height/2, zombie.width, zombie.height)

            if pea_rect.colliderect(zombie_rect):
                peas_to_remove.append(pea)  # 击中僵尸则标记豌豆为移除
                sounds.pea_hit.play()  # 播放豌豆击中音效
                if zombie.take_damage(pea.damage):
                    ZOMBIES.remove(zombie)  # 僵尸死亡则移除
                    GAME_STATE['zombies_killed'] += 1  # 增加击杀数
                    # 检查是否完成关卡目标
                    if GAME_STATE['zombies_killed'] >= 50:
                        if GAME_STATE['level'] >= 3:
                            GAME_STATE['victory'] = True  # 完成所有关卡，游戏胜利
                            sounds.victory.play()  # 播放胜利音效
                        else:
                            next_level()  # 进入下一关
                break

    # 更新植物状态
    for plant in PLANTS[:]:
        result = plant.update()
        # 樱桃炸弹爆炸结束处理
        if plant.plant_type == "cherry_bomb" and result == "explode_final":
            grid_x = plant.grid_x
            grid_y = plant.grid_y

            # 计算爆炸范围
            explosion_left = grid_x * 160
            explosion_top = 120 + grid_y * 120
            explosion_right = (grid_x + 1) * 160
            explosion_bottom = 120 + (grid_y + 1) * 120

            # 处理爆炸范围内的僵尸
            zombies_to_remove = []
            for zombie in ZOMBIES:
                explosion_rect = Rect(explosion_left - 20, explosion_top - 20,
                                      explosion_right - explosion_left + 40,
                                      explosion_bottom - explosion_top + 40)
                zombie_rect = Rect(zombie.x - zombie.width/2, zombie.y - zombie.height/2, zombie.width, zombie.height)

                if explosion_rect.colliderect(zombie_rect):
                    zombies_to_remove.append(zombie)
                    GAME_STATE['zombies_killed'] += 1  # 增加击杀数

            # 移除被爆炸消灭的僵尸
            for zombie in zombies_to_remove:
                if zombie in ZOMBIES:
                    ZOMBIES.remove(zombie)

            # 检查是否完成关卡目标
            if GAME_STATE['zombies_killed'] >= 50:
                if GAME_STATE['level'] >= 3:
                    GAME_STATE['victory'] = True
                    sounds.victory.play()
                else:
                    next_level()

            plants_to_remove.append(plant)  # 移除爆炸后的樱桃炸弹
            if 0 <= grid_x < 5 and 0 <= grid_y < 5:
                MAP.tiles[grid_x][grid_y] = False  # 标记格子为可种植
            continue

        # 移除爆炸后的樱桃炸弹
        elif plant.plant_type == "cherry_bomb" and plant.exploded and not plant.explosion_animation:
            plants_to_remove.append(plant)
            grid_x = plant.grid_x
            grid_y = plant.grid_y
            if 0 <= grid_x < 5 and 0 <= grid_y < 5:
                MAP.tiles[grid_x][grid_y] = False
            continue

        # 豌豆射手发射豌豆
        elif isinstance(result, Pea):
            PEAS.append(result)  # 添加新豌豆到列表

    # 更新僵尸状态
    zombies_to_remove = []
    for zombie in ZOMBIES[:]:
        result = zombie.update(PLANTS)
        if result == "reached_left":
            zombies_to_remove.append(zombie)  # 到达左侧则移除
            continue
        elif isinstance(result, tuple) and result[0] == "plant_died":
            dead_plant = result[1]
            if dead_plant in PLANTS and dead_plant not in plants_to_remove:
                plants_to_remove.append(dead_plant)  # 植物死亡则标记为移除

    # 执行移除操作
    for pea in peas_to_remove:
        if pea in PEAS:
            PEAS.remove(pea)

    for zombie in zombies_to_remove:
        if zombie in ZOMBIES:
            ZOMBIES.remove(zombie)

    for plant in plants_to_remove:
        if plant in PLANTS:
            PLANTS.remove(plant)
            grid_x = plant.grid_x
            grid_y = plant.grid_y
            if 0 <= grid_x < 5 and 0 <= grid_y < 5:
                MAP.tiles[grid_x][grid_y] = False  # 标记格子为可种植

    # 检查游戏是否结束
    if GAME_STATE['lives'] <= 0:
        GAME_STATE['game_over'] = True
        sounds.lose.play()  # 播放失败音效

def draw():
    """游戏画面渲染函数"""
    if not GAME_STATE['game_started']:
        # 游戏未开始界面
        screen.fill((0, 0, 0))
        screen.draw.text("植物大战僵尸", (WIDTH//2 - 150, HEIGHT//3 - 50), color="green", fontsize=60, fontname=FONT_NAME)
        screen.draw.text("点击任意位置开始游戏", (WIDTH//2 - 180, HEIGHT//2), color="white", fontsize=40, fontname=FONT_NAME)
        screen.draw.text(f"当前关卡: {GAME_STATE['level']}", (WIDTH//2 - 100, HEIGHT//2 + 60), color="yellow", fontsize=30, fontname=FONT_NAME)
        return

    # 更新并绘制地图
    MAP.update_background()
    MAP.draw()

    # 绘制生命值
    for i in range(GAME_STATE['lives']):
        rect = Rect((WIDTH - 50 - i * 30, 20), (25, 25))
        screen.draw.filled_rect(rect, (255, 0, 0))  # 红色方块表示生命

    # 绘制阳光
    sun_x = WIDTH - 50
    for _ in range(min(int(GAME_STATE['sunlight']), 10)):
        screen.blit(sun.image, (sun_x, 50))
        sun_x -= 25  # 逐个绘制阳光图标

    # 绘制所有植物
    for plant in PLANTS:
        plant.draw()

    # 绘制所有豌豆
    for pea in PEAS:
        pea.draw()

    # 绘制所有僵尸
    for zombie in ZOMBIES:
        zombie.draw()

    # 绘制游戏信息
    level_text = f"第{GAME_STATE['level']}关"
    kills_text = f"已击败: {GAME_STATE['zombies_killed']}/50"
    screen.draw.text(level_text, (20, 20), color="white", fontsize=30, fontname=FONT_NAME)
    screen.draw.text(kills_text, (20, 50), color="white", fontsize=30, fontname=FONT_NAME)

    # 绘制僵尸生成比例
    level = GAME_STATE['level']
    normal_weight = max(0.1, 0.7 - (level - 1) * 0.15)
    conehead_weight = min(0.5, 0.2 + (level - 1) * 0.1)
    newspaper_weight = min(0.4, 0.1 + (level - 1) * 0.05)
    ratio_text = f"僵尸比例: 普通:{normal_weight*100:.0f}% 铁桶:{conehead_weight*100:.0f}% 读报:{newspaper_weight*100:.0f}%"
    screen.draw.text(ratio_text, (WIDTH - 450, 80), color="yellow", fontsize=20, fontname=FONT_NAME)

    # 绘制游戏结束或胜利界面
    if GAME_STATE['game_over']:
        screen.draw.text("游戏结束!", (WIDTH//2 - 100, HEIGHT//2 - 50), color="red", fontsize=50, fontname=FONT_NAME)
        screen.draw.text("点击任意位置重新开始", (WIDTH//2 - 150, HEIGHT//2), color="white", fontsize=30, fontname=FONT_NAME)
    if GAME_STATE['victory']:
        screen.draw.text("恭喜通关!", (WIDTH//2 - 100, HEIGHT//2 - 50), color="yellow", fontsize=50, fontname=FONT_NAME)
        screen.draw.text("点击任意位置重新开始", (WIDTH//2 - 150, HEIGHT//2), color="white", fontsize=30, fontname=FONT_NAME)

def on_mouse_down(pos):
    """鼠标点击事件处理"""
    global GAME_STATE
    if not GAME_STATE['game_started']:
        GAME_STATE['game_started'] = True  # 开始游戏
        return

    if GAME_STATE['game_over'] or GAME_STATE['victory']:
        reset_game()  # 重置游戏
        return

    # 处理种植植物逻辑
    x, y = pos
    if 0 <= x < 800 and 120 <= y < 600:
        grid_x = int(x // 160)
        grid_y = int((y - 120) // 120)

        if 0 <= grid_x < 5 and 0 <= grid_y < 5:
            if MAP.tiles[grid_x][grid_y]:
                return  # 已有植物则不种植

            plant_x = grid_x * 160
            plant_y = 120 + grid_y * 120

            # 根据关卡调整植物价格
            peashooter_cost = max(1, 2 - (GAME_STATE['level'] - 1) // 2)
            cherry_bomb_cost = max(3, 5 - (GAME_STATE['level'] - 1))

            # 种植豌豆射手（阳光足够且数量未达上限）
            if GAME_STATE['sunlight'] >= peashooter_cost and len(PEASHOOTERS) < 5:
                GAME_STATE['sunlight'] -= peashooter_cost
                MAP.tiles[grid_x][grid_y] = True
                new_plant = Plant(plant_x, plant_y, "peashooter", grid_x, grid_y)
                PEASHOOTERS.append(new_plant)
                sounds.plant.play()  # 播放种植音效
            # 种植樱桃炸弹（阳光足够）
            elif GAME_STATE['sunlight'] >= cherry_bomb_cost:
                GAME_STATE['sunlight'] -= cherry_bomb_cost
                MAP.tiles[grid_x][grid_y] = True
                new_plant = Plant(plant_x, plant_y, "cherry_bomb", grid_x, grid_y)
                PEASHOOTERS.append(new_plant)
                sounds.plant.play()  # 播放种植音效

def next_level():
    """进入下一关"""
    global MAP, ZOMBIES, PEASHOOTERS, PLANTS, PEAS, GAME_STATE
    current_level = GAME_STATE['level']
    current_sun = GAME_STATE['sunlight']

    # 计算过关奖励阳光
    sun_bonus = min(10, current_sun + 2)

    # 重置游戏状态
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
        'game_started': True,
        'zombies_spawned': 0
    }
    ZOMBIES = []
    PEASHOOTERS = []
    PLANTS = PEASHOOTERS
    PEAS = []
    MAP = Map()
    generate_map()
    sounds.victory.play()  # 播放胜利音效

def reset_game():
    """重置游戏"""
    global GAME_STATE, MAP, ZOMBIES, PEASHOOTERS, PLANTS, PEAS
    sounds.chomp.stop()  # 停止咀嚼音效

    # 停止背景音乐并重新播放
    if hasattr(sounds, 'background_music'):
        sounds.background_music.stop()
        sounds.background_music.play(-1)

    # 重置游戏状态为初始值
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
        'game_started': False,
        'zombies_spawned': 0
    }
    MAP = Map()
    ZOMBIES = []
    PEASHOOTERS = []
    PLANTS = PEASHOOTERS
    PEAS = []
    generate_map()  # 生成初始地图

# 初始化地图
generate_map()
# 启动游戏
pgzrun.go()