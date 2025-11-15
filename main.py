import pygame
from pygame.locals import *

<<<<<<< HEAD
=======
import constants
>>>>>>> e86ca2a1b396c96e6e4b2af92c120477b237efc8
from classes import *


def window_setup():
    pygame.init()
    game_controller.width, game_controller.height = game_controller.map_width * constants.BLOCK_SIZE, game_controller.map_height * constants.BLOCK_SIZE
    game_controller.screen = pygame.display.set_mode((game_controller.width, game_controller.height))
    game_controller.clock = pygame.time.Clock()
    game_controller.running = True


def auto_play():
    auto_play_instance = AutoPlay((game_controller.map_width, game_controller.map_height))
    while game_controller.running:
        game_controller.tick()
        game_controller.change_direction(auto_play_instance.control(game_controller.snake, game_controller.food))
        game_controller.screen.fill('black')
        if game_controller.snake_moving:
            game_controller.snake_move()
            game_controller.tick_food_value()
        game_controller.draw()
        pygame.display.update()
        game_controller.clock.tick(constants.FPS)


def manual_play():
    while game_controller.running:
        for event in pygame.event.get():
            if event.type == QUIT:
                game_controller.running = False
                break
            if event.type == KEYDOWN:
                game_controller.is_key_down = True
            if event.type == KEYUP:
                game_controller.is_key_down = False
        game_controller.tick()
        game_controller.get_key_respond(pygame.key.get_pressed())
        game_controller.screen.fill('black')
        if game_controller.snake_moving:
            game_controller.snake_move()
            game_controller.tick_food_value()
        game_controller.draw()
        pygame.display.update()
        game_controller.clock.tick(constants.FPS)


def main():
    window_setup()
    game_controller.initialize()
    if game_controller.automated:
        auto_play()
    else:
        manual_play()
    pygame.quit()


if __name__ == '__main__':
    input_gui = GUI()
    input_gui.run()
    main()
