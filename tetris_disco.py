import pygame as pg
import random
import math
import time
import sys
from pygame.locals import *
from settings import *
import pathlib


def pauseScreen():
    global start
    start.play()
    pause = pg.Surface((600, 500), pg.SRCALPHA)
    pause.fill((0, 0, 0, 200))
    sc.blit(pause, (0, 0))


def main():
    global clock, sc, basic_font, big_font, pointsfont, bonus, start, game_over, images, points
    pg.init()
    pg.mixer.music.load("sounds/tetris_theme.mp3")
    pg.mixer.music.play(-1)
    start = pg.mixer.Sound("sounds/start.wav")
    bonus = pg.mixer.Sound("sounds/bonus.wav")
    game_over = pg.mixer.Sound("sounds/game_over.wav")
    clock = pg.time.Clock()
    sc = pg.display.set_mode((window_w, window_h))
    basic_font = pg.font.SysFont('arial', 20)
    points_font = pg.font.SysFont('arial', 30)
    big_font = pg.font.SysFont('verdana', 40)
    pg.display.set_caption('Тетрис')
    showText('Тетрис')
    files = [item for item in pathlib.Path("sprites/").rglob('*.png') if item.is_file()]
    images = [pg.image.load(file).convert_alpha() for file in files]
    images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in images]

    while True:
        tetris()
        pauseScreen()
        game_over.play()
        f = open("record.txt", "r")
        record = int(f.readlines()[0])
        f.close()
        if points > record:
            f = open("record.txt", "w")
            f.write(str(points))
            f.close()
        showText(f'Проигрыш. Счёт: {points}')


def tetris():
    global start, game_over, points
    start.play()
    zone = empty_zone()
    last_move_down = time.time()
    last_side_move = time.time()
    last_fall = time.time()
    down = False
    right = False
    left = False

    points = 0
    level, fall_speed = speed(points)

    fallf = getNewFig()
    nextf = getNewFig()

    while True:

        if fallf == None:
            fallf = nextf
            nextf = getNewFig()
            last_fall = time.time()
            

            if not checkPos(zone, fallf):
                return
        quitGame()
        for event in pg.event.get(): 
            if event.type == KEYUP:
                if event.key == K_SPACE:
                    pauseScreen()
                    showText('Пауза')
                    last_fall = time.time()
                    last_move_down = time.time()
                    last_side_move = time.time()
                elif event.key == K_LEFT:
                    left = False
                elif event.key == K_RIGHT:
                    right = False
                elif event.key == K_DOWN:
                    down = False

            elif event.type == KEYDOWN:
                if event.key == K_LEFT and checkPos(zone, fallf, X=-1):
                    fallf['x'] -= 1
                    left = True
                    right = False
                    last_side_move = time.time()

                elif event.key == K_RIGHT and checkPos(zone, fallf, X=1):
                    fallf['x'] += 1
                    right = True
                    left = False
                    last_side_move = time.time()

                elif event.key == K_UP:
                    fallf['rotation'] = (fallf['rotation'] + 1) % len(figures[fallf['shape']])
                    if not checkPos(zone, fallf):
                        fallf['rotation'] = (fallf['rotation'] - 1) % len(figures[fallf['shape']])

                elif event.key == K_DOWN:
                    down = True
                    if checkPos(zone, fallf, Y=1):
                        fallf['y'] += 1
                    last_move_down = time.time()

                elif event.key == K_RETURN:
                    down = False
                    left = False
                    right = False
                    for i in range(1, zone_h):
                        if not checkPos(zone, fallf, Y=i):
                            break
                    fallf['y'] += i - 1

        if (left or right) and time.time() - last_side_move > side_freq:
            if left and checkPos(zone, fallf, X=-1):
                fallf['x'] -= 1
            elif right and checkPos(zone, fallf, X=1):
                fallf['x'] += 1
            last_side_move = time.time()

        if down and time.time() - last_move_down > down_freq and checkPos(zone, fallf, Y=1):
            fallf['y'] += 1
            last_move_down = time.time()

        if time.time() - last_fall > fall_speed:
            if not checkPos(zone, fallf, Y=1):
                add_to_zone(zone, fallf)
                points += clear_row(zone) * 100
                level, fall_speed = speed(points)
                fallf = None
            else:
                fallf['y'] += 1
                last_fall = time.time()

        sc.fill(bg_color)
        title()
        gZone(zone)
        info(points)
        img_nextFig(nextf)
        if fallf != None:
            show_figure(fallf)
        pg.display.update()
        clock.tick(FPS)


def txtObjects(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()


def check():
    quitGame()

    for event in pg.event.get([KEYDOWN, KEYUP]):
        if event.type == KEYUP:
            return event.key
    return None


def showText(text):
    titleSurf, titleRect = txtObjects(text, big_font, title_color)
    titleRect.center = (int(window_w / 2) - 3, int(window_h / 2) - 3)
    sc.blit(titleSurf, titleRect)
   
    pressKeySurf, pressKeyRect = txtObjects('Нажмите любую клавишу для продолжения', basic_font, title_color)
    pressKeyRect.center = (int(window_w / 2), int(window_h / 2) + 100)
    sc.blit(pressKeySurf, pressKeyRect)

    while check() == None:
        pg.display.update()
        clock.tick()


def quitGame():
    for event in pg.event.get(QUIT):
        pg.quit()
        sys.exit()
    for event in pg.event.get(KEYUP): 
        if event.key == K_ESCAPE:
            pg.quit()
            sys.exit()
        pg.event.post(event) 


def speed(points):
    level = points // 300 + 1
    fall_speed = 0.27 - (level * 0.01)
    return level, fall_speed

def getNewFig():
    shape = random.choice(list(figures.keys()))
    newFigure = {'shape': shape,
                'rotation': random.randint(0, len(figures[shape]) - 1),
                'x': zone_w // 2 - fig_w // 2,
                'y': -2, 
                'color': random.randint(0, len(colors)-1)}
    return newFigure


def add_to_zone(zone, fig):
    for x in range(fig_w):
        for y in range(fig_h):
            if figures[fig['shape']][fig['rotation']][y][x] != empty:
                zone[x + fig['x']][y + fig['y']] = fig['color']


def empty_zone():
    lst = []
    for i in range(zone_w):
        lst.append([empty] * zone_h)
    return lst


def inzone(x, y):
    f = x >= 0 and x < zone_w and y < zone_h
    return f


def checkPos(zone, fig, X=0, Y=0):
    # проверяет, находится ли фигура в границах стакана, не сталкиваясь с другими фигурами
    for x in range(fig_w):
        for y in range(fig_h):
            above = y + fig['y'] + Y < 0
            if above or figures[fig['shape']][fig['rotation']][y][x] == empty:
                continue
            if not inzone(x + fig['x'] + X, y + fig['y'] + Y):
                return False
            if zone[x + fig['x'] + X][y + fig['y'] + Y] != empty:
                return False
    return True

def is_full(zone, y):
    global bonus
    for x in range(zone_w):
        if zone[x][y] == empty:
            return False
    bonus.play()
    return True


def clear_row(zone):
    kill_lines = 0
    y = zone_h - 1
    while y >= 0:
        if is_full(zone, y):
           for pushDownY in range(y, 0, -1):
                for x in range(zone_w):
                    zone[x][pushDownY] = zone[x][pushDownY-1]
           for x in range(zone_w):
                zone[x][0] = empty
           kill_lines += 1
        else:
            y -= 1 
    return kill_lines


def getCoords(block_x, block_y):
    return (side_marg + (block_x * block)), (top_marg + (block_y * block))


def img_block(bl_x, bl_y, color, px=None, py=None):
    global image
    if color == empty:
        return
    if px == None and py == None:
        px, py = getCoords(bl_x, bl_y)

    image = random.choice(images)
    sc.blit(image, (px + 1, py + 1, block - 1, block - 1))


def gZone(zone):
    for x in range(W):
        for y in range(H):
            pg.draw.rect(sc, (185, 185, 185),
                         (x * TILE_SIZE + side_marg, y * TILE_SIZE + top_marg, TILE_SIZE, TILE_SIZE), 1)
    pg.draw.rect(sc, get_color(), (side_marg - 4, top_marg - 4, (zone_w * block) + 8, (zone_h * block) + 8), 5)

    for x in range(zone_w):
        for y in range(zone_h):
            img_block(x, y, zone[x][y])


def get_color():
    time = pg.time.get_ticks() * 0.002
    n_sin = lambda t: (math.sin(t) * 0.5 + 0.5) * 255
    return n_sin(time * 0.5), n_sin(time * 0.7), n_sin(time * 0.9)


def title():
    titleSurf = big_font.render('ДИСКО Тетрис', True, get_color())
    titleRect = titleSurf.get_rect()
    titleRect.topleft = (window_w - 375, 30)
    sc.blit(titleSurf, titleRect)
    

def info(points):
    pointsSurf = basic_font.render(f'Очки: {points}', True, get_color())
    pointsRect = pointsSurf.get_rect()
    pointsRect.topleft = (window_w - 250, 130)
    sc.blit(pointsSurf, pointsRect)

    f = open("record.txt", "r")
    recordlSurf = basic_font.render(f'Рекорд: {int(list(f.readlines())[0])}', True, get_color())
    f.close()
    recordRect = recordlSurf.get_rect()
    recordRect.topleft = (window_w - 270, 450)
    sc.blit(recordlSurf, recordRect)

    pausebSurf = basic_font.render('Space - пауза', True, get_color())
    pausebRect = pausebSurf.get_rect()
    pausebRect.topleft = (window_w - 270, 420)
    sc.blit(pausebSurf, pausebRect)


def show_figure(fig, px=None, py=None):
    figToDraw = figures[fig['shape']][fig['rotation']]
    if px == None and py == None:
        px, py = getCoords(fig['x'], fig['y'])

    for x in range(fig_w):
        for y in range(fig_h):
            if figToDraw[y][x] != empty:
                img_block(None, None, fig['color'], px + (x * block), py + (y * block))


def img_nextFig(fig):

    nextSurf = basic_font.render('Следующая фигура:', True, get_color())
    nextRect = nextSurf.get_rect()
    nextRect.topleft = (window_w - 300, 230)
    sc.blit(nextSurf, nextRect)
    show_figure(fig, px=window_w-270, py=250)


if __name__ == '__main__':
    main()
