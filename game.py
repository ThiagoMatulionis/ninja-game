import sys
import pygame
import random
import math

from scripts.animations import Animation
from scripts.enemy import Enemy
from scripts.player import Player
from scripts.spark import Spark
from scripts.utils import load_image, load_images, load_sfx, load_sounds
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle

LEVELS_ORDER = [
  '0_movement_intro',
  '1_the_great_climb',
  '2_enemy_intro',
  '3_fighting_through',
  '4_pacience',
  '5_showoff'
]

class Game:
  def __init__(self):
    pygame.init()
    pygame.display.set_caption('ninja game')
    
    self.screen = pygame.display.set_mode((640, 480)) ## X, Y
    self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
    self.display_2 = pygame.Surface((320, 240))
    self.clock = pygame.time.Clock()
    
    self.movement = [
      False,  ## LEFT
      False  ## RIGHT
    ]
    
    self.assets = self.create_assets()
    self.sounds = self.create_sfx()
    
    self.debug_mode = False
    self.print = False
    
    self.screenshake = 0
    self.tilemap = Tilemap(self, tile_size=16)
    self.clouds = Clouds(self.assets['clouds'], count=16)
    self.frames = 0
    self.level = 0 
    self.load_level(LEVELS_ORDER[self.level])
  

  def load_level(self, map_id):
    file_path = './data/created_maps/'
    self.tilemap.load(file_path, str(map_id) + '.json')
    
    ## Tree particles init
    self.leaf_spawners = []
    for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
      leaf_reac = pygame.Rect(tree['pos'][0] + 4, tree['pos'][1] + 4, 23, 13)
      self.leaf_spawners.append(leaf_reac)
    ##
    
    
    ## Enemy spawners
    self.enemies: list[Enemy] = []
    player_spawn_coord = (0, 0)
    for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2)], keep=False):
      if spawner['variant'] == 0:
        player_spawn_coord = spawner['pos']
      elif spawner['variant'] == 1:
        self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
      elif spawner['variant'] == 2:
        self.enemies.append(Enemy(self, spawner['pos'], (8, 15), True))
    ##
    
    self.player = Player(self, player_spawn_coord)
    self.scroll = self.create_camera()
    
    self.particles: list[Particle] = []
    self.projectiles = []
    self.sparks = []
    self.transition = -30

  def run(self):
    pygame.mixer.music.load('data/music.wav')
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
    
    self.sounds['ambience'].play(-1)
    
    while True:
      self.screenshake = max(0, self.screenshake - 1)
      
      if self.transition < 0:
        self.transition += 1
      
      if not len(self.enemies):
        self.transition += 1
        if self.transition > 60:
          self.level = (self.level + 1) % len(LEVELS_ORDER)
          self.load_level(LEVELS_ORDER[self.level])
      
      if self.player.dead:
        self.player.dead += 1
        if self.player.dead >= 30:
          self.transition = min(30, self.transition + 1)
        
        if self.player.dead > 60:
          self.load_level(LEVELS_ORDER[self.level])
      
      
      self.frames = (self.frames + 1) % 61
      self.set_background()
      self.set_camera_coord()
      render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
      
      self.clouds.update()
      self.clouds.render(self.display_2, offset=render_scroll)
      
      self.tilemap.render(self.display, offset = render_scroll)
      
      for enemy in self.enemies:
        kill = enemy.update(self.tilemap, (0,0))
        enemy.render(self.display, offset=render_scroll)
        if kill:
          self.enemies.remove(enemy)
      
      
      if not self.player.dead:
        self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
        self.player.render(self.display, offset = render_scroll)
      
      
      ## TODO: Refactor projectile handler
      ## TODO: Create Projectile class
      for projectile in self.projectiles.copy():
        projectile['location'][0] = projectile['location'][0] + projectile['velocity']
        projectile['timer'] = max(0, projectile['timer'] - 1)
        img = self.assets['projectile']
        self.display.blit(img, (projectile['location'][0] - img.get_width() / 2 - render_scroll[0], projectile['location'][1] - img.get_height() / 2 - render_scroll[1]))
        
        if self.tilemap.is_solid_block(projectile['location']):
          self.projectiles.remove(projectile)
          for i in range(4):
            pos = projectile['location']
            angle = random.random() - 0.5 + (math.pi if projectile['velocity'] > 0 else 0)
            speed = random.random() + 2
            
            self.sparks.append(Spark(pos, angle, speed))
        elif projectile['timer'] < 0:
          self.projectiles.remove(projectile)
        elif not self.player.dead and not self.player.dash_info['active_frames']:
          if self.player.rect().collidepoint(projectile['location']):
            self.projectiles.remove(projectile)
            self.player.death()
      ####
      
      
      display_mask = pygame.mask.from_surface(self.display)
      display_sillhouette = display_mask.to_surface(setcolor = (0, 0, 0, 255), unsetcolor = (0, 0, 0, 0))
      
      for offset in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
        self.display_2.blit(display_sillhouette, offset)
      
      for spark in self.sparks.copy():
        kill = spark.update()
        spark.render(self.display, render_scroll)
        if kill:
          self.sparks.remove(spark)
      
      ## TODO: Refactor particles handler
      ## Particles
      for rect in self.leaf_spawners:
        if random.random() * 49999 < rect.width * rect.height:
          pos_x = rect.x + random.random() * rect.width
          pos_y = rect.y + random.random() * rect.height
          velocity = [ -0.1, 0.3 ]
          self.particles.append(Particle(self, 'leaf', (pos_x, pos_y), velocity, frame=random.randint(0, 20)))
      
      for particles in self.particles.copy():
        kill = particles.update()
        particles.render(self.display, offset=render_scroll)
        
        if particles.p_type == 'leaf':
          ## Moving particle left to right
          particles.pos[0] += math.sin(particles.animation.frame * 0.035) * 0.3
        
        if kill:
          self.particles.remove(particles)
      ####
      
      self.handle_user_input()
      
      if self.transition:
        transition_surf = pygame.Surface(self.display.get_size())
        pygame.draw.circle(transition_surf, (255, 255 , 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
        transition_surf.set_colorkey((255, 255, 255))
        self.display.blit(transition_surf, (0, 0))
      
      if self.debug_mode:
        text = self.my_font.render('Debug mode', False, (0, 0, 0))
        self.display_2.blit(text, (10, self.display_2.get_height() - 10))
      self.display_2.blit(self.display, (0, 0))
      screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
      self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
      pygame.display.update()
      self.clock.tick(60)
  
  def set_background(self):
    self.display.fill((0, 0, 0, 0))
    self.display_2.blit(self.assets['background'], (0,0))
    # self.screen.blit(self.display, (0, 0))

  def set_camera_coord(self):
    # REMEMBER: when setting camera coordinate, 
    # you should aim for the top left corner of the screen
    
    player_rect = self.player.rect()
    display = self.display
    
    # [camera_x_coord +] = camera coordinates will be the same value as before (camera_x_coord)
    # [player_rect.centerx - half_x_screen] = going into the direction of the player (up half screen)
    # [- camera_x_coord] = excludes the coord of camera before division
    # [/ 30] = smoothens camera to go slowly when close to target and faster when player is far away
    
    # X axis
    camera_x_coord = self.scroll[0]
    half_x_screen = display.get_width() / 2
    self.scroll[0] = camera_x_coord + ((player_rect.centerx - half_x_screen - camera_x_coord) / 30)
    
    # Y axis
    camera_y_coord = self.scroll[1]
    half_y_screen = display.get_height() / 2
    self.scroll[1] = camera_y_coord + (player_rect.centery - half_y_screen - camera_y_coord) / 30
    
    # if self.frames == 1:
    #   print('camera: ('+ str(self.scroll[0]) + ',' + str(self.scroll[1]) + ')')
  
  def handle_user_input(self):
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
      
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_F3:
          pygame.font.init()
          self.my_font = pygame.font.SysFont('Arial', 8)
          self.debug_mode = not self.debug_mode
        if event.key == pygame.K_F10:
          self.print = True
        elif event.key == pygame.K_w:
          if self.player.jump():
            self.sounds['jump'].play()
        elif event.key == pygame.K_a:
            self.movement[0]= True
        elif event.key == pygame.K_d:
          self.movement[1]= True
        elif event.key == pygame.K_LSHIFT:
          self.player.dash()
        
      if event.type == pygame.KEYUP:
        if event.key == pygame.K_a:
          self.movement[0] = False
        elif event.key == pygame.K_d:
          self.movement[1] = False
        if event.key == pygame.K_F10:
          self.print = False

  def create_camera(self):
    # REMEMBER: when setting camera coordinate, 
    # you should aim for the top left corner of the screen
    
    # creating camera coord to be centered on the player
    player_rect = self.player.rect()
    display = self.display
    scroll = [0, 0]
    
    # X axis
    camera_x_coord = scroll[0]
    half_x_screen = display.get_width() / 2
    scroll[0] = camera_x_coord + (player_rect.centerx - half_x_screen - camera_x_coord)
    
    # Y axis
    camera_y_coord = scroll[1]
    half_y_screen = display.get_height() / 2
    scroll[1] = camera_y_coord + (player_rect.centery - half_y_screen - camera_y_coord)

    return scroll

  def create_assets(self):
    return {
      'player': load_image('entities/player.png'),
      'decor': load_images('tiles/decor'),
      'large_decor': load_images('tiles/large_decor'),
      'grass': load_images('tiles/grass'),
      'stone': load_images('tiles/stone'),
      'background': load_image('background.png'),
      'clouds': load_images('clouds'),
      'gun': load_image('gun.png'),
      'projectile': load_image('projectile.png'),
      'harmless_enemy': {
        'idle': Animation(load_images('entities/harmless_enemy/idle'), img_dur=6),
        'run': Animation(load_images('entities/harmless_enemy/run'), img_dur=4),
      },
      'enemy': {
        'idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
        'run': Animation(load_images('entities/enemy/run'), img_dur=4),
      },
      'player': {
        'idle': Animation(load_images('entities/player/idle'), img_dur = 6, loop = True),
        'run': Animation(load_images('entities/player/run'), img_dur = 4, loop = True),
        'jump': Animation(load_images('entities/player/jump')),
        'slide': Animation(load_images('entities/player/slide')),
        'wall_slide': Animation(load_images('entities/player/wall_slide')),
      },
      'particles': {
        'leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
        'dash': Animation(load_images('particles/particle'), img_dur=6, loop=False)
      }
    }

  def create_sfx(self):
    return {
      'jump': load_sfx('jump.wav', 0.1),
      'dash': load_sfx('dash.wav', 0.1),
      'hurts': load_sounds('hurts', 0.3),
      'hits': load_sounds('hits', 0.22),
      'shoot': load_sfx('shoot.wav', 0.4),
      'ambience': load_sfx('ambience.wav', 0.2),
    }

Game().run()