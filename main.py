from classes import *
import constants
import pygame
from pygame.locals import *


def window_setup():
    pygame.init()
    game_controller.width, game_controller.height = game_controller.map_width * constants.BLOCK_SIZE, game_controller.map_height * constants.BLOCK_SIZE
    game_controller.screen = pygame.display.set_mode((game_controller.width, game_controller.height))
    game_controller.clock = pygame.time.Clock()
    game_controller.running = True


def main():
    window_setup()
    game_controller.initialize()
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

    pygame.quit()


if __name__ == '__main__':
    input_gui = GUI()
    input_gui.run()
    main()
