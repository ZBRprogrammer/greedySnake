import tkinter as tk
from math import floor
from queue import Queue
from random import randint
from tkinter import *
from tkinter import messagebox
from encrypt import *
import pygame.key
from pygame import Rect
from pygame import Surface
from pygame import draw
from pygame.time import Clock

import constants


def on_entry_click(entry, default_text):
    if entry.get() == default_text:
        entry.configure(fg='black')
        entry.delete(0, tk.END)
        entry.insert(0, '')


def on_entry_unfocus(entry, default_text):
    if entry.get() == '':
        entry.configure(fg='gray')
        entry.delete(0, tk.END)
        entry.insert(0, default_text)


def entry_template(parent, default_text) -> Entry:
    # create entry
    entry = Entry(parent, width=constants.ENTRY_WIDTH, fg='gray')
    # set default text
    entry.insert(0, default_text)
    # bind functions
    entry.bind('<FocusIn>', lambda event: on_entry_click(entry, default_text))
    entry.bind('<FocusOut>', lambda event: on_entry_unfocus(entry, default_text))

    return entry


def frame_template(parent, text, *args) -> tuple[Frame, IntVar]:
    # create frame
    frame = Frame(parent)
    # set text
    Label(frame, text=text).pack(side="left")
    # add buttons
    var = IntVar()
    var.set(-1)  # default choice
    for i, arg in enumerate(args):
        Radiobutton(frame, text=arg, variable=var, value=i).pack(side="left")
    return frame, var


def get_rect(self_pos: tuple[int, int], target_pos: tuple[int, int] | None = None) -> Rect:
    x1 = self_pos[0] * constants.BLOCK_SIZE + constants.BLOCK_INTERVAL
    y1 = self_pos[1] * constants.BLOCK_SIZE + constants.BLOCK_INTERVAL
    width = constants.BLOCK_SIZE - constants.BLOCK_INTERVAL
    height = constants.BLOCK_SIZE - constants.BLOCK_INTERVAL
    if target_pos is None:
        return Rect(x1, y1, width, height)
    if (self_pos[0] + 1 + game_controller.map_width) % game_controller.map_width == target_pos[0]:  # connect to right
        width += constants.BLOCK_INTERVAL
    elif (self_pos[1] + 1 + game_controller.map_height) % game_controller.map_height == target_pos[
        1]:  # connect to down
        height += constants.BLOCK_INTERVAL
    elif (self_pos[0] - 1 + game_controller.map_width) % game_controller.map_width == target_pos[0]:  # connect to left
        x1 -= constants.BLOCK_INTERVAL
        width += constants.BLOCK_INTERVAL
    elif (self_pos[1] - 1 + game_controller.map_height) % game_controller.map_height == target_pos[1]:  # connect to up
        y1 -= constants.BLOCK_INTERVAL
        height += constants.BLOCK_INTERVAL
    return Rect(x1, y1, width, height)


class GameController:
    class Food:
        def __init__(self, pos: tuple[int, int], value: int, bonus: bool):
            self.pos = pos
            self.value = value
            self.is_bonus = bonus
            self.color = constants.FOOD_COLOR_LIST[0]

        def value_decline(self):
            self.value -= 1
            self.get_color()

        def get_color(self):
            self.color = constants.FOOD_COLOR_LIST[
                min((self.value - constants.FOOD_VALUE_MIN) * len(constants.FOOD_COLOR_LIST) // (
                        constants.FOOD_VALUE_MAX - constants.FOOD_VALUE_MIN + 1),
                    len(constants.FOOD_COLOR_LIST) - 1)]

    class Snake:
        def __init__(self, head: tuple[int, int], body: list[tuple[int, int]], head_color: str, body_color: str):
            self.snake_list = [head, *body]
            self.velocity = (0, 0)
            self.head_color = head_color
            self.body_color = body_color

        def move(self):
            snake_head_pos = self.snake_list[0]
            new_pos = ((snake_head_pos[0] + self.velocity[0] + game_controller.map_width) % game_controller.map_width,
                       (snake_head_pos[1] + self.velocity[1] + game_controller.map_height) % game_controller.map_height)
            self.snake_list.insert(0, new_pos)

        def pop(self):
            self.snake_list.pop(-1)

        def change_direction(self, new_velocity: tuple[int, int]):
            self.velocity = new_velocity

    def __init__(self):
        self.score = 0
        self.ticks = 0
        self.screen = Surface((0, 0))
        self.width, self.height = (0, 0)
        self.map_width, self.map_height = (0, 0)
        self.run_interval = 0
        self.running = False
        self.snake_moving = False
        self.clock = Clock()
        self.snake = self.Snake((0, 0), [], '',
                                '')
        self.food = self.Food((0, 0), 0, False)
        self.recorded_key_state = self.is_key_down = False
        self.recorded_key_pressed = None
        self.tmp_direction = (0, 0)
        self.running_tick = 0
        self.automated = False
        self.pausing = False
        self.about_to_respawn = False
        self.high_score = 0

    def tick(self):
        self.ticks += 1
        self.ticks %= constants.FPS
        if self.ticks % self.run_interval == 0:
            self.running_tick += 1

    def initialize(self):
        self.high_score = get_high_score()
        self.score = 0
        self.snake.snake_list = [(randint(0, self.map_width), randint(0, self.map_height))]
        self.snake.velocity = self.tmp_direction = constants.DIRECTIONS[randint(0, 3)]
        self.snake_moving = True
        self.pausing = False
        self.about_to_respawn = False
        self.summon_new_food()

    def change_direction(self, new_velocity: tuple[int, int]):
        self.tmp_direction = new_velocity

    def snake_move(self):
        if self.ticks % self.run_interval != 0:
            return
        self.snake.velocity = self.tmp_direction
        self.snake.move()
        if self.snake.snake_list[0] != self.food.pos:
            self.snake.pop()
        else:
            self.score += self.food.value
            self.summon_new_food()
        for i in self.snake.snake_list[1:]:
            if i == self.snake.snake_list[0]:
                self.snake_moving = False

    def summon_new_food(self):
        while True:
            self.food.pos = (randint(0, self.map_width - 1),  # x pos
                             randint(0, self.map_height - 1))  # y pos
            valid = True
            for body in self.snake.snake_list:
                if self.food.pos == body:
                    valid = False
                    break
            if valid:
                break
        self.food.is_bonus = ((self.score + 1) / constants.FOOD_BONUS_INTERVAL).is_integer() & (not self.food.is_bonus)
        self.food.value = constants.FOOD_VALUE_MAX if self.food.is_bonus else 1
        self.food.get_color()

    def tick_food_value(self):
        if not self.food.is_bonus:
            return
        if self.running_tick % constants.FOOD_BONUS_DECLINE_INTERVAL == 0:
            self.food.value_decline()
            if self.food.value < constants.FOOD_DISAPPEAR_THRESHOLD:
                self.summon_new_food()

    def get_key_respond(self, key_pressed: pygame.key.ScancodeWrapper):
        # check if key_pressed changed
        if self.recorded_key_state != self.is_key_down:
            if self.is_key_down:  # record key_pressed
                self.recorded_key_pressed = key_pressed
            if self.recorded_key_state:  # wait for key_up
                for key, value in constants.KEY_DIRECTION_MAPPING.items():
                    if self.recorded_key_pressed[key] and value <= 3 and tuple(
                            map(sum, zip(self.snake.velocity, constants.DIRECTIONS[value]))) != (0, 0):
                        # tuple(map(sum,zip(self.snake.velocity,constants.DIRECTIONS[value]))) != (0,0) -> check if directions are opposing
                        self.tmp_direction = constants.DIRECTIONS[value]  # record input direction
                        break
                    elif self.recorded_key_pressed[key] and value == 4:
                        print(key,value)
                        self.pausing = not self.pausing
                        break
                    elif self.recorded_key_pressed[key] and value == 5 and self.snake_moving == False:
                        self.about_to_respawn = True
                        break
            self.recorded_key_state = self.is_key_down  # change state

    def draw(self):
        for i in range(self.map_width):
            for j in range(self.map_height):
                draw.rect(self.screen, constants.BACKGROUND_COLOR, get_rect((i, j)))
        if len(self.snake.snake_list) == 1:
            draw.rect(self.screen, self.snake.head_color, get_rect(self.snake.snake_list[0]))
        elif len(self.snake.snake_list) == 2:
            draw.rect(self.screen, self.snake.head_color, get_rect(self.snake.snake_list[0], self.snake.snake_list[1]))
            draw.rect(self.screen, self.snake.body_color, get_rect(self.snake.snake_list[1], self.snake.snake_list[0]))
        else:
            draw.rect(self.screen, self.snake.head_color, get_rect(self.snake.snake_list[0], self.snake.snake_list[1]))
            for i in range(1, len(self.snake.snake_list) - 1):
                draw.rect(self.screen, self.snake.body_color,
                          get_rect(self.snake.snake_list[i], self.snake.snake_list[i - 1]))
                draw.rect(self.screen, self.snake.body_color,
                          get_rect(self.snake.snake_list[i], self.snake.snake_list[i + 1]))
            draw.rect(self.screen, self.snake.body_color,
                      get_rect(self.snake.snake_list[-1], self.snake.snake_list[-2]))
        draw.rect(self.screen, self.food.color, get_rect(self.food.pos))


class GUI:
    def __init__(self):
        self.tk = Tk()
        self.size_var = IntVar()
        self.difficulty_var = IntVar()
        self.head_color_var = StringVar()
        self.body_color_var = StringVar()
        self.is_automated_var = BooleanVar()
        self.width_entry = Entry()
        self.height_entry = Entry()
        self.speed_entry = Entry()
        self.tk.protocol("WM_DELETE_WINDOW", self.quit)

    def run(self):
        self.construct_lay_out()
        self.tk.mainloop()

    def quit(self):
        self.tk.destroy()
        exit(0)

    def validate(self):
        if 0 <= self.is_automated_var.get() <= 2:
            game_controller.automated = bool(self.is_automated_var.get())
        else:
            messagebox.showerror(title='Error', message='Automation input is invalid')
            return
        if 0 <= self.size_var.get() <= 2:
            game_controller.map_width, game_controller.map_height = constants.WIDTH_HEIGHT_LIST[self.size_var.get()]
        elif self.size_var.get() == 3 and self.width_entry.get().isdigit() and self.height_entry.get().isdigit() and int(
                self.width_entry.get()) > 0 and int(self.height_entry.get()) > 0:
            game_controller.map_width, game_controller.map_height = int(self.width_entry.get()), int(
                self.height_entry.get())
        else:
            messagebox.showerror(title='Error', message='Size input is invalid')
            return
        if 0 <= self.difficulty_var.get() <= 2:
            game_controller.run_interval = constants.SPEED_LIST[self.difficulty_var.get()]
        elif self.difficulty_var.get() == 3 and self.speed_entry.get().isdigit() and int(self.speed_entry.get()) > 0:
            game_controller.run_interval = int(self.speed_entry.get())
        else:
            messagebox.showerror(title='Error', message='Speed input is invalid')
            return
        if self.head_color_var.get() != self.body_color_var.get():
            game_controller.snake.head_color = self.head_color_var.get()
            game_controller.snake.body_color = self.body_color_var.get()
        else:
            messagebox.showerror(title='Error', message='Head color and Body color cannot be the same')
            return
        self.tk.destroy()

    def construct_automation_layout(self, parent) -> Frame:
        # automation frame
        automation_frame, self.is_automated_var = frame_template(parent, constants.INPUT_AUTOMATION_CONFIG,
                                                                 constants.INPUT_AUTOMATION_NO,
                                                                 constants.INPUT_AUTOMATION_YES)
        return automation_frame

    def construct_size_layout(self, parent) -> Frame:
        # size frame
        size_frame, self.size_var = frame_template(parent, constants.INPUT_SIZE_CONFIG, constants.INPUT_SIZE_SMALL,
                                                   constants.INPUT_SIZE_MEDIUM, constants.INPUT_SIZE_LARGE,
                                                   constants.INPUT_SIZE_CUSTOM)
        # entries
        # width
        self.width_entry = entry_template(size_frame, constants.CUSTOM_ENTRY_WIDTH_DEFAULT)
        self.width_entry.pack(side='left')
        # label '×'
        Label(size_frame, text=constants.SEPARATE_CHAR).pack(side='left')
        # height
        self.height_entry = entry_template(size_frame, constants.CUSTOM_ENTRY_HEIGHT_DEFAULT)
        self.height_entry.pack(side='left')
        return size_frame

    def construct_difficulty_layout(self, parent) -> Frame:
        # difficulty frame
        difficulty_frame, self.difficulty_var = frame_template(parent, constants.INPUT_DIFFICULTY_CONFIG,
                                                               constants.INPUT_DIFFICULTY_EASY,
                                                               constants.INPUT_DIFFICULTY_NORMAL,
                                                               constants.INPUT_DIFFICULTY_HARD,
                                                               constants.INPUT_DIFFICULTY_CUSTOM)
        # entries
        self.speed_entry = entry_template(difficulty_frame, constants.CUSTOM_ENTRY_DIFFICULTY)
        self.speed_entry.pack(side='left')
        return difficulty_frame

    def construct_color_layout(self, parent) -> Frame:
        # create color frame
        color_frame = Frame(parent)
        # set head color
        Label(color_frame, text=constants.INPUT_SNAKE_HEAD_COLOR_CONFIG).pack(side='left')
        self.head_color_var = StringVar()
        self.head_color_var.set(constants.DEFAULT_COLOR)
        OptionMenu(color_frame, self.head_color_var, constants.DEFAULT_COLOR, *constants.COLOR_LIST).pack(side='left')
        # set body color
        Label(color_frame, text=constants.INPUT_SNAKE_BODY_COLOR_CONFIG).pack(side='left')
        self.body_color_var = StringVar()
        self.body_color_var.set(constants.DEFAULT_COLOR)
        OptionMenu(color_frame, self.body_color_var, constants.DEFAULT_COLOR, *constants.COLOR_LIST).pack(side='left')

        return color_frame

    def construct_button_layout(self, parent) -> Frame:
        button_frame = Frame(parent)
        Button(button_frame, text=constants.CHECK_BUTTON_TEXT, command=self.validate).pack(side='left', expand=True)
        Button(button_frame, text=constants.QUIT_BUTTON_TEXT, command=self.quit).pack(side='left', expand=True)
        return button_frame

    def construct_lay_out(self):
        # pin window to the top
        self.tk.attributes("-topmost", 1)
        # set window size and align window to center
        screen_width, screen_height = self.get_screen_size()
        self.tk.geometry(
            f"{constants.INPUT_WIDTH}x{constants.INPUT_HEIGHT}+{(screen_width - constants.INPUT_WIDTH) // 2}+{(screen_height - constants.INPUT_HEIGHT) // 2}")
        # strict window size
        self.tk.resizable(False, False)
        # set title
        self.tk.title(constants.INPUT_TITLE)

        # config frame
        main_frame = LabelFrame(self.tk, text=constants.INPUT_SUBTITLE)
        main_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.construct_automation_layout(main_frame).pack(fill='x', expand=True)
        # size frame
        self.construct_size_layout(main_frame).pack(fill='x', expand=True)
        # difficulty frame
        self.construct_difficulty_layout(main_frame).pack(fill='x', expand=True)
        # color frame
        self.construct_color_layout(main_frame).pack(fill='x', expand=True)
        # button frame
        self.construct_button_layout(main_frame).pack(fill='x', expand=True)

    def get_screen_size(self) -> tuple[int, int]:
        return self.tk.winfo_screenwidth(), self.tk.winfo_screenheight()


class AutoPlay:
    class HamiltonianCycle:
        def __init__(self, cycle: list[tuple[int, int]], pos_to_index: dict[tuple[int, int], int],
                     next_pos: dict[tuple[int, int], tuple[int, int]],
                     prev_pos: dict[tuple[int, int], tuple[int, int]]):
            self.cycle = cycle  # list of pos in cycle
            self.pos_to_index = pos_to_index  # mapping from pos to index
            self.next_pos = next_pos
            self.prev_pos = prev_pos

    def __init__(self, map_size: tuple[int, int]):
        self.map_size = map_size
        self.grid_area = map_size[0] * map_size[1]
        self.L0 = floor(self.grid_area / 2)
        self.h_cycle_cache = None
        self.consecutive_no_food_moves = 0  # 连续未吃到食物的移动次数
        self.max_consecutive_no_food = 20  # 最大连续未吃到食物的移动次数

    def get_hamiltonian_cycle(self) -> HamiltonianCycle:
        """获取或计算哈密顿环"""
        if self.h_cycle_cache is None:
            self.h_cycle_cache = self._compute_hamiltonian_cycle()
        return self.h_cycle_cache

    def _compute_hamiltonian_cycle(self) -> HamiltonianCycle:
        """计算哈密顿环"""
        width, height = self.map_size
        grid_area = self.grid_area
        cycle = []
        pos_to_index = {}

        # 使用代数构造法
        current = (0, 0)
        for i in range(grid_area):
            cycle.append(current)
            pos_to_index[current] = i

            # 计算下一个位置: φ(x,y) = (x+1, y+x mod height)
            next_x = (current[0] + 1) % width
            next_y = (current[1] + current[0]) % height
            current = (next_x, next_y)

        # 构建邻接关系
        next_pos = {}
        prev_pos = {}
        for i in range(grid_area):
            current_pos = cycle[i]
            next_pos[current_pos] = cycle[(i + 1) % grid_area]
            prev_pos[current_pos] = cycle[(i - 1) % grid_area]

        return self.HamiltonianCycle(cycle, pos_to_index, next_pos, prev_pos)

    @staticmethod
    def is_body_continuous_on_cycle(snake: GameController.Snake, h_cycle: HamiltonianCycle) -> bool:
        """检查蛇身体是否在环上形成连续段"""
        grid_area = len(h_cycle.cycle)
        indices = []

        for segment in snake.snake_list:
            if segment in h_cycle.pos_to_index:
                indices.append(h_cycle.pos_to_index[segment])
            else:
                return False

        # 排序索引并检查连续性（考虑环的循环特性）
        sorted_indices = sorted(indices)

        # 检查是否连续
        for i in range(1, len(sorted_indices)):
            if (sorted_indices[i] - sorted_indices[i - 1]) != 1:
                # 检查是否循环连续
                if not (i == len(sorted_indices) - 1 and
                        sorted_indices[0] == 0 and
                        sorted_indices[-1] == grid_area - 1):
                    return False

        return True

    def select_best_cycle_direction(self, head_pos: tuple[int, int], target_idx: int,
                                    snake: GameController.Snake, h_cycle: HamiltonianCycle) -> tuple[int, int] | None:
        """在环上选择最佳移动方向"""
        grid_area = len(h_cycle.cycle)
        head_idx = h_cycle.pos_to_index[head_pos]

        # 计算两个方向的距离
        clockwise_dist = (target_idx - head_idx) % grid_area
        counter_dist = (head_idx - target_idx) % grid_area

        # 选择较短且安全的方向
        if clockwise_dist <= counter_dist:
            next_pos = h_cycle.next_pos[head_pos]
            if self.is_safe_move(next_pos, snake):
                return self.get_direction(head_pos, next_pos)
            else:
                # 尝试另一个方向
                next_pos = h_cycle.prev_pos[head_pos]
                if self.is_safe_move(next_pos, snake):
                    return self.get_direction(head_pos, next_pos)
        else:
            next_pos = h_cycle.prev_pos[head_pos]
            if self.is_safe_move(next_pos, snake):
                return self.get_direction(head_pos, next_pos)
            else:
                next_pos = h_cycle.next_pos[head_pos]
                if self.is_safe_move(next_pos, snake):
                    return self.get_direction(head_pos, next_pos)

        # 两个方向都不安全
        return None

    def optimal_cycle_move(self, snake: GameController.Snake, food: GameController.Food,
                           h_cycle: HamiltonianCycle) -> tuple[int, int]:
        """最优环移动：积极向食物方向移动"""
        head_pos = snake.snake_list[0]
        food_idx = h_cycle.pos_to_index[food.pos]

        # 使用公共函数选择方向
        direction = self.select_best_cycle_direction(head_pos, food_idx, snake, h_cycle)

        if direction is not None:
            return direction
        else:
            # 两个方向都不安全，寻找任何安全方向
            return self.find_safe_direction(snake)

    def move_to_segment(self, snake: GameController.Snake, h_cycle: HamiltonianCycle,
                        target_segment: tuple[int, int]) -> tuple[int, int]:
        """移动到目标段"""
        head_pos = snake.snake_list[0]
        start_idx, end_idx = target_segment

        # 使用公共函数选择方向
        direction = self.select_best_cycle_direction(head_pos, start_idx, snake, h_cycle)

        if direction is not None:
            return direction
        else:
            return self.find_safe_direction(snake)

    @staticmethod
    def find_target_segment(snake: GameController.Snake, h_cycle: HamiltonianCycle) -> tuple[int, int] | None:
        """寻找环上适合的连续空闲段"""
        grid_area = len(h_cycle.cycle)
        snake_length = len(snake.snake_list)

        # 寻找最长的连续空闲段
        best_segment = None
        max_length = 0

        for start_idx in range(grid_area):
            length = 0
            current_idx = start_idx

            while length < grid_area:
                current_pos = h_cycle.cycle[current_idx]
                if current_pos not in snake.snake_list:
                    length += 1
                else:
                    break
                current_idx = (current_idx + 1) % grid_area

            if length >= snake_length and length > max_length:
                max_length = length
                best_segment = (start_idx, (start_idx + length) % grid_area)

        return best_segment

    def find_nearest_cycle_position(self, pos: tuple[int, int], obstacles: list[tuple[int, int]],
                                    h_cycle: HamiltonianCycle) -> tuple[int, int]:
        """找到离给定位置最近的环上顶点"""
        nearest = None
        min_distance = float('inf')

        for cycle_pos in h_cycle.cycle:
            if cycle_pos in obstacles:
                continue

            distance = self.manhattan_distance(pos, cycle_pos)
            if distance < min_distance:
                min_distance = distance
                nearest = cycle_pos

        return nearest

    def move_to_cycle(self, snake: GameController.Snake, h_cycle: HamiltonianCycle) -> tuple[int, int]:
        """将蛇头移动到环上"""
        # 找到最近的环上顶点
        nearest_cycle_pos = self.find_nearest_cycle_position(
            snake.snake_list[0],
            snake.snake_list[:-1],
            h_cycle
        )

        # 使用BFS移动到该位置
        path = self.bfs_find_path(
            snake.snake_list[0],
            nearest_cycle_pos,
            snake.snake_list[:-1]
        )

        if path:
            return self.get_direction(snake.snake_list[0], path[0])
        else:
            return self.find_safe_direction(snake)

    def rearrangement_move(self, snake: GameController.Snake, h_cycle: HamiltonianCycle) -> tuple[int, int]:
        """重新排列算法"""
        snake_head = snake.snake_list[0]

        if snake_head not in h_cycle.pos_to_index:
            # 蛇头不在环上，先移动到环上
            return self.move_to_cycle(snake, h_cycle)

        # 蛇头在环上，但身体不连续
        # 寻找目标连续段
        target_segment = self.find_target_segment(snake, h_cycle)

        if target_segment is None:
            # 没有合适的目标段，使用安全移动
            return self.find_safe_direction(snake)

        # 移动到目标段
        return self.move_to_segment(snake, h_cycle, target_segment)

    def hamiltonian_strategy(self, snake: GameController.Snake, food: GameController.Food) -> tuple[int, int]:
        """哈密顿环策略：积极寻求食物"""
        h_cycle = self.get_hamiltonian_cycle()

        if not self.is_body_continuous_on_cycle(snake, h_cycle):
            # 需要重新排列
            return self.rearrangement_move(snake, h_cycle)

        # 正常哈密顿环移动
        return self.optimal_cycle_move(snake, food, h_cycle)

    def bfs_strategy(self, snake: GameController.Snake, food: GameController.Food) -> tuple[int, int]:
        """BFS策略：积极寻求食物，只在必要时考虑安全"""
        # 首先尝试直接找到到食物的路径
        path = self.bfs_find_path(
            snake.snake_list[0],
            food.pos,
            snake.snake_list[:-1]
        )

        if path:
            # 检查吃食物后是否有足够的空间
            if self.is_eating_safe(snake, food.pos):
                self.consecutive_no_food_moves = 0  # 重置计数器
                return self.get_direction(snake.snake_list[0], path[0])

        # 如果没有直接路径到食物，寻找替代路径
        return self.alternative_food_strategy(snake, food)

    def alternative_food_strategy(self, snake: GameController.Snake, food: GameController.Food) -> tuple[int, int]:
        """替代食物策略：当无法直接到达食物时，寻找其他增长机会"""
        # 增加连续未吃到食物的计数
        self.consecutive_no_food_moves += 1

        # 如果连续多次未吃到食物，尝试更积极的策略
        if self.consecutive_no_food_moves > self.max_consecutive_no_food:
            return self.aggressive_food_strategy(snake, food)

        # 寻找最安全的移动方向，同时尽量靠近食物
        return self.safe_toward_food_strategy(snake, food)

    def aggressive_food_strategy(self, snake: GameController.Snake, food: GameController.Food) -> tuple[int, int]:
        """积极食物策略：在多次未吃到食物后，采取更积极的策略"""
        head = snake.snake_list[0]

        # 计算到食物的方向
        food_direction = self.get_direction_toward_food(head, food.pos)

        # 检查这个方向是否相对安全
        next_pos = (
            (head[0] + food_direction[0]) % self.map_size[0],
            (head[1] + food_direction[1]) % self.map_size[1]
        )

        # 如果这个方向相对安全（不直接撞到身体），就尝试
        if self.is_relatively_safe_move(next_pos, snake):
            self.consecutive_no_food_moves = 0  # 重置计数器
            return food_direction

        # 如果积极策略不安全，回退到安全策略
        return self.find_safe_direction(snake)

    def safe_toward_food_strategy(self, snake: GameController.Snake, food: GameController.Food) -> tuple[int, int]:
        """安全靠近食物策略：在安全的前提下尽量靠近食物"""
        head = snake.snake_list[0]
        best_direction = None
        min_food_distance = float('inf')

        # 评估所有安全方向，选择最接近食物的方向
        for neighbor in self.get_neighbors(head):
            if self.is_safe_move(neighbor, snake):
                distance = self.manhattan_distance(neighbor, food.pos)
                if distance < min_food_distance:
                    min_food_distance = distance
                    best_direction = self.get_direction(head, neighbor)

        if best_direction is not None:
            return best_direction

        # 如果没有安全方向，寻找相对安全的方向
        return self.find_relatively_safe_direction(snake, food)

    def is_eating_safe(self, snake: GameController.Snake, food_pos: tuple[int, int]) -> bool:
        """检查吃食物后是否安全"""
        # 模拟吃食物后的状态
        new_snake_list = [food_pos] + snake.snake_list  # 头部移动到食物位置，身体增长

        # 检查新头部是否与身体其他部分碰撞
        if food_pos in snake.snake_list:
            return False

        # 检查吃食物后是否有足够的空间移动
        reachable_space = self.calculate_reachable_space(food_pos, new_snake_list)

        # 如果可达空间大于蛇身长度的1/3，认为是安全的
        # 这个阈值比之前更宽松，允许更积极的吃食物策略
        return reachable_space >= len(new_snake_list) // 3

    def calculate_reachable_space(self, start_pos: tuple[int, int], snake_list: list[tuple[int, int]]) -> int:
        """计算从起始位置可达的空间大小"""
        visited = set()
        queue = Queue()

        queue.put(start_pos)
        visited.add(start_pos)

        while not queue.empty():
            current_pos = queue.get()

            for neighbor in self.get_neighbors(current_pos):
                if neighbor not in snake_list and neighbor not in visited:
                    visited.add(neighbor)
                    queue.put(neighbor)

        return len(visited)

    def control(self, snake: GameController.Snake, food: GameController.Food) -> tuple[int, int]:
        """主控制算法：积极寻求增长，同时保持安全"""
        snake_length = len(snake.snake_list)

        # 根据蛇身长度选择策略
        if snake_length < self.L0:
            # BFS策略模式：积极寻求食物
            return self.bfs_strategy(snake, food)
        else:
            # 哈密顿环策略模式：在环上积极寻求食物
            return self.hamiltonian_strategy(snake, food)

    # 新增工具函数
    def get_direction_toward_food(self, head_pos: tuple[int, int], food_pos: tuple[int, int]) -> tuple[int, int]:
        """获取朝向食物的方向"""
        # 计算最短路径方向（考虑边界穿越）
        dx = food_pos[0] - head_pos[0]
        dy = food_pos[1] - head_pos[1]

        # 考虑边界穿越的最短路径
        if abs(dx) > self.map_size[0] / 2:
            dx = -dx / abs(dx) * (self.map_size[0] - abs(dx)) if dx != 0 else 0

        if abs(dy) > self.map_size[1] / 2:
            dy = -dy / abs(dy) * (self.map_size[1] - abs(dy)) if dy != 0 else 0

        # 选择主要方向
        if abs(dx) > abs(dy):
            return 1 if dx > 0 else -1, 0
        else:
            return 0, 1 if dy > 0 else -1

    @staticmethod
    def is_relatively_safe_move(new_head: tuple[int, int], snake: GameController.Snake) -> bool:
        """检查移动是否相对安全（允许尾部碰撞）"""
        # 允许移动到尾部位置（因为尾部会移动）
        return new_head not in snake.snake_list[:-1]

    def find_relatively_safe_direction(self, snake: GameController.Snake, food: GameController.Food) -> tuple[int, int]:
        """寻找相对安全的移动方向（允许尾部碰撞）"""
        head = snake.snake_list[0]

        # 优先选择朝向食物的方向
        food_direction = self.get_direction_toward_food(head, food.pos)
        next_pos = (
            (head[0] + food_direction[0]) % self.map_size[0],
            (head[1] + food_direction[1]) % self.map_size[1]
        )

        if self.is_relatively_safe_move(next_pos, snake):
            return food_direction

        # 如果没有朝向食物的安全方向，寻找任何相对安全的方向
        for neighbor in self.get_neighbors(head):
            if self.is_relatively_safe_move(neighbor, snake):
                return self.get_direction(head, neighbor)

        # 如果没有相对安全的方向，回退到绝对安全的方向
        return self.find_safe_direction(snake)

    # 原有工具函数
    def get_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """获取邻居位置"""
        neighbors = []
        for dx, dy in constants.DIRECTIONS:
            new_x = (pos[0] + dx + self.map_size[0]) % self.map_size[0]
            new_y = (pos[1] + dy + self.map_size[1]) % self.map_size[1]
            neighbors.append((new_x, new_y))
        return neighbors

    @staticmethod
    def is_safe_move_simulation(new_head: tuple[int, int], obstacles: list[tuple[int, int]]) -> bool:
        """模拟移动后的安全性验证"""
        new_obstacles = obstacles.copy()
        if len(new_obstacles) > 0:
            new_obstacles.pop()  # 尾部移动

        return new_head not in new_obstacles

    @staticmethod
    def reconstruct_path(parent: dict[tuple[int, int], tuple[int, int]],
                         start: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
        """重构路径"""
        path = []
        current = target

        while current != start:
            path.append(current)
            if current not in parent:
                return []
            current = parent[current]

        path.reverse()
        return path

    def bfs_find_path(self, start: tuple[int, int], target: tuple[int, int],
                      obstacles: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """BFS寻路"""
        queue = Queue()
        visited = set()
        parent = dict()

        queue.put((start, 0))
        visited.add(start)
        parent[start] = None

        while not queue.empty():
            current_pos, steps = queue.get()

            if current_pos == target:
                return self.reconstruct_path(parent, start, target)

            if steps >= self.grid_area - len(obstacles):
                continue

            for neighbor in self.get_neighbors(current_pos):
                if neighbor not in obstacles and neighbor not in visited:
                    if self.is_safe_move_simulation(neighbor, obstacles):
                        visited.add(neighbor)
                        parent[neighbor] = current_pos
                        queue.put((neighbor, steps + 1))

        return []

    @staticmethod
    def is_safe_move(new_head: tuple[int, int], snake: GameController.Snake) -> bool:
        """检查移动是否安全"""
        return new_head not in snake.snake_list[:-1]

    def get_direction(self, from_pos: tuple[int, int], to_pos: tuple[int, int]) -> tuple[int, int]:
        """获取方向向量"""
        dx = (to_pos[0] - from_pos[0]) % self.map_size[0]
        dy = (to_pos[1] - from_pos[1]) % self.map_size[1]

        # 处理边界穿越
        if dx == 1 or dx == -(self.map_size[0] - 1):
            return constants.DIRECTIONS[1]  # RIGHT
        if dx == -1 or dx == self.map_size[0] - 1:
            return constants.DIRECTIONS[3]  # LEFT
        if dy == 1 or dy == -(self.map_size[1] - 1):
            return constants.DIRECTIONS[0]  # DOWN
        if dy == -1 or dy == self.map_size[1] - 1:
            return constants.DIRECTIONS[2]  # UP

        return 0, 0

    def find_safe_direction(self, snake: GameController.Snake) -> tuple[int, int]:
        """寻找任何安全的移动方向"""
        head = snake.snake_list[0]
        for neighbor in self.get_neighbors(head):
            if self.is_safe_move(neighbor, snake):
                return self.get_direction(head, neighbor)

        # 没有安全方向，随机选择
        return constants.DIRECTIONS[randint(0, 3)]

    def manhattan_distance(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
        """计算曼哈顿距离（考虑边界穿越）"""
        dx = min(abs(pos1[0] - pos2[0]), self.map_size[0] - abs(pos1[0] - pos2[0]))
        dy = min(abs(pos1[1] - pos2[1]), self.map_size[1] - abs(pos1[1] - pos2[1]))
        return dx + dy


game_controller = GameController()

if __name__ == '__main__':
    test_gui = GUI()
    test_gui.run()
