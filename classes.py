import tkinter as tk
from tkinter import *
from tkinter import messagebox

from random import randint

import pygame.key
from pygame import draw
from pygame import Surface
from pygame import Rect
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


def frame_template(parent, text, button_amount, *args) -> tuple[Frame, IntVar]:
    # create frame
    frame = Frame(parent)
    # set text
    Label(frame, text=text).pack(side="left")
    # add buttons
    var = IntVar()
    var.set(button_amount)
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

        def get_color(self):
            self.color = constants.FOOD_COLOR_LIST[(self.value-constants.FOOD_VALUE_MIN) // ((
                        constants.FOOD_VALUE_MAX - constants.FOOD_VALUE_MIN // len(constants.FOOD_COLOR_LIST) - 1))]

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

    def __init__(self, score: int, screen: Surface | None, screen_size: tuple[int, int],
                 map_size: tuple[int, int], run_interval: int, running: bool, snake_moving: bool, clock: Clock | None,
                 snake_head_color: str, snake_body_color: str):
        self.score = score
        self.ticks = 0
        self.screen = screen
        self.width, self.height = screen_size
        self.map_width, self.map_height = map_size
        self.run_interval = run_interval
        self.running = running
        self.snake_moving = snake_moving
        self.clock = clock
        self.snake = self.Snake((randint(0, self.map_width), randint(0, self.map_height)), [], snake_head_color,
                                snake_body_color)
        self.food = self.Food((0, 0), 0, False)
        self.is_key_down = False
        self.recorded_key_state = self.is_key_down
        self.recorded_key_pressed = None
        self.tmp_direction = (0,0)
        self.running_tick = 0

    def tick(self):
        self.ticks += 1
        self.ticks %= constants.FPS
        if self.ticks % self.run_interval == 0:
            self.running_tick+=1


    def initialize(self):
        self.snake.snake_list = [(randint(0, self.map_width), randint(0, self.map_height))]
        self.snake.velocity = self.tmp_direction = constants.DIRECTIONS[randint(0, 3)]
        self.snake_moving = True
        self.summon_new_food()

    def snake_move(self):
        if self.ticks%self.run_interval != 0:
            return
        self.snake.velocity = self.tmp_direction
        self.snake.move()
        for i in self.snake.snake_list[1:]:
            if i == self.snake.snake_list[0]:
                self.snake_moving = False
        if self.snake.snake_list[0] != self.food.pos:
            self.snake.pop()
        else:
            self.score += self.food.value
            self.summon_new_food()

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
        self.food.value = randint(constants.FOOD_VALUE_MIN, constants.FOOD_VALUE_MAX)  # value
        self.food.is_bonus = ((self.score+1) / constants.FOOD_BONUS_INTERVAL).is_integer() ^ self.food.is_bonus  # is bonus
        self.food.get_color()
        # print(f"DEBUG: is_bonus: {self.food.is_bonus}")

    def tick_food_value(self):
        if not self.food.is_bonus:
            return
        if self.running_tick % constants.FOOD_BONUS_DECLINE_INTERVAL == 0:
            self.food.value_decline()
            if self.food.value < constants.FOOD_DISAPPEAR_THRESHOLD:
                self.summon_new_food()

    def get_key_respond(self, key_pressed:pygame.key.ScancodeWrapper):
        # check if key_pressed changed
        if self.recorded_key_state != self.is_key_down:
            if self.is_key_down: # record key_pressed
                self.recorded_key_pressed = key_pressed
            if self.recorded_key_state: # wait for key_up
                for key, value in constants.KEY_DIRECTION_MAPPING.items():
                    if self.recorded_key_pressed[key] and tuple(map(sum,zip(self.snake.velocity,constants.DIRECTIONS[value]))) != (0,0):
                        # tuple(map(sum,zip(self.snake.velocity,constants.DIRECTIONS[value]))) != (0,0) -> check if directions are opposing
                        self.tmp_direction = constants.DIRECTIONS[value] # record input direction
                        break
            self.recorded_key_state = self.is_key_down # change state

    def draw(self):
        for i in range(self.map_width):
            for j in range(self.map_height):
                draw.rect(self.screen,constants.BACKGROUND_COLOR,get_rect((i,j)))
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
        draw.rect(self.screen,self.food.color,get_rect(self.food.pos))


class GUI:
    def __init__(self):
        self.tk = Tk()
        self.size_var = IntVar()
        self.difficulty_var = IntVar()
        self.head_color_var = StringVar()
        self.body_color_var = StringVar()
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
        if self.size_var.get() <= 2:
            game_controller.map_width, game_controller.map_height = constants.WIDTH_HEIGHT_LIST[self.size_var.get()]
        elif self.size_var.get() == 3 and self.width_entry.get().isdigit() and self.height_entry.get().isdigit() and int(
                self.width_entry.get()) > 0 and int(self.height_entry.get()) > 0:
            game_controller.map_width, game_controller.map_height = int(self.width_entry.get()), int(self.height_entry.get())
        else:
            messagebox.showerror(title='Error', message='Size input is invalid')
            return
        if self.difficulty_var.get() <= 2:
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

    def construct_size_layout(self, parent) -> Frame:
        # size frame
        size_frame, self.size_var = frame_template(parent, constants.INPUT_SIZE_CONFIG, 4, constants.INPUT_SIZE_SMALL,
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
        difficulty_frame, self.difficulty_var = frame_template(parent, constants.INPUT_DIFFICULTY_CONFIG, 4,
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


game_controller = GameController(0, None, (0, 0), (0, 0), 0, False, False, None, '', '')

if __name__ == '__main__':
    test_gui = GUI()
    test_gui.run()
