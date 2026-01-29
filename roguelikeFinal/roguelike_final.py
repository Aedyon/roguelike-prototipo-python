import pygame
import sys
import random

# --- CONFIGURAÇÕES ---
LARGURA_TELA = 800
ALTURA_TELA = 600
TILE_W = 64
TILE_H = 32
FPS = 60

# Cores (Placeholders para quando não tiver Sprite)
CORES = {
    'bg': (20, 20, 30),
    'chao': (34, 139, 34),
    'parede': (60, 60, 70),
    'player': (50, 100, 255),
    'inimigo': (200, 50, 50),
    'boss': (100, 0, 0),
    'bau': (255, 215, 0),
    'fonte': (0, 255, 255), # Buff
    'portal': (148, 0, 211),
    'ui_bg': (0, 0, 0, 200),
    'texto': (255, 255, 255),
    'selecionado': (255, 255, 0)
}

# --- SISTEMA DE ASSETS ---
# --- CLASSE DE ASSETS ADAPTADA PARA SUA PASTA ---
class AssetManager:
    def __init__(self):
        self.sprites = {}
        
        # Caminhos base baseados nos seus prints
        # O "." significa a pasta atual onde está o script
        base_iso = "assets/miniature dungeon/Isometric/"
        base_char = "assets/miniature dungeon/Characters/Male/"
        
        try:
            # 1. CARREGAR CHÃO (stone_N.png do Print 2)
            img_chao = pygame.image.load(base_iso + "stone_N.png").convert_alpha()
            # Ajuste fino: Kenney tiles costumam ser meio grandes, vamos forçar o tamanho do nosso Grid
            self.sprites['chao'] = pygame.transform.scale(img_chao, (TILE_W, int(TILE_H * 2)))

            # 2. CARREGAR PLAYER (Male_0_Idle0.png do Print 4)
            img_human = pygame.image.load(base_char + "Male_0_Idle0.png").convert_alpha()
            # Escala do personagem (ajuste conforme achar bonito)
            img_human = pygame.transform.scale(img_human, (40, 60))
            
            self.sprites['player'] = img_human
            
            # 3. CRIAR INIMIGOS (Usando o mesmo sprite, mas pintando de outra cor)
            # Inimigo Comum (Vermelho)
            self.sprites['inimigo'] = self.tingir_imagem(img_human, (200, 50, 50))
            # Boss (Grande e Roxo)
            boss_base = pygame.transform.scale(img_human, (80, 120))
            self.sprites['boss'] = self.tingir_imagem(boss_base, (100, 0, 100))

            # 4. OBJETOS
            # Baú (chestClose_N.png do Print 1)
            img_bau = pygame.image.load(base_iso + "chestClose_N.png").convert_alpha()
            self.sprites['bau'] = pygame.transform.scale(img_bau, (50, 50))
            
            # Fonte (Improviso: barrel_N.png do Print 1)
            img_fonte = pygame.image.load(base_iso + "barrel_N.png").convert_alpha()
            self.sprites['fonte'] = pygame.transform.scale(img_fonte, (40, 50))
            
            # Portal (stairs_N.png do Print 2 - Escada para descer)
            img_portal = pygame.image.load(base_iso + "stairs_N.png").convert_alpha()
            self.sprites['portal'] = pygame.transform.scale(img_portal, (TILE_W, int(TILE_H * 2.5)))

            print("Sucesso! Sprites do Kenney carregados.")

        except Exception as e:
            print(f"ERRO DE ARQUIVO: {e}")
            print("Verifique se o nome das pastas está igualzinho ao Windows (maiúscula/minúscula).")
            print("Rodando com quadrados coloridos de fallback.")

    def tingir_imagem(self, imagem, cor):
        """Cria uma cópia da imagem e pinta ela com uma cor (para inimigos)"""
        imagem_colorida = imagem.copy()
        # Cria uma superficie da mesma cor para misturar
        filtro = pygame.Surface(imagem_colorida.get_size()).convert_alpha()
        filtro.fill(cor)
        # BLEND_MULT multiplica as cores (branco vira a cor do filtro)
        imagem_colorida.blit(filtro, (0,0), special_flags=pygame.BLEND_MULT)
        return imagem_colorida

    def desenhar(self, superficie, chave, x, y, cor_placeholder, forma="losango"):
        """Desenha sprite ou fallback geométrico"""
        if chave in self.sprites:
            img = self.sprites[chave]
            rect = img.get_rect()
            
            # --- AJUSTE DE PIVÔ (CENTRALIZAÇÃO) ---
            if chave == 'chao':
                # Chão centraliza no meio do tile
                rect.center = (x, y + TILE_H//2)
            elif chave == 'portal':
                # Escada precisa alinhar um pouco diferente pra parecer que desce
                rect.midtop = (x, y - 10)
            else:
                # Personagens e Objetos: Pé da imagem no centro do losango
                rect.midbottom = (x, y + TILE_H)
                
            superficie.blit(img, rect)
        else:
            # Fallback Geométrico (Código antigo)
            if forma == "losango":
                pontos = [(x, y), (x + TILE_W/2, y + TILE_H/2), (x, y + TILE_H), (x - TILE_W/2, y + TILE_H/2)]
                pygame.draw.polygon(superficie, cor_placeholder, pontos)
                pygame.draw.polygon(superficie, (0,0,0), pontos, 1)
            elif forma == "circulo":
                pygame.draw.circle(superficie, cor_placeholder, (int(x), int(y + TILE_H//2)), 15)
            elif forma == "retangulo":
                pygame.draw.rect(superficie, cor_placeholder, (x - 15, y, 30, 30))

# --- CÂMERA ---
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.math.Vector2(0, 0)
        self.width = width
        self.height = height

    def update(self, alvo):
        x = -alvo.visual_x + int(LARGURA_TELA / 2)
        y = -alvo.visual_y + int(ALTURA_TELA / 2)
        # Suavização simples
        self.camera.x += (x - self.camera.x) * 0.1
        self.camera.y += (y - self.camera.y) * 0.1

    def apply(self, x, y):
        return x + self.camera.x, y + self.camera.y

# --- ENTIDADES ---
class Entidade:
    def __init__(self, grid_x, grid_y, nome):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.visual_x, self.visual_y = self.cart_para_iso(grid_x, grid_y)
        self.nome = nome
        self.vivo = True

    def cart_para_iso(self, x, y):
        iso_x = (x - y) * (TILE_W / 2)
        iso_y = (x + y) * (TILE_H / 2)
        return iso_x, iso_y

    def update_visual(self):
        # Move o visual suavemente até o grid
        alvo_x, alvo_y = self.cart_para_iso(self.grid_x, self.grid_y)
        self.visual_x += (alvo_x - self.visual_x) * 0.2
        self.visual_y += (alvo_y - self.visual_y) * 0.2

class Player(Entidade):
    def __init__(self, x, y):
        super().__init__(x, y, "Herói")
        # Status Base
        self.forca = 5
        self.destreza = 3
        self.vitalidade = 10
        
        self.vida_max = self.vitalidade * 10
        self.vida = self.vida_max
        self.xp = 0
        self.nivel = 1
        
        self.inventario = []
        self.arma_equipada = {"nome": "Adaga", "dano": 3, "tipo": "arma"}
        self.cooldown_ataque = 0

    def mover(self, dx, dy, mapa):
        nx, ny = self.grid_x + dx, self.grid_y + dy
        if 0 <= ny < len(mapa) and 0 <= nx < len(mapa[0]):
            if mapa[ny][nx] != 0: # 0 é parede
                self.grid_x, self.grid_y = nx, ny

    def atacar(self, inimigos):
        if self.cooldown_ataque > 0: return None
        self.cooldown_ataque = 30
        
        dano_total = self.arma_equipada['dano'] + self.forca
        msg = "Errou!"
        
        for ini in inimigos:
            if not ini.vivo: continue
            dist = abs(self.grid_x - ini.grid_x) + abs(self.grid_y - ini.grid_y)
            if dist <= 1:
                ini.tomar_dano(dano_total)
                msg = f"Hit {dano_total}!"
                if not ini.vivo:
                    self.xp += ini.xp_drop
        return msg

class Inimigo(Entidade):
    def __init__(self, x, y, nome, stats, boss=False):
        super().__init__(x, y, nome)
        # CORREÇÃO 1: Adicionando vida_max para a barra funcionar
        self.vida_max = stats['vida'] 
        self.vida = stats['vida']
        self.dano = stats['dano']
        self.xp_drop = stats['xp']
        self.boss = boss
        self.timer_acao = 0
        self.velocidade = 60 if not boss else 45

    def update_ia(self, player):
        if not self.vivo: return
        self.timer_acao += 1
        if self.timer_acao >= self.velocidade:
            self.timer_acao = 0
            dist = abs(self.grid_x - player.grid_x) + abs(self.grid_y - player.grid_y)
            
            if dist <= 1: # Atacar
                player.vida -= self.dano
            else: # Perseguir
                dx = 1 if player.grid_x > self.grid_x else -1 if player.grid_x < self.grid_x else 0
                dy = 1 if player.grid_y > self.grid_y else -1 if player.grid_y < self.grid_y else 0
                self.grid_x += dx
                if dx == 0: self.grid_y += dy

    def tomar_dano(self, quant):
        self.vida -= quant
        if self.vida <= 0: self.vivo = False

class ObjetoInterativo(Entidade):
    def __init__(self, x, y, tipo, dados):
        super().__init__(x, y, tipo)
        self.tipo = tipo # 'bau', 'fonte', 'portal'
        self.dados = dados
        self.ativo = True

# --- MOTOR DO JOGO ---
class Game:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption("Roguelike Isométrico Completo")
        self.clock = pygame.time.Clock()
        self.fonte = pygame.font.SysFont('Consolas', 18)
        self.fonte_grande = pygame.font.SysFont('Verdana', 32, bold=True)
        
        self.assets = AssetManager()
        self.camera = Camera(LARGURA_TELA, ALTURA_TELA)
        
        # Estados
        self.STATE_MENU = 0
        self.STATE_PLAY = 1
        self.STATE_PAUSE = 2
        self.STATE_INVENTORY = 3
        self.STATE_GAMEOVER = 4
        self.STATE_WIN = 5
        self.estado_atual = self.STATE_MENU
        
        self.player = Player(2, 2)
        self.sala_atual_idx = 0
        self.salas = []
        self.log_msgs = []
        
        self.criar_salas()
        self.carregar_sala(0)

    def criar_salas(self):
        # 0: Parede, 1: Chão
        layout_padrao = [
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1]
        ]
        
        # Sala 1: Tutorial/Básica
        s1 = {'mapa': layout_padrao, 'tipo': 'combate', 'inimigos': [
            {'nome': 'Slime', 'vida': 20, 'dano': 2, 'xp': 10, 'pos': (4,4)}
        ], 'obj': []}
        
        # Sala 2: Combate Médio
        s2 = {'mapa': layout_padrao, 'tipo': 'combate', 'inimigos': [
            {'nome': 'Goblin', 'vida': 30, 'dano': 5, 'xp': 20, 'pos': (3,3)},
            {'nome': 'Goblin', 'vida': 30, 'dano': 5, 'xp': 20, 'pos': (5,2)}
        ], 'obj': []}
        
        # Sala 3: Item (Tesouro)
        s3 = {'mapa': layout_padrao, 'tipo': 'tesouro', 'inimigos': [], 'obj': [
            {'tipo': 'bau', 'pos': (4,4), 'item': {'nome': 'Espada Longa', 'dano': 8, 'tipo': 'arma'}}
        ]}
        
        # Sala 4: Buff (Fonte)
        s4 = {'mapa': layout_padrao, 'tipo': 'fonte', 'inimigos': [], 'obj': [
            {'tipo': 'fonte', 'pos': (4,4), 'buff': 'vida_full'}
        ]}
        
        # Sala 5: Boss
        s5 = {'mapa': layout_padrao, 'tipo': 'boss', 'inimigos': [
            {'nome': 'REI ORC', 'vida': 150, 'dano': 12, 'xp': 500, 'pos': (5,5), 'boss': True}
        ], 'obj': []}
        
        self.salas = [s1, s2, s3, s4, s5]

    def carregar_sala(self, indice):
        self.sala_atual_idx = indice
        dados = self.salas[indice]
        self.mapa_atual = dados['mapa']
        
        self.inimigos = []
        for ini in dados['inimigos']:
            boss = ini.get('boss', False)
            mob = Inimigo(ini['pos'][0], ini['pos'][1], ini['nome'], ini, boss)
            self.inimigos.append(mob)
            
        self.objetos = []
        for obj in dados['obj']:
            o = ObjetoInterativo(obj['pos'][0], obj['pos'][1], obj['tipo'], obj)
            self.objetos.append(o)
            
        # Adiciona portal de saída
        self.portal = ObjetoInterativo(7, 7, 'portal', {})
        if dados['tipo'] in ['combate', 'boss']:
            self.portal.ativo = False # Trancado
        else:
            self.portal.ativo = True # Aberto
            
        self.objetos.append(self.portal)
        self.player.grid_x, self.player.grid_y = 1, 1 # Spawn seguro
        self.log(f"Entrou na Sala {indice + 1}")

    def log(self, texto):
        self.log_msgs.append(texto)
        if len(self.log_msgs) > 5: self.log_msgs.pop(0)

    def desenhar_texto_central(self, texto, y_offset=0, cor=CORES['texto']):
        surf = self.fonte_grande.render(texto, True, cor)
        rect = surf.get_rect(center=(LARGURA_TELA//2, ALTURA_TELA//2 + y_offset))
        self.tela.blit(surf, rect)

    # --- LOOP PRINCIPAL ---
    def run(self):
        while True:
            self.input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.KEYDOWN:
                # Controles Globais
                if event.key == pygame.K_ESCAPE:
                    if self.estado_atual == self.STATE_PLAY: self.estado_atual = self.STATE_PAUSE
                    elif self.estado_atual == self.STATE_PAUSE: self.estado_atual = self.STATE_PLAY
                    elif self.estado_atual == self.STATE_INVENTORY: self.estado_atual = self.STATE_PLAY

                # Controles por Estado
                if self.estado_atual == self.STATE_MENU:
                    if event.key == pygame.K_RETURN: self.estado_atual = self.STATE_PLAY
                
                elif self.estado_atual == self.STATE_PLAY:
                    dx, dy = 0, 0
                    if event.key == pygame.K_UP: dy = -1
                    elif event.key == pygame.K_DOWN: dy = 1
                    elif event.key == pygame.K_LEFT: dx = -1
                    elif event.key == pygame.K_RIGHT: dx = 1
                    elif event.key == pygame.K_SPACE: 
                        res = self.player.atacar(self.inimigos)
                        if res: self.log(res)
                    elif event.key == pygame.K_i: self.estado_atual = self.STATE_INVENTORY
                    elif event.key == pygame.K_e: self.interagir()
                    
                    if dx != 0 or dy != 0:
                        self.player.mover(dx, dy, self.mapa_atual)
                        # CORREÇÃO 2: Verificar o que tem no chão logo após mover
                        self.checar_piso()

                elif self.estado_atual == self.STATE_GAMEOVER or self.estado_atual == self.STATE_WIN:
                    if event.key == pygame.K_r: # Reiniciar simples (recarrega tudo)
                         self.__init__() 

    def interagir(self):
        # Checa baú ou fonte (Portal agora é automático no checar_piso)
        for obj in self.objetos:
            if self.player.grid_x == obj.grid_x and self.player.grid_y == obj.grid_y:
                if not obj.ativo: 
                    # self.log("Está vazio!") # Removido para não floodar
                    continue
                
                if obj.tipo == 'bau':
                    item = obj.dados['item']
                    self.player.inventario.append(item)
                    self.log(f"Pegou: {item['nome']}")
                    obj.ativo = False
                
                elif obj.tipo == 'fonte':
                    self.player.vida = self.player.vida_max
                    self.log("Vida restaurada!")
                    obj.ativo = False

    def checar_piso(self):
        # CORREÇÃO 3: Lógica automática para entrar no portal ao pisar
        if self.player.grid_x == self.portal.grid_x and self.player.grid_y == self.portal.grid_y:
            if self.portal.ativo:
                if self.sala_atual_idx < 4:
                    self.carregar_sala(self.sala_atual_idx + 1)
                else:
                    self.estado_atual = self.STATE_WIN
            else:
                self.log("Trancado! Mate os inimigos.")

    def update(self):
        if self.estado_atual == self.STATE_PLAY:
            self.player.update_visual()
            if self.player.cooldown_ataque > 0: self.player.cooldown_ataque -= 1
            
            inimigos_vivos = [i for i in self.inimigos if i.vivo]
            
            # Destranca portal se limpar sala
            if not inimigos_vivos and not self.portal.ativo:
                 if self.salas[self.sala_atual_idx]['tipo'] in ['combate', 'boss']:
                     self.portal.ativo = True
                     self.log("A sala abriu!")
            
            # IA Inimigos
            for ini in self.inimigos:
                ini.update_visual()
                ini.update_ia(self.player)

            if self.player.vida <= 0:
                self.estado_atual = self.STATE_GAMEOVER

            # Câmera segue player
            self.camera.update(self.player)

    def draw(self):
        self.tela.fill(CORES['bg'])
        
        if self.estado_atual == self.STATE_MENU:
            self.desenhar_texto_central("ROGUELIKE PYTHON", -50)
            self.desenhar_texto_central("Pressione [ENTER]", 50, (200,200,200))
        
        elif self.estado_atual in [self.STATE_PLAY, self.STATE_PAUSE, self.STATE_INVENTORY, self.STATE_GAMEOVER, self.STATE_WIN]:
            # 1. Desenha Mapa
            for y, linha in enumerate(self.mapa_atual):
                for x, tile in enumerate(linha):
                    if tile == 1:
                        iso_x, iso_y = (x - y) * (TILE_W / 2), (x + y) * (TILE_H / 2)
                        cam_x, cam_y = self.camera.apply(iso_x, iso_y)
                        self.assets.desenhar(self.tela, 'chao', cam_x, cam_y, CORES['chao'], 'losango')

            # 2. Desenha Entidades (Y-Sort)
            entidades = [self.player] + [i for i in self.inimigos if i.vivo] + [o for o in self.objetos if o.ativo or o.tipo=='portal']
            entidades.sort(key=lambda e: e.grid_y)

            for ent in entidades:
                cam_x, cam_y = self.camera.apply(ent.visual_x, ent.visual_y)
                
                if isinstance(ent, Player):
                    self.assets.desenhar(self.tela, 'player', cam_x, cam_y, CORES['player'], 'circulo')
                elif isinstance(ent, Inimigo):
                    cor = CORES['boss'] if ent.boss else CORES['inimigo']
                    self.assets.desenhar(self.tela, 'inimigo', cam_x, cam_y, cor, 'circulo')
                    
                    # CORREÇÃO 4: Barra de vida corrigida (proporção correta)
                    pygame.draw.rect(self.tela, (255,0,0), (cam_x-10, cam_y-30, 20, 4))
                    if ent.vida_max > 0:
                        pct = ent.vida / ent.vida_max
                        pygame.draw.rect(self.tela, (0,255,0), (cam_x-10, cam_y-30, 20*pct, 4))
                
                elif isinstance(ent, ObjetoInterativo):
                    cor = CORES[ent.tipo]
                    if ent.tipo == 'portal' and not ent.ativo: cor = (50,0,0) # Trancado
                    self.assets.desenhar(self.tela, ent.tipo, cam_x, cam_y, cor, 'retangulo')

            # 3. UI Overlay
            self.desenhar_ui()
            
            # Telas Sobrepostas
            if self.estado_atual == self.STATE_INVENTORY:
                self.desenhar_inventario()
            elif self.estado_atual == self.STATE_PAUSE:
                self.desenhar_texto_central("PAUSA", 0)
            elif self.estado_atual == self.STATE_GAMEOVER:
                self.desenhar_texto_central("GAME OVER", 0, (255,0,0))
                self.desenhar_texto_central("[R] Reiniciar", 50, (255,255,255))
            elif self.estado_atual == self.STATE_WIN:
                self.desenhar_texto_central("VITÓRIA!", 0, (255,215,0))
                self.desenhar_texto_central(f"Nível Final: {self.player.nivel}", 50)

        pygame.display.flip()

    def desenhar_ui(self):
        # HUD Inferior
        pygame.draw.rect(self.tela, (50,50,50), (0, ALTURA_TELA-40, LARGURA_TELA, 40))
        texto = f"Vida: {self.player.vida}/{self.player.vida_max}  |  Força: {self.player.forca}  |  Arma: {self.player.arma_equipada['nome']}"
        surf = self.fonte.render(texto, True, CORES['texto'])
        self.tela.blit(surf, (10, ALTURA_TELA-30))
        
        # Log
        y = 10
        for msg in reversed(self.log_msgs):
            t = self.fonte.render(msg, True, (200,200,200))
            self.tela.blit(t, (10, y))
            y += 20

    def desenhar_inventario(self):
        s = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        s.fill((0,0,0,180))
        self.tela.blit(s, (0,0))
        
        cx, cy = LARGURA_TELA//2, ALTURA_TELA//2
        rect = pygame.Rect(cx-200, cy-150, 400, 300)
        pygame.draw.rect(self.tela, (30,30,40), rect)
        pygame.draw.rect(self.tela, (200,200,200), rect, 2)
        
        self.tela.blit(self.fonte.render("INVENTÁRIO (ESC para sair)", True, CORES['texto']), (rect.x+10, rect.y+10))
        
        y_item = rect.y + 50
        if not self.player.inventario:
            self.tela.blit(self.fonte.render("Vazio...", True, (150,150,150)), (rect.x+20, y_item))
        else:
            for item in self.player.inventario:
                txt = f"- {item['nome']} (+{item['dano']} atk)"
                self.tela.blit(self.fonte.render(txt, True, CORES['texto']), (rect.x+20, y_item))
                y_item += 30

if __name__ == "__main__":
    Game().run()