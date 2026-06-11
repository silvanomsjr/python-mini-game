"""
=============================================================================
SPACE INVADERS - Mini Game 2D em Python/Pygame
=============================================================================
Conceitos de Computação Gráfica que aparecem por aqui:
  - Transformações geométricas (rotação e translação) via matrizes manuais
  - Animação com loop principal (game loop)
  - Rasterização de primitivas geométricas (polígonos, círculos, linhas)
  - Detecção de colisão implementada manualmente (AABB e circular)
=============================================================================
"""

import pygame
import math
import random
import sys

# CONSTANTES GLOBAIS
LARGURA = 800
ALTURA = 600
FPS = 60

# Paleta de cores
PRETO      = (0, 0, 0)
BRANCO     = (255, 255, 255)
VERDE      = (0, 255, 100)
CIANO      = (0, 220, 255)
VERMELHO   = (255, 60, 60)
AMARELO    = (255, 230, 0)
LARANJA    = (255, 140, 0)
ROXO       = (180, 0, 255)
CINZA      = (80, 80, 80)
AZUL_ESC   = (10, 10, 40)


# FUNÇÕES DE TRANSFORMAÇÃO GEOMÉTRICA

def rotacionar_ponto(x: float, y: float, theta: float):
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    x_rot = x * cos_t - y * sin_t
    y_rot = x * sin_t + y * cos_t
    return x_rot, y_rot


def transladar_ponto(x_rot: float, y_rot: float, tx: float, ty: float):
    return x_rot + tx, y_rot + ty


def transformar_vertices(vertices_locais: list, theta: float, tx: float, ty: float):
    resultado = []
    for (x, y) in vertices_locais:
        x_rot, y_rot = rotacionar_ponto(x, y, theta)
        x_fin, y_fin = transladar_ponto(x_rot, y_rot, tx, ty)
        resultado.append((x_fin, y_fin))
    return resultado


# FUNÇÕES DE COLISÃO (implementadas manualmente)

def colisao_circular(ax: float, ay: float, ra: float,
                     bx: float, by: float, rb: float) -> bool:
    dx = bx - ax
    dy = by - ay
    distancia_sq = dx * dx + dy * dy
    soma_raios = ra + rb
    return distancia_sq <= soma_raios * soma_raios


def colisao_aabb(ax: float, ay: float, aw: float, ah: float,
                 bx: float, by: float, bw: float, bh: float) -> bool:
    a_esq  = ax - aw / 2
    a_dir  = ax + aw / 2
    a_topo = ay - ah / 2
    a_bx   = ay + ah / 2

    b_esq  = bx - bw / 2
    b_dir  = bx + bw / 2
    b_topo = by - bh / 2
    b_bx   = by + bh / 2

    return (a_esq < b_dir and a_dir > b_esq and
            a_topo < b_bx and a_bx > b_topo)


# ===========================================================================
# CLASSE: Estrela (fundo animado)
# ===========================================================================

class Estrela:
    def __init__(self):
        self.x = random.randint(0, LARGURA)
        self.y = random.randint(0, ALTURA)
        self.vel = random.uniform(0.5, 2.5)
        self.raio = random.randint(1, 2)
        brilho = random.randint(120, 255)
        self.cor = (brilho, brilho, brilho)

    def update(self):
        self.y += self.vel
        if self.y > ALTURA:
            self.y = 0
            self.x = random.randint(0, LARGURA)

    def draw(self, tela):
        pygame.draw.circle(tela, self.cor, (int(self.x), int(self.y)), self.raio)


# ===========================================================================
# CLASSE: Bullet (projétil)
# ===========================================================================

class Bullet:
    VELOCIDADE = 10
    RAIO       = 4

    def __init__(self, x: float, y: float, angulo: float):
        self.x = x
        self.y = y
        self.dx = math.sin(angulo) * self.VELOCIDADE
        self.dy = -math.cos(angulo) * self.VELOCIDADE
        self.ativo = True

    def update(self):
        self.x += self.dx
        self.y += self.dy
        if (self.x < -10 or self.x > LARGURA + 10 or
                self.y < -10 or self.y > ALTURA + 10):
            self.ativo = False

    def draw(self, tela):
        pygame.draw.circle(tela, AMARELO,
                           (int(self.x), int(self.y)), self.RAIO)
        pygame.draw.circle(tela, BRANCO,
                           (int(self.x), int(self.y)), self.RAIO - 2)


# ===========================================================================
# CLASSE: Player (nave do jogador)
# ===========================================================================

class Player:
    VELOCIDADE = 5
    RAIO       = 18

    VERTICES_LOCAIS = [
        (0,   -20),
        (-12,  14),
        (0,    8),
        (12,   14),
    ]

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.angulo = 0.0          # Fixo em 0 (apontado sempre para cima)
        self.vidas = 3
        self.invencivel = False
        self.timer_inv = 0
        self.DUR_INV = 90

        self.particulas = []

    def update(self, teclas):
        # --- MOVIMENTO (Apenas Eixo X) ---
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            self.x -= self.VELOCIDADE
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            self.x += self.VELOCIDADE

        # Limita posição dentro da tela (apenas X importa agora)
        self.x = max(20, min(LARGURA - 20, self.x))

        # --- Invencibilidade temporária ---
        if self.invencivel:
            self.timer_inv -= 1
            if self.timer_inv <= 0:
                self.invencivel = False


    def atirar(self):
        px, py = rotacionar_ponto(0, -20, self.angulo)
        px += self.x
        py += self.y
        return Bullet(px, py, self.angulo)

    def tomar_dano(self):
        if not self.invencivel:
            self.vidas -= 1
            self.invencivel = True
            self.timer_inv = self.DUR_INV

    def draw(self, tela):
        for p in self.particulas:
            alpha = int(255 * (p['vida'] / 20))
            r = max(1, p['vida'] // 4)
            pygame.draw.circle(tela, p['cor'], (int(p['x']), int(p['y'])), r)

        verts_mundo = transformar_vertices(
            self.VERTICES_LOCAIS, self.angulo, self.x, self.y
        )

        if self.invencivel and (self.timer_inv // 6) % 2 == 0:
            return

        pygame.draw.polygon(tela, CINZA, [(int(x+2), int(y+2)) for x, y in verts_mundo])

        cor_nave = CIANO if not self.invencivel else VERMELHO
        pygame.draw.polygon(tela, cor_nave, [(int(x), int(y)) for x, y in verts_mundo])

        pygame.draw.polygon(tela, BRANCO,
                            [(int(x), int(y)) for x, y in verts_mundo], 1)

        pygame.draw.circle(tela, BRANCO, (int(self.x), int(self.y)), 3)


# ===========================================================================
# CLASSE: Enemy (inimigo)
# ===========================================================================

class Enemy:
    VELOCIDADE_BASE = 1.8
    RAIO            = 16

    def __init__(self, x: float, y: float, tipo: int = 0):
        self.x = float(x)
        self.y = float(y)
        self.x_inicial = float(x)
        self.tipo = tipo
        self.ativo = True
        self.tempo = random.uniform(0, math.pi * 2)
        self.velocidade = self.VELOCIDADE_BASE + random.uniform(0, 1.0)

        self.amplitude = random.uniform(60, 120)
        self.freq = random.uniform(1.5, 3.0)

        if self.tipo == 0:
            n = 6
            self.vertices_locais = [
                (self.RAIO * math.cos(math.radians(i * 60 - 30)),
                 self.RAIO * math.sin(math.radians(i * 60 - 30)))
                for i in range(n)
            ]
            self.cor       = VERMELHO
            self.cor_borda = LARANJA
        else:
            r = self.RAIO
            self.vertices_locais = [
                (0, -r),
                (r * 0.7, 0),
                (0, r),
                (-r * 0.7, 0),
            ]
            self.cor       = ROXO
            self.cor_borda = CIANO

        self.angulo = 0.0
        self.vel_rot = random.uniform(-0.04, 0.04)

    def update(self, dt: float = 1.0):
        self.tempo += 0.03 * dt
        self.y += self.velocidade * dt

        if self.tipo == 1:
            self.x = self.x_inicial + self.amplitude * math.sin(self.tempo * self.freq)

        self.angulo += self.vel_rot * dt

        if self.y > ALTURA + 30:
            self.ativo = False

    def draw(self, tela):
        verts = transformar_vertices(
            self.vertices_locais, self.angulo, self.x, self.y
        )
        pts = [(int(x), int(y)) for x, y in verts]

        pygame.draw.polygon(tela, self.cor, pts)
        pygame.draw.polygon(tela, self.cor_borda, pts, 2)

        pygame.draw.circle(tela, BRANCO, (int(self.x), int(self.y)), 3)


# ===========================================================================
# CLASSE: Particle (explosão)
# ===========================================================================

class Particula:
    def __init__(self, x: float, y: float, cor):
        self.x = x
        self.y = y
        angulo = random.uniform(0, math.pi * 2)
        speed  = random.uniform(1, 5)
        self.dx = math.cos(angulo) * speed
        self.dy = math.sin(angulo) * speed
        self.vida = random.randint(15, 35)
        self.vida_max = self.vida
        self.cor = cor
        self.raio = random.randint(2, 5)

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.1
        self.vida -= 1

    def draw(self, tela):
        alpha_ratio = self.vida / self.vida_max
        r = max(1, int(self.raio * alpha_ratio))
        cor = tuple(min(255, int(c * alpha_ratio)) for c in self.cor)
        pygame.draw.circle(tela, cor, (int(self.x), int(self.y)), r)


# ===========================================================================
# CLASSE: Game (controlador principal)
# ===========================================================================

class Game:
    def __init__(self):
        pygame.init()
        self.tela  = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Space Invaders Style — Computação Gráfica 2D")
        self.clock = pygame.time.Clock()

        self.fonte_hud    = pygame.font.SysFont("consolas", 20, bold=True)
        self.fonte_grande = pygame.font.SysFont("consolas", 48, bold=True)
        self.fonte_media  = pygame.font.SysFont("consolas", 28)

        self._inicializar()

    def _inicializar(self):
        # A nave nasce na base da tela e ali permanecerá fixada no eixo Y
        self.player     = Player(LARGURA // 2, ALTURA - 50)
        self.inimigos   = []
        self.projéteis  = []
        self.particulas = []
        self.estrelas   = [Estrela() for _ in range(120)]

        self.pontuacao       = 0
        self.game_over       = False

        self.timer_spawn     = 0
        self.intervalo_spawn = 120
        self.dificuldade     = 0

    def _spawn_inimigo(self):
        x = random.randint(30, LARGURA - 30)
        y = random.randint(-60, -20)
        prob_onda = min(0.5, 0.2 + self.dificuldade * 0.05)
        tipo = 1 if random.random() < prob_onda else 0
        self.inimigos.append(Enemy(x, y, tipo))

    def _processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_r and self.game_over:
                    self._inicializar()

                # Atirar com a barra de espaço (sem mouse)
                if evento.key == pygame.K_SPACE and not self.game_over:
                    self.projéteis.append(self.player.atirar())

    def _atualizar(self):
        if self.game_over:
            return

        teclas = pygame.key.get_pressed()

        for e in self.estrelas:
            e.update()

        # Agora passamos apenas as teclas (sem a posição do mouse)
        self.player.update(teclas)

        for b in self.projéteis:
            b.update()
        self.projéteis = [b for b in self.projéteis if b.ativo]

        for en in self.inimigos:
            en.update()
        self.inimigos = [en for en in self.inimigos if en.ativo]

        for p in self.particulas:
            p.update()
        self.particulas = [p for p in self.particulas if p.vida > 0]

        self.timer_spawn += 1
        if self.timer_spawn >= self.intervalo_spawn:
            self.timer_spawn = 0
            self._spawn_inimigo()
            if self.intervalo_spawn > 40:
                self.intervalo_spawn -= 1
            self.dificuldade += 1

        self._verificar_colisoes()

        if self.player.vidas <= 0:
            self.game_over = True

    def _verificar_colisoes(self):
        inimigos_vivos = []

        for en in self.inimigos:
            destruido = False

            for b in self.projéteis:
                if not b.ativo:
                    continue
                if colisao_circular(b.x, b.y, b.RAIO,
                                    en.x, en.y, en.RAIO):
                    b.ativo = False
                    destruido = True
                    self.pontuacao += 10

                    for _ in range(20):
                        self.particulas.append(
                            Particula(en.x, en.y, en.cor)
                        )
                    break 

            if not destruido:
                if colisao_circular(self.player.x, self.player.y, self.player.RAIO,
                                    en.x, en.y, en.RAIO):
                    self.player.tomar_dano()
                    destruido = True
                    for _ in range(15):
                        self.particulas.append(
                            Particula(en.x, en.y, LARANJA)
                        )

            if not destruido:
                inimigos_vivos.append(en)

        self.inimigos = inimigos_vivos

    def _renderizar(self):
        self.tela.fill(PRETO)

        for e in self.estrelas:
            e.draw(self.tela)

        if not self.game_over:
            for p in self.particulas:
                p.draw(self.tela)

            for en in self.inimigos:
                en.draw(self.tela)

            for b in self.projéteis:
                b.draw(self.tela)

            self.player.draw(self.tela)

            txt_pts = self.fonte_hud.render(
                f"PONTOS: {self.pontuacao}", True, AMARELO
            )
            self.tela.blit(txt_pts, (10, 10))

            for i in range(self.player.vidas):
                vx = 90 + i * 30
                vy = 38
                verts_vida = transformar_vertices(
                    [(0, -8), (-5, 6), (0, 3), (5, 6)], 0, vx + 10, vy
                )
                pygame.draw.polygon(self.tela, CIANO,
                                    [(int(x), int(y)) for x, y in verts_vida])

            txt_vidas = self.fonte_hud.render("VIDAS:", True, CIANO)
            self.tela.blit(txt_vidas, (10, 28))

        else:
            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.tela.blit(overlay, (0, 0))

            txt_go = self.fonte_grande.render("GAME OVER", True, VERMELHO)
            self.tela.blit(txt_go,
                           (LARGURA // 2 - txt_go.get_width() // 2, ALTURA // 2 - 80))

            txt_sc = self.fonte_media.render(
                f"Pontuação Final: {self.pontuacao}", True, AMARELO
            )
            self.tela.blit(txt_sc,
                           (LARGURA // 2 - txt_sc.get_width() // 2, ALTURA // 2))

            txt_r = self.fonte_media.render("Pressione R para reiniciar", True, BRANCO)
            self.tela.blit(txt_r,
                           (LARGURA // 2 - txt_r.get_width() // 2, ALTURA // 2 + 60))

        fps_txt = self.fonte_hud.render(
            f"FPS: {int(self.clock.get_fps())}", True, CINZA
        )
        self.tela.blit(fps_txt, (LARGURA - 90, 10))

        pygame.display.flip()

    def run(self):
        while True:
            self._processar_eventos()
            self._atualizar()
            self._renderizar()
            self.clock.tick(FPS)


if __name__ == "__main__":
    jogo = Game()
    jogo.run()
