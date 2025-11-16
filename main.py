import pygame
from pygame.locals import *
from encrypt import *
from classes import *


def window_setup():
    pygame.init()
    game_controller.width, game_controller.height = game_controller.map_width * constants.BLOCK_SIZE, game_controller.map_height * constants.BLOCK_SIZE
    game_controller.screen = pygame.display.set_mode((game_controller.width, game_controller.height))
    game_controller.clock = pygame.time.Clock()
    game_controller.running = True


def play_game(is_auto=False):
    """
    通用的游戏主循环

    Args:
        is_auto: 是否为自动模式
    """
    auto_play_instance = AutoPlay((game_controller.map_width, game_controller.map_height)) if is_auto else None

    while game_controller.running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == QUIT:
                game_controller.running = False
                break
            if event.type == KEYDOWN:
                game_controller.is_key_down = True
            if event.type == KEYUP:
                game_controller.is_key_down = False

        # 游戏逻辑更新
        game_controller.tick()
        game_controller.get_key_respond(pygame.key.get_pressed())

        # 自动模式下的方向控制
        if is_auto and auto_play_instance:
            game_controller.change_direction(auto_play_instance.control(game_controller.snake, game_controller.food))

        # 渲染
        game_controller.screen.fill('black')

        # 游戏状态处理
        if not game_controller.pausing:
            if game_controller.snake_moving:
                # 更新标题显示分数
                title = constants.AUTO_PLAY_TITLE if is_auto else constants.MANUAL_PLAY_TITLE
                pygame.display.set_caption(title.format(score = game_controller.score, high_score = game_controller.high_score))

                # 游戏进行中的逻辑
                game_controller.snake_move()
                game_controller.tick_food_value()
            elif not game_controller.snake_moving and game_controller.about_to_respawn:
                # 重新初始化游戏
                game_controller.initialize()
            else:
                # 游戏结束状态
                pygame.display.set_caption(constants.DEAD_TITLE.format(score = game_controller.score, high_score = game_controller.high_score))
                game_over(game_controller.score)
        else:
            # 暂停状态
            pygame.display.set_caption(constants.PAUSED_TITLE)

        # 绘制和更新
        game_controller.draw()
        pygame.display.update()
        game_controller.clock.tick(constants.FPS)



# 在游戏结束时调用
def game_over(score):
    # 根据游戏模式决定是否记入最高分
    is_auto = game_controller.automated  # 假设这是判断是否为自动模式的标志
    handle_game_over(score, is_auto)



def main():
    window_setup()
    game_controller.initialize()
    play_game(is_auto=game_controller.automated)
    pygame.quit()
    exit(0)


if __name__ == '__main__':
    input_gui = GUI()
    input_gui.run()
    main()
