from classes import *
import constants
import pygame
from pygame.locals import *


def window_setup():
    pygame.init()
    constants.width, constants.height = constants.map_width * constants.BLOCK_SIZE, constants.map_height * constants.BLOCK_SIZE
    constants.screen = pygame.display.set_mode((constants.width, constants.height))
    constants.Clock = pygame.time.Clock()
    constants.running = True


def main():
    window_setup()
    while constants.running:
        for event in pygame.event.get():
            if event.type == QUIT:
                constants.running = False
                break

        constants.screen.fill('black')

        pygame.display.update()
        constants.Clock.tick(constants.fps)


if __name__ == '__main__':
    input_gui = GUI()
    input_gui.run()
    main()
