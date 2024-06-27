import pygame

# from game import Game
from scripts.tilemap import Tilemap

class PhysicsEntity:
  def __init__(self, game, e_type, pos, size):
    self.game = game
    self.type = e_type
    self.pos = list(pos)
    self.size = size
    self.velocity = [0, 0]
    self.colisions = {'up': False, 'down': False, 'left': False, 'right': False}
    
    self.action = ''
    self.flip = False
    self.set_action('idle')
    
    self.last_movement = [0, 0]
    
    # Because not all images have the same pixels quantity
    # You want to render those different images offset
    # of the original coordenates
    self.anim_offset = (-3, -3)
    
  def rect(self):
    return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
  
  def update(self, tilemap: Tilemap, movement = (0, 0), debug=False):
    self.colisions = {'up': False, 'down': False, 'left': False, 'right': False}
    entity_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
    
    last_pos = list(self.pos)
    
    ## HORIZONTAL COLLISION
    self.pos[0] = self.pos[0] + entity_movement[0]
    entity_collision = self.rect()
    if debug: print('Collision(X): ' + str(entity_collision.x))
    for tile in tilemap.physics_rect_around(self.pos):
      if entity_collision.colliderect(tile):
        if entity_movement[0] > 0: # Going right
          entity_collision.right = tile.left
          self.colisions['right'] = True
        elif entity_movement[0] < 0: # Going left
          entity_collision.left = tile.right
          self.colisions['left'] = True
        self.pos[0] = entity_collision.x
        
        if debug:
          print('Detected horizontal colision to tile: ' + str(tilemap.tilemap[str(tile.left // tilemap.tile_size) + ';' + str(tile.top // tilemap.tile_size)]))
          print('Moving player x pos to ' + str(entity_collision.x))
    
    ## VERTICAL COLLISION
    self.pos[1] = self.pos[1] + entity_movement[1]
    entity_collision = self.rect()
    for tile in tilemap.physics_rect_around(self.pos):
      if entity_collision.colliderect(tile):
        if entity_movement[1] > 0: # Going down
          entity_collision.bottom = tile.top
          self.colisions['down'] = True
        if entity_movement[1] < 0: # Going up
          entity_collision.top = tile.bottom
          self.colisions['up'] = True
        self.pos[1] = entity_collision.y
    
    if movement[0] > 0:
      self.flip = False
    if movement[0] < 0:
      self.flip = True
    
    self.last_movement = movement
    self.velocity[1] = min(5, self.velocity[1] + 0.1)
    
    if self.colisions['down'] or self.colisions['up']:
      self.velocity[1] = 0
    
    self.animation.update()
    
    if debug:
      self.print_position(last_pos, entity_movement)
      print('++++++++++++++++++++++++++++++')
    
  def set_action(self, action):
    if action != self.action:
      self.action = action
      self.animation = self.game.assets[self.type][self.action].copy()
    
  def render(self, surf, offset = (0, 0)):
    surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
  
  def print_position(self, last_position, entity_movement):
    e_rect = self.rect()
    print(str(self.type) + ' position: [' + str(self.pos[0]) + ',' + str(self.pos[1]) + '] ( Changed ' + '[' + str(self.pos[0] - last_position[0]) + ',' + str(self.pos[1] - last_position[1]) + '] )')
    print(str(self.type) + ' movement: [' + str(entity_movement[0]) + ',' + str(entity_movement[1]) + ']')
    print(str(self.type) + ' size: ' + str(e_rect.size))