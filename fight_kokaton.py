import math
import random
import sys
import time

import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ

NUM_OF_BOMS = 5  # 爆弾の数

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し,真理値タプルを返す関数
    引数:こうかとん,または,爆弾SurfaceのRect
    戻り値:横方向,縦方向のはみ出し判定結果（画面内:True/画面外:False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num:こうかとん画像ファイル名の番号
        引数2 xy:こうかとん画像の位置座標タプル
        """
        self.img = pg.transform.flip(  # 左右反転
            pg.transform.rotozoom(  # 2倍に拡大
                pg.image.load(f"ex03/fig/{num}.png"), 
                0, 
                2.0), 
            True, 
            False
        )
        self.rct = self.img.get_rect()
        self.rct.center = xy
        self.dire = (5, 0)

        img_flip = pg.transform.flip(self.img, True, False)
        self.imgs: dict = {
            (0, 0): self.img,
            (-5, 0): img_flip,
            (-5, -5): pg.transform.rotozoom(img_flip, -45,1),
            (0, -5): pg.transform.rotozoom(self.img, 90, 1),
            (-5, 5): pg.transform.rotozoom(img_flip, 45, 1),
            (5, 0): self.img,
            (5, -5): pg.transform.rotozoom(self.img, 45, 1),
            (0, 5): pg.transform.rotozoom(self.img, -90, 1),
            (5, 5): pg.transform.rotozoom(self.img, -45, 1),
        }

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num:こうかとん画像ファイル名の番号
        引数2 screen:画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"ex03/fig/{num}.png"), 0, 2.0)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst:押下キーの真理値リスト
        引数2 screen:画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        screen.blit(self.imgs[tuple(sum_mv)], self.rct)
        if sum_mv == [0, 0]: sum_mv = [5, 0]
        self.dire = tuple(sum_mv)


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self):
        """
        爆弾円Surfaceを生成する
        """
        color_list = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        color = random.choice(color_list)
        rad_list = [10, 20, 30, 40, 50]
        rad = random.choice(rad_list)
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        mv_list = [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]
        self.vx, self.vy = random.choice(mv_list), random.choice(mv_list)

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen:画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird:ビームを放つこうかとん
        """
        self.img = pg.transform.rotozoom(pg.image.load("ex03/fig/beam.png"), 0, 2.0)
        self.rct = self.img.get_rect()
        self.vx, self.vy = bird.dire[0], bird.dire[1]
        self.rct.centerx = bird.rct.centerx + (bird.rct.width * self.vx/5 )
        self.rct.centery = bird.rct.centery + (bird.rct.height * self.vy/5 )

        self.img = pg.transform.rotozoom(self.img, math.degrees(math.atan2(-self.vy, self.vx)), 1.0)

    def update(self, screen: pg.Surface):
        """
        ビームを右方向に移動させる
        引数 screen:画面Surface
        """
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, bomb: Bomb):
        """
        爆発エフェクトSurfaceを生成する
        引数 bomb:爆発した爆弾
        """
        self.img = pg.transform.rotozoom(pg.image.load("ex03/fig/explosion.gif"), 0, 2.0)
        self.img_list = [
            self.img,
            pg.transform.flip(self.img, True, False),
            pg.transform.flip(self.img, False, True),
            pg.transform.flip(self.img, True, True),
        ]
        self.rct = self.img.get_rect()
        self.rct.center = bomb.rct.center
        self.life = 100

    def update(self, screen: pg.Surface):
        """
        爆発経過時間を１減算
        lifeの値に応じて画像リストを切り替えて爆発を演出
        引数 screen:画面Surface
        """
        screen.blit(self.img_list[self.life % len(self.img_list)], self.rct)
        self.life -= 1


class Score:
    """
    スコアに関するクラス
    """
    def __init__(self):
        """
        フォント、文字色、初期値の設定
        文字列Surfaceを生成
        """
        self.font = pg.font.SysFont("hg創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.font.render(f"スコア:{self.score}", 0, self.color)
        self.rct = 100, HEIGHT - 50

    def update(self, screen: pg.Surface):
        """
        現在のスコアを表示する
        引数 screen:画面Surface
        """
        self.img = self.font.render(f"スコア:{self.score}", 0, self.color)
        screen.blit(self.img, self.rct)        


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("ex03/fig/pg_bg.jpg")
    bird = Bird(3, (900, 400))
    bombs = [Bomb() for _ in range(NUM_OF_BOMS)]
    explosions = []
    beams = []
    score = Score()

    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # ビームクラスのインスタンスを生成する
                beams.append(Beam(bird))
        
        screen.blit(bg_img, [0, 0])
        
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return
        
        for i,bomb in enumerate(bombs):
            for j,beam in enumerate(beams):
                if bomb.rct.colliderect(beam.rct):
                    # 爆弾とビームの衝突判定
                    bombs[i] = None
                    beams[j] = None
                    beams = [beam for beam in beams if beam is not None]
                    explosions.append(Explosion(bomb))
                    score.score += 1
                    pg.display.update()
        
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        bombs = [bomb for bomb in bombs if bomb is not None]
        explosions = [explosion for explosion in explosions if explosion.life > 0]
        for bomb in bombs:
            bomb.update(screen)
        for explosion in explosions:
            explosion.update(screen)
        for beam in beams:
            if beam.rct.left > WIDTH or beam.rct.right < 0 or beam.rct.top > HEIGHT or beam.rct.bottom < 0:
                beams.remove(beam)    
            beam.update(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
