"""
=============================================================================
SPACE SHOOTER - Mini Game 2D em Python/Pygame
=============================================================================
Demonstra conceitos de Computação Gráfica:
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

# ---------------------------------------------------------------------------
# CONSTANTES GLOBAIS
# ---------------------------------------------------------------------------
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


# ===========================================================================
# FUNÇÕES DE TRANSFORMAÇÃO GEOMÉTRICA
# ===========================================================================

def rotacionar_ponto(x: float, y: float, theta: float):
    """
    ROTAÇÃO 2D — aplica a matriz de rotação sobre um ponto (x, y).

    Matriz de Rotação:
        | cos(θ)  -sin(θ) |   | x |
        | sin(θ)   cos(θ) | × | y |

    Fórmulas:
        x' = x * cos(θ) - y * sin(θ)
        y' = x * sin(θ) + y * cos(θ)

    Parâmetros:
        x, y  – coordenadas locais do ponto
        theta – ângulo de rotação em radianos

    Retorna:
        (x', y') – ponto rotacionado
    """
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    x_rot = x * cos_t - y * sin_t
    y_rot = x * sin_t + y * cos_t
    return x_rot, y_rot


def transladar_ponto(x_rot: float, y_rot: float, tx: float, ty: float):
    """
    TRANSLAÇÃO 2D — desloca um ponto já rotacionado para o espaço mundial.

    Fórmulas:
        x_final = x' + tx
        y_final = y' + ty

    Parâmetros:
        x_rot, y_rot – coordenadas após a rotação
        tx, ty       – deslocamento (posição do objeto no mundo)

    Retorna:
        (x_final, y_final) – ponto em coordenadas mundiais
    """
    return x_rot + tx, y_rot + ty


def transformar_vertices(vertices_locais: list, theta: float, tx: float, ty: float):
    """
    Aplica ROTAÇÃO seguida de TRANSLAÇÃO em uma lista de vértices locais.

    Esta é a pipeline completa de transformação:
        1. Rotacionar em torno da origem local (0,0)
        2. Transladar para a posição mundial (tx, ty)

    Retorna lista de tuplas (x, y) prontas para pygame.draw.polygon().
    """
    resultado = []
    for (x, y) in vertices_locais:
        x_rot, y_rot = rotacionar_ponto(x, y, theta)
        x_fin, y_fin = transladar_ponto(x_rot, y_rot, tx, ty)
        resultado.append((x_fin, y_fin))
    return resultado


# ===========================================================================
# FUNÇÕES DE COLISÃO (implementadas manualmente)
# ===========================================================================

def colisao_circular(ax: float, ay: float, ra: float,
                     bx: float, by: float, rb: float) -> bool:
    """
    COLISÃO CIRCULAR — verifica se dois círculos se intersectam.

    Princípio: dois círculos colidem quando a distância entre seus centros
    é menor ou igual à soma de seus raios.

        distância = sqrt((bx-ax)² + (by-ay)²)
        colisão   = distância <= ra + rb

    Usamos distância² para evitar sqrt (otimização).

    Parâmetros:
        ax, ay – centro do objeto A
        ra     – raio do objeto A
        bx, by – centro do objeto B
        rb     – raio do objeto B

    Retorna:
        True se houver colisão, False caso contrário.
    """
    dx = bx - ax
    dy = by - ay
    distancia_sq = dx * dx + dy * dy
    soma_raios = ra + rb
    return distancia_sq <= soma_raios * soma_raios


def colisao_aabb(ax: float, ay: float, aw: float, ah: float,
                 bx: float, by: float, bw: float, bh: float) -> bool:
    """
    COLISÃO AABB (Axis-Aligned Bounding Box) — caixas sem rotação.

    Dois retângulos NÃO colidem se um estiver completamente fora do outro
    em qualquer eixo. Logo, colidem quando TODAS as condições forem verdadeiras:
        A.esquerda < B.direita
        A.direita  > B.esquerda
        A.topo     < B.baixo
        A.baixo    > B.topo

    Parâmetros:
        ax, ay – centro do objeto A
        aw, ah – largura e altura do objeto A
        bx, by – centro do objeto B
        bw, bh – largura e altura do objeto B

    Retorna:
        True se houver colisão.
    """
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
    """Estrela do fundo — ponto branco que cria parallax simples."""

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
    """
    Projétil disparado pelo jogador.

    O vetor de direção é calculado no momento do disparo a partir do ângulo
    da nave, garantindo que o tiro siga a orientação atual.
    """

    VELOCIDADE = 10
    RAIO       = 4    # raio para colisão circular

    def __init__(self, x: float, y: float, angulo: float):
        self.x = x
        self.y = y
        # Vetor de direção baseado no ângulo da nave
        # (ângulo aponta para cima na convenção local, -π/2 alinha com eixo Y)
        self.dx = math.sin(angulo) * self.VELOCIDADE
        self.dy = -math.cos(angulo) * self.VELOCIDADE
        self.ativo = True

    def update(self):
        """Translação simples: soma vetor de direção à posição atual."""
        self.x += self.dx
        self.y += self.dy
        # Remove projétil que saiu da tela
        if (self.x < -10 or self.x > LARGURA + 10 or
                self.y < -10 or self.y > ALTURA + 10):
            self.ativo = False

    def draw(self, tela):
        """Desenha como pequeno círculo brilhante com 'brilho' ao redor."""
        pygame.draw.circle(tela, AMARELO,
                           (int(self.x), int(self.y)), self.RAIO)
        pygame.draw.circle(tela, BRANCO,
                           (int(self.x), int(self.y)), self.RAIO - 2)


# ===========================================================================
# CLASSE: Player (nave do jogador)
# ===========================================================================

class Player:
    """
    Nave do jogador representada por um triângulo com vértices locais.

    Pipeline de transformação por frame:
        1. Calcular ângulo de rotação (apontar para o mouse)
        2. Aplicar rotação em cada vértice local → coordenadas giradas
        3. Aplicar translação → coordenadas mundiais
        4. Desenhar polígono com as coordenadas mundiais
    """

    VELOCIDADE = 4
    RAIO       = 18   # raio aproximado para colisão

    # Vértices locais do triângulo da nave (origem = centro da nave)
    # Triângulo apontando para cima (eixo Y negativo = "frente")
    VERTICES_LOCAIS = [
        (0,   -20),   # ponta da frente (topo)
        (-12,  14),   # asa esquerda
        (0,    8),    # recuo central (traseira interna)
        (12,   14),   # asa direita
    ]

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.angulo = 0.0          # ângulo de rotação em radianos
        self.vidas = 3
        self.invencivel = False    # frames de invencibilidade após dano
        self.timer_inv = 0
        self.DUR_INV = 90          # 1.5 s a 60 FPS

        # Rastro de partículas do propulsor
        self.particulas = []

    def update(self, teclas, mouse_pos):
        """
        Atualiza posição (WASD), ângulo (mouse) e estado do jogador.
        """
        # --- MOVIMENTO (Translação incremental) ---
        if teclas[pygame.K_w]:
            self.y -= self.VELOCIDADE
        if teclas[pygame.K_s]:
            self.y += self.VELOCIDADE
        if teclas[pygame.K_a]:
            self.x -= self.VELOCIDADE
        if teclas[pygame.K_d]:
            self.x += self.VELOCIDADE

        # Limita posição dentro da tela
        self.x = max(20, min(LARGURA - 20, self.x))
        self.y = max(20, min(ALTURA - 20, self.y))

        # --- ROTAÇÃO — aponta para o mouse ---
        # Calcula o vetor da nave até o mouse
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        # atan2 devolve ângulo em relação ao eixo X; ajustamos para Y negativo
        self.angulo = math.atan2(dx, -dy)

        # --- Invencibilidade temporária ---
        if self.invencivel:
            self.timer_inv -= 1
            if self.timer_inv <= 0:
                self.invencivel = False

        # --- Partículas do propulsor ---
        # Gera partículas na traseira da nave quando se move
        movendo = (teclas[pygame.K_w] or teclas[pygame.K_s] or
                   teclas[pygame.K_a] or teclas[pygame.K_d])
        if movendo:
            # Calcula posição traseira da nave (vértice (0, 14) em locais)
            tx_local, ty_local = 0, 14
            px, py = rotacionar_ponto(tx_local, ty_local, self.angulo)
            px += self.x
            py += self.y
            self.particulas.append({
                'x': px + random.uniform(-4, 4),
                'y': py + random.uniform(-4, 4),
                'vida': random.randint(10, 20),
                'cor': random.choice([LARANJA, AMARELO, VERMELHO])
            })

        # Atualiza e remove partículas mortas
        for p in self.particulas:
            p['vida'] -= 1
        self.particulas = [p for p in self.particulas if p['vida'] > 0]

    def atirar(self):
        """Cria um projétil na ponta da nave com a direção atual."""
        # Ponta da nave: vértice local (0, -20) rotacionado + translação
        px, py = rotacionar_ponto(0, -20, self.angulo)
        px += self.x
        py += self.y
        return Bullet(px, py, self.angulo)

    def tomar_dano(self):
        """Reduz vidas se não estiver invencível."""
        if not self.invencivel:
            self.vidas -= 1
            self.invencivel = True
            self.timer_inv = self.DUR_INV

    def draw(self, tela):
        """
        Renderiza a nave:
         1. Partículas do propulsor
         2. Contorno externo (sombra)
         3. Polígono principal
         4. Detalhe central
        """
        # Partículas
        for p in self.particulas:
            alpha = int(255 * (p['vida'] / 20))
            r = max(1, p['vida'] // 4)
            pygame.draw.circle(tela, p['cor'], (int(p['x']), int(p['y'])), r)

        # Transforma vértices: ROTAÇÃO + TRANSLAÇÃO
        verts_mundo = transformar_vertices(
            self.VERTICES_LOCAIS, self.angulo, self.x, self.y
        )

        # Pisca durante invencibilidade
        if self.invencivel and (self.timer_inv // 6) % 2 == 0:
            return

        # Sombra / borda
        pygame.draw.polygon(tela, CINZA, [(int(x+2), int(y+2)) for x, y in verts_mundo])

        # Corpo da nave
        cor_nave = CIANO if not self.invencivel else AMARELO
        pygame.draw.polygon(tela, cor_nave, [(int(x), int(y)) for x, y in verts_mundo])

        # Contorno
        pygame.draw.polygon(tela, BRANCO,
                            [(int(x), int(y)) for x, y in verts_mundo], 1)

        # Detalhe: pequeno círculo central (cockpit)
        pygame.draw.circle(tela, BRANCO, (int(self.x), int(self.y)), 3)


# ===========================================================================
# CLASSE: Enemy (inimigo)
# ===========================================================================

class Enemy:
    """
    Inimigo com dois tipos de movimento:
      - Tipo 0: movimento reto para baixo
      - Tipo 1: movimento ondulatório (seno) — x = x_inicial + A * sin(t)

    Representados por polígonos simples (hexágono ou losango).
    """

    VELOCIDADE_BASE = 1.8
    RAIO            = 16   # raio para colisão

    def __init__(self, x: float, y: float, tipo: int = 0):
        self.x = float(x)
        self.y = float(y)
        self.x_inicial = float(x)   # posição X de referência para seno
        self.tipo = tipo
        self.ativo = True
        self.tempo = random.uniform(0, math.pi * 2)  # fase inicial aleatória
        self.velocidade = self.VELOCIDADE_BASE + random.uniform(0, 1.0)

        # Parâmetros do movimento ondulatório
        self.amplitude = random.uniform(60, 120)
        self.freq = random.uniform(1.5, 3.0)

        # Vértices locais dependem do tipo
        if self.tipo == 0:
            # Hexágono achatado
            n = 6
            self.vertices_locais = [
                (self.RAIO * math.cos(math.radians(i * 60 - 30)),
                 self.RAIO * math.sin(math.radians(i * 60 - 30)))
                for i in range(n)
            ]
            self.cor       = VERMELHO
            self.cor_borda = LARANJA
        else:
            # Losango (4 pontas)
            r = self.RAIO
            self.vertices_locais = [
                (0, -r),
                (r * 0.7, 0),
                (0, r),
                (-r * 0.7, 0),
            ]
            self.cor       = ROXO
            self.cor_borda = CIANO

        # Ângulo de rotação (para animação visual)
        self.angulo = 0.0
        self.vel_rot = random.uniform(-0.04, 0.04)

    def update(self, dt: float = 1.0):
        """
        Atualiza posição do inimigo.

        Tipo 0 — translação vertical simples:
            y += velocidade

        Tipo 1 — movimento ondulatório:
            x = x_inicial + amplitude * sin(tempo * freq)
            y += velocidade
        """
        self.tempo += 0.03 * dt

        # Movimento vertical (todos os tipos)
        self.y += self.velocidade * dt

        # Movimento horizontal ondulatório (apenas tipo 1)
        if self.tipo == 1:
            # SENO — oscilação em X baseada no tempo
            self.x = self.x_inicial + self.amplitude * math.sin(self.tempo * self.freq)

        # Rotação visual contínua
        self.angulo += self.vel_rot * dt

        # Desativa ao sair da tela
        if self.y > ALTURA + 30:
            self.ativo = False

    def draw(self, tela):
        """
        Desenha o inimigo com rotação aplicada manualmente via
        transformar_vertices() (rotação + translação).
        """
        # Transforma vértices: ROTAÇÃO + TRANSLAÇÃO
        verts = transformar_vertices(
            self.vertices_locais, self.angulo, self.x, self.y
        )
        pts = [(int(x), int(y)) for x, y in verts]

        pygame.draw.polygon(tela, self.cor, pts)
        pygame.draw.polygon(tela, self.cor_borda, pts, 2)

        # Pequeno "núcleo" brilhante
        pygame.draw.circle(tela, BRANCO, (int(self.x), int(self.y)), 3)


# ===========================================================================
# CLASSE: Particle (explosão)
# ===========================================================================

class Particula:
    """Partícula de explosão — usada ao destruir um inimigo."""

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
        self.dy += 0.1   # gravidade leve
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
    """
    GAME LOOP PRINCIPAL
    ===================
    Segue o padrão clássico de game loop:
        while rodando:
            1. Processar eventos (input do usuário)
            2. Atualizar lógica (física, IA, colisões)
            3. Renderizar (desenhar tudo na tela)
            4. clock.tick(FPS)  → controla velocidade
    """

    def __init__(self):
        pygame.init()
        self.tela  = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Space Shooter — Computação Gráfica 2D")
        self.clock = pygame.time.Clock()

        # Fontes
        self.fonte_hud   = pygame.font.SysFont("consolas", 20, bold=True)
        self.fonte_grande = pygame.font.SysFont("consolas", 48, bold=True)
        self.fonte_media  = pygame.font.SysFont("consolas", 28)

        self._inicializar()

    def _inicializar(self):
        """Inicializa / reinicia todos os objetos do jogo."""
        self.player     = Player(LARGURA // 2, ALTURA - 100)
        self.inimigos   = []
        self.projéteis  = []
        self.particulas = []
        self.estrelas   = [Estrela() for _ in range(120)]

        self.pontuacao       = 0
        self.game_over       = False

        # Controle de spawn de inimigos
        self.timer_spawn     = 0
        self.intervalo_spawn = 120   # frames entre spawns (2 s a 60 FPS)
        self.dificuldade     = 0     # aumenta com o tempo

    # -----------------------------------------------------------------------
    # SPAWN DE INIMIGOS
    # -----------------------------------------------------------------------
    def _spawn_inimigo(self):
        """
        SPAWN — cria um novo inimigo em posição aleatória no topo da tela.

        Tipo 0 (movimento reto) ou Tipo 1 (ondulatório) são escolhidos
        aleatoriamente, com maior chance de tipo 1 conforme a dificuldade.
        """
        x = random.randint(30, LARGURA - 30)
        y = random.randint(-60, -20)
        prob_onda = min(0.5, 0.2 + self.dificuldade * 0.05)
        tipo = 1 if random.random() < prob_onda else 0
        self.inimigos.append(Enemy(x, y, tipo))

    # -----------------------------------------------------------------------
    # PROCESSAMENTO DE EVENTOS
    # -----------------------------------------------------------------------
    def _processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                # Reinicia ao pressionar R no game over
                if evento.key == pygame.K_r and self.game_over:
                    self._inicializar()

            # Tiro com clique esquerdo do mouse
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1 and not self.game_over:
                    self.projéteis.append(self.player.atirar())

    # -----------------------------------------------------------------------
    # ATUALIZAÇÃO DA LÓGICA
    # -----------------------------------------------------------------------
    def _atualizar(self):
        if self.game_over:
            return

        teclas    = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Atualiza fundo
        for e in self.estrelas:
            e.update()

        # Atualiza jogador
        self.player.update(teclas, mouse_pos)

        # Atualiza projéteis
        for b in self.projéteis:
            b.update()
        self.projéteis = [b for b in self.projéteis if b.ativo]

        # Atualiza inimigos
        for en in self.inimigos:
            en.update()
        self.inimigos = [en for en in self.inimigos if en.ativo]

        # Atualiza partículas de explosão
        for p in self.particulas:
            p.update()
        self.particulas = [p for p in self.particulas if p.vida > 0]

        # --- SPAWN ---
        self.timer_spawn += 1
        if self.timer_spawn >= self.intervalo_spawn:
            self.timer_spawn = 0
            self._spawn_inimigo()
            # Aumenta dificuldade reduzindo intervalo de spawn
            if self.intervalo_spawn > 40:
                self.intervalo_spawn -= 1
            self.dificuldade += 1

        # --- COLISÕES ---
        self._verificar_colisoes()

        # Game over se sem vidas
        if self.player.vidas <= 0:
            self.game_over = True

    # -----------------------------------------------------------------------
    # VERIFICAÇÃO DE COLISÕES (implementada manualmente)
    # -----------------------------------------------------------------------
    def _verificar_colisoes(self):
        """
        SISTEMA DE COLISÃO MANUAL
        =========================
        Usa colisão_circular() para:
          a) Tiro × Inimigo
          b) Jogador × Inimigo

        Não utiliza pygame.sprite.colliderect() nem nenhum método pronto.
        """
        inimigos_vivos = []

        for en in self.inimigos:
            destruido = False

            # (a) COLISÃO: Tiro × Inimigo
            for b in self.projéteis:
                if not b.ativo:
                    continue
                if colisao_circular(b.x, b.y, b.RAIO,
                                    en.x, en.y, en.RAIO):
                    # Colisão detectada!
                    b.ativo = False    # remove projétil
                    destruido = True
                    self.pontuacao += 10  # +10 pontos por inimigo

                    # Gera explosão de partículas
                    for _ in range(20):
                        self.particulas.append(
                            Particula(en.x, en.y, en.cor)
                        )
                    break  # inimigo já destruído, sai do loop de tiros

            # (b) COLISÃO: Jogador × Inimigo
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

    # -----------------------------------------------------------------------
    # RENDERIZAÇÃO
    # -----------------------------------------------------------------------
    def _renderizar(self):
        # Fundo escuro
        self.tela.fill(AZUL_ESC)

        # Estrelas de fundo
        for e in self.estrelas:
            e.draw(self.tela)

        if not self.game_over:
            # Partículas de explosão
            for p in self.particulas:
                p.draw(self.tela)

            # Inimigos
            for en in self.inimigos:
                en.draw(self.tela)

            # Projéteis
            for b in self.projéteis:
                b.draw(self.tela)

            # Jogador
            self.player.draw(self.tela)

            # HUD — Pontuação
            txt_pts = self.fonte_hud.render(
                f"PONTOS: {self.pontuacao}", True, AMARELO
            )
            self.tela.blit(txt_pts, (10, 10))

            # HUD — Vidas (corações / triângulos)
            for i in range(self.player.vidas):
                # Pequena nave como ícone de vida
                vx = 10 + i * 30
                vy = 38
                verts_vida = transformar_vertices(
                    [(0, -8), (-5, 6), (0, 3), (5, 6)], 0, vx + 10, vy
                )
                pygame.draw.polygon(self.tela, CIANO,
                                    [(int(x), int(y)) for x, y in verts_vida])

            txt_vidas = self.fonte_hud.render("VIDAS:", True, CIANO)
            self.tela.blit(txt_vidas, (10, 28))

            # Ponteiro de mira (crosshair)
            mx, my = pygame.mouse.get_pos()
            pygame.draw.line(self.tela, VERDE, (mx - 10, my), (mx + 10, my), 1)
            pygame.draw.line(self.tela, VERDE, (mx, my - 10), (mx, my + 10), 1)
            pygame.draw.circle(self.tela, VERDE, (mx, my), 8, 1)

        else:
            # --- TELA DE GAME OVER ---
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

        # FPS (canto superior direito)
        fps_txt = self.fonte_hud.render(
            f"FPS: {int(self.clock.get_fps())}", True, CINZA
        )
        self.tela.blit(fps_txt, (LARGURA - 90, 10))

        pygame.display.flip()

    # -----------------------------------------------------------------------
    # LOOP PRINCIPAL
    # -----------------------------------------------------------------------
    def run(self):
        """
        GAME LOOP TRADICIONAL
        =====================
        Executa continuamente até o usuário fechar a janela.

        Cada iteração:
          1. _processar_eventos()  → input do usuário
          2. _atualizar()          → lógica do jogo
          3. _renderizar()         → desenho na tela
          4. clock.tick(FPS)       → limita a ~60 FPS
        """
        while True:
            # 1. Eventos
            self._processar_eventos()
            # 2. Lógica
            self._atualizar()
            # 3. Renderização
            self._renderizar()
            # 4. Controle de FPS — limita a 60 quadros/segundo
            self.clock.tick(FPS)


# ===========================================================================
# PONTO DE ENTRADA
# ===========================================================================
if __name__ == "__main__":
    jogo = Game()
    jogo.run()
