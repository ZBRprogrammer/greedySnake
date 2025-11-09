import tkinter as tk
from tkinter import *
from tkinter import messagebox
import constants


def on_entry_click(event, entry, default_text):
    if entry.get() == default_text:
        entry.configure(fg='black')
        entry.delete(0, tk.END)
        entry.insert(0, '')


def on_entry_unfocus(event, entry, default_text):
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
    entry.bind('<FocusIn>', lambda event: on_entry_click(event, entry, default_text))
    entry.bind('<FocusOut>', lambda event: on_entry_unfocus(event, entry, default_text))

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


class Snake:
    class Node:
        def __init__(self,front=None, rear=None):
            self.front = front
            self.rear = rear

    def __init__(self):
        pass


class Food:
    def __init__(self):
        pass


class GameController:
    def __init__(self):
        pass


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
            constants.map_width, constants.map_height = constants.WIDTH_HEIGHT_LIST[self.size_var.get()]
        elif self.size_var.get() == 3 and self.width_entry.get().isdigit() and self.height_entry.get().isdigit() and int(
                self.width_entry.get()) > 0 and int(self.height_entry.get()) > 0:
            constants.map_width, constants.map_height = self.width_entry.get(), self.height_entry.get()
        else:
            messagebox.showerror(title='Error', message='Size input is invalid')
            return
        if self.difficulty_var.get() <= 2:
            constants.fps = constants.SPEED_LIST[self.difficulty_var.get()]
        elif self.difficulty_var.get() == 3 and self.speed_entry.get().isdigit() and int(self.speed_entry.get()) > 0:
            constants.fps = self.speed_entry.get()
        else:
            messagebox.showerror(title='Error', message='Speed input is invalid')
            return
        if self.head_color_var.get() != self.body_color_var.get():
            constants.head_color = self.head_color_var.get()
            constants.body_color = self.body_color_var.get()
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


if __name__ == '__main__':
    test_gui = GUI()
    test_gui.run()
