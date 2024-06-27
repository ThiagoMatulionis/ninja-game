import math
import random

import pygame
from scripts.entities import PhysicsEntity
from scripts.particle import Particle
from scripts.spark import Spark

DASH_COOLDOWN_FRAMES = 50
DASH_ACTIVE_FRAMES = 10
PLAYER_SIZE = (8, 15)
DASH_SIZE = (8, 15)

class Player(PhysicsEntity):
  
  def __init__(self, game, pos):
    super().__init__(game, 'player', pos, PLAYER_SIZE)
    self.air_time = 0
    self.jumps = 1
    self.wall_sliding = False
    self.dead = 0
    self.dash_info = {
      'direction': 0,
      'ratio': 0,
      'active_frames': 0,
      'cooldown_frames': 0,
    }
    
  def update(self, tilemap, movement = (0, 0)):
    debug = self.game.debug_mode and self.game.print
    
    super().update(tilemap, movement=movement, debug=debug)
    
    self.handle_dash_physics(tilemap)
    
    self.air_time = self.air_time + 1
    if self.colisions['down']:
      self.air_time = 0
      self.jumps = 1
      
    if self.air_time > 160:
      self.death()
    
    self.wall_sliding = False
    if self.isWallSliding():
      self.wall_sliding = True
      self.air_time = 5
      self.velocity[1] = min(self.velocity[1], 0.5)
      self.set_action('wall_slide')
      self.flip = self.colisions['left']
    elif self.isInTheAir():
      self.set_action('jump')
    elif movement[0] != 0:
      self.set_action('run')
    else:
      self.set_action('idle')
      
    if self.velocity[0] > 0:
      self.velocity[0] = max(self.velocity[0] - 0.1, 0)
    else:
      self.velocity[0] = min(self.velocity[0] + 0.1, 0)
  
  def dash(self):
    if not self.dead and not self.dash_info['direction'] and not self.dash_info['cooldown_frames']:
      if self.flip: self.dash_info['direction'] = -1 # GOING LEFT
      else: self.dash_info['direction'] = 1 # GOING RIGHT
      
      if self.action == 'jump':
        self.dash_info['ratio'] = 5
      elif self.action == 'idle' or self.action == 'run':
        self.dash_info['ratio'] = 6
      
      self.size = DASH_SIZE
      self.game.sounds['dash'].play()
      self.dash_particle_burst()
  
  def jump(self):
    if self.wall_sliding:
      if self.flip and self.last_movement[0] < 0:
        self.velocity[0] = 2
        self.velocity[1] = -2.0
        self.air_time = 5
        # Consuming a jump but capping at 0
        self.jumps = max(0, self.jumps - 1)
        return True
      elif not self.flip and self.last_movement[0] > 0:
        self.velocity[0] = -2
        self.velocity[1] = -2.0
        self.air_time = 5
        # Consuming a jump but capping at 0
        self.jumps = max(0, self.jumps - 1)
        return True
    elif self.jumps:
      self.velocity[1] = -2.5
      self.jumps -= 1
      self.air_time = 5
      return True
  
  def isInTheAir(self):
    return self.air_time > 4
  
  def isWallSliding(self):
    return (self.colisions['right'] or self.colisions['left']) and self.isInTheAir()

  def handle_dash_physics(self, tilemap):
    if self.dash_info['cooldown_frames']:
      self.dash_info['cooldown_frames'] = max(self.dash_info['cooldown_frames'] - 1, 0)
    elif self.dash_info['active_frames']:
      self.dash_info['active_frames'] = max(self.dash_info['active_frames'] - 1, 0)
      self.velocity[0] = self.dash_info['direction'] * self.dash_info['ratio']
      
      if not self.game.debug_mode:
        p_velocity = [self.dash_info['direction'] * random.random() * 3, 0]
        dash_particle = Particle(self.game, 'dash', self.rect().center, p_velocity, random.randint(0, 7))
        self.game.particles.append(dash_particle)
      
      if self.dash_info['active_frames'] == 0: # Resetting  dash
        self.dash_particle_burst()
        self.velocity[0] = 0
        self.dash_info['cooldown_frames'] = DASH_COOLDOWN_FRAMES
        self.dash_info['direction'] = 0
        self.dash_info['ratio'] = 0
        self.size = PLAYER_SIZE
        if self.game.debug_mode: 
          print('Dash ended')
    elif self.dash_info['direction']:
      self.dash_info['active_frames'] = DASH_ACTIVE_FRAMES
      if self.game.debug_mode:
        print('Dash started')
  
  def render(self, surf, offset=(0,0)):
    if not self.dash_info['direction']:
      super().render(surf, offset)
    
    if self.game.debug_mode:
      pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(self.pos[0] - offset[0], self.pos[1] - offset[1], self.size[0], self.size[1]))
    
  
  def dash_particle_burst(self):
    if self.game.debug_mode:
      pass
    # Burst Particles
    for i in range(20):
      angle = random.random() * math.pi * 2
      speed = random.random() * 0.5 + 0.5
      p_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
      dash_particle = Particle(self.game, 'dash', self.rect().center, p_velocity, random.randint(0, 7))
      self.game.particles.append(dash_particle)
  
  def death(self):
    self.game.screenshake = max(16, self.game.screenshake)
    self.dead = 1
    self.death_sound()
    
    for i in range(30):
      pos = self.rect().center
      angle = random.random() * math.pi * 2
      speed = random.random() + 2
      self.game.sparks.append(Spark(pos, angle, speed))
      
      speed = random.random() * 5
      p_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
      self.game.particles.append(Particle(self.game, 'dash', self.rect().center, p_velocity, random.randint(0, 7)))
  
  def death_sound(self):
    sounds: list[pygame.mixer.Sound] = self.game.sounds['hurts']
    i = int(random.random() * len(sounds))
    
    sounds[i].play()
  