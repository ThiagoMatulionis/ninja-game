import math
import random

import pygame
from scripts.entities import PhysicsEntity
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.tilemap import Tilemap

## TODO: Enemy reaction time

class Enemy(PhysicsEntity):
  def __init__(self, game, pos, size, harmless = False):
    super().__init__(game, 'enemy' if not harmless else 'harmless_enemy', pos, size)
    self.walking = 0
    self.shot_cooldown = 30
    self.harmless = harmless
    
  def update(self, tilemap: Tilemap, movement=(0,0)):
    if not self.harmless: 
      self.shooting_handler()
    
    if self.walking:
      if self.colisions['right'] or self.colisions['left']:
        self.flip = not self.flip
      else:
        coord = (self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)
        
        if not self.game.tilemap.is_solid_block(coord):
          self.flip = not self.flip
      
      movement = (movement[0] -0.5 if self.flip else 0.5, movement[1])
      self.walking = max(0, self.walking - 1)
    elif random.random() < 0.01:
        self.walking = random.randint(30, 90)
    
    super().update(tilemap, movement=movement)
    
    if movement[0] != 0:
      self.set_action('run')
    else:
      self.set_action('idle')
    
    if self.game.player.dash_info['active_frames'] > 2:
      if self.rect().colliderect(self.game.player.rect()):
        self.death_sound()
        for i in range(30):
          pos = self.rect().center
          angle = random.random() * math.pi * 2
          speed = random.random() + 2
          self.game.sparks.append(Spark(pos, angle, speed))
          
          speed = random.random() * 5
          p_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
          self.game.particles.append(Particle(self.game, 'dash', self.rect().center, p_velocity, random.randint(0, 7)))
        self.game.sparks.append(Spark(self.rect().center, 0, random.random() + 5))
        self.game.sparks.append(Spark(self.rect().center, math.pi, random.random() + 5))
        self.game.screenshake = max(16, self.game.screenshake)
        return True
    
    return False
  
  def render(self, surf, offset=[0,0]):
    super().render(surf, offset)
    
    if not self.harmless:
      self.draw_gun(surf, offset)
  
  def draw_gun(self, surf: pygame.Surface, offset):
    gun_offset = (-4 - self.game.assets['gun'].get_width()) if self.flip else 4
    
    gun_x_axis = self.rect().centerx + gun_offset - offset[0]
    gun_y_axis = self.rect().centery - offset[1]
    
    surf.blit(pygame.transform.flip(self.game.assets['gun'], self.flip, False), (gun_x_axis, gun_y_axis))
  
  def shooting_handler(self):
    distance_between_player = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
    self.shot_cooldown = max(0, self.shot_cooldown - 1)
    
    if not self.shot_cooldown:
      if abs(distance_between_player[1]) < 16 and abs(distance_between_player[0]) < 100:
        if random.random() * 1000 > 985 and distance_between_player[0] != 0:
          if self.flip and distance_between_player[0] < 0:
            self.game.projectiles.append({
              'location': [self.rect().centerx - 7, self.rect().centery], 
              'velocity': -1.5,
              'timer': 180
            })
            
            self.shot_cooldown = 120
            self.game.sounds['shoot'].play()
            
            for i in range(4):
              pos = self.game.projectiles[-1]['location']
              angle = random.random() - 0.5 + math.pi
              speed = random.random() + 2
              self.game.sparks.append(Spark(pos, angle, speed))
            
          elif not self.flip and distance_between_player[0] > 0:
            self.game.projectiles.append({
              'location': [self.rect().centerx + 7, self.rect().centery], 
              'velocity': 1.5,
              'timer': 180
            })
            self.shot_cooldown = 120
            self.game.sounds['shoot'].play()

            for i in range(4):
              pos = self.game.projectiles[-1]['location']
              angle = random.random() - 0.5
              # angle = - random.random() + 0.5 - math.pi ## CHECK again later
              speed = random.random() + 2
              
              self.game.sparks.append(Spark(pos, angle, speed))

  def death_sound(self):
    lista: list[pygame.mixer.Sound] = self.game.sounds['hits']
    i = int(random.random() * len(lista))
    lista[i].play()
  
