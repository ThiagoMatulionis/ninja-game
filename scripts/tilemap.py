import json
import pygame
from dict_hash import dict_hash

NEIGHBOR_OFFSETS = [
  (-1,  1),  (0,  1), (1,  1),   ## DOWN_LEFT, DOWN,   DOWN_RIGHT
  (-1,  0),  (0,  0), (1,  0),  ## LEFT,      CENTER, RIGHT
  (-1, -1),  (0, -1), (1, -1),  ## UP_LEFT,   UP,     UP_RIGHT
]

AUTOTILE_TYPES = { 'grass', 'stone' }
AUTOTILE_MAP = {
  tuple(sorted([(0, 1), (1, 0)])): 0,
  tuple(sorted([(-1, 0), (0, 1), (1, 0)])): 1,
  tuple(sorted([(-1, 0), (0, 1)])): 2,
  tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
  tuple(sorted([(-1, 0), (0, -1)])): 4,
  tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
  tuple(sorted([(0, -1), (1, 0)])): 6,
  tuple(sorted([(0, -1), (0, 1), (1, 0)])): 7,
  tuple(sorted([(-1, 0), (0, -1), (0, 1), (1, 0)])): 8,
}

PHYSICS_TILES = { 'grass', 'stone' }

class Tilemap:
  def __init__(self, game, tile_size = 16):
    self.game = game
    self.tile_size = tile_size
    self.tilemap = {}
    self.offgrid_tiles = []

  def tiles_around(self, pos): 
    arround_tiles = []
    tile_pos = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
    
    for neighboor_offset in NEIGHBOR_OFFSETS:
      offset_location = str(tile_pos[0] + neighboor_offset[0]) + ';' + str(tile_pos[1] + neighboor_offset[1])
      if offset_location in self.tilemap:
        arround_tiles.append(self.tilemap[offset_location])
    
    return arround_tiles

  def save(self, path):
    file_content = {'tilemap': self.tilemap, 'offgrid': self.offgrid_tiles, 'tile_size': self.tile_size}
    
    if len(self.game.map_name) > 0:
      file_name = self.game.map_name
    else:
      file_name = str(dict_hash(file_content)) + '.json'
    
    print('====== Saving '+ file_name + ' into '+ path + ' =======')
    
    file_connection = open(path + file_name, 'w') # Writing
    
    json.dump(file_content, file_connection)
    
    file_connection.close()

  def load(self, path, file_name):
    file_connection = open(path + file_name, 'r') # Reading
    
    data = json.load(file_connection)
    
    file_connection.close()
    
    
    self.tilemap = data['tilemap']
    self.offgrid_tiles = data['offgrid']
    self.tile_size = data['tile_size']
  
  def autotile(self):
    for coord in self.tilemap:
      tile = self.tilemap[coord]
      if tile['type'] in AUTOTILE_TYPES:
        neighbors = set()
        for shift in [(-1, 0), (0, -1), (0, 1), (1, 0)]:
          check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
          if check_loc in self.tilemap:
            tile_shift = self.tilemap[check_loc]
            if(tile_shift['type'] == tile['type']):
              neighbors.add(shift)
        neighbors = tuple(sorted(neighbors))
        if neighbors in AUTOTILE_MAP:
          tile['variant'] = AUTOTILE_MAP[neighbors]

  def extract(self, id_pairs, keep = False):
    matches = []
    for tile in self.offgrid_tiles.copy():
      if (tile['type'], tile['variant']) in id_pairs:
        matches.append(tile.copy())
        if not keep:
          self.offgrid_tiles.remove(tile)
    
    to_be_deleted = []
    for loc in self.tilemap:
      tile = self.tilemap[loc]
      if (tile['type'], tile['variant']) in id_pairs:
        matches.append(tile.copy())
        matches[-1]['pos'] = matches[-1]['pos'].copy()
        matches[-1]['pos'][0] = matches[-1]['pos'][0] * self.tile_size
        matches[-1]['pos'][1] = matches[-1]['pos'][1] * self.tile_size
        if not keep:
          to_be_deleted.append(loc)
    
    for loc in to_be_deleted:
      del self.tilemap[loc]
    
    return matches
  
  def physics_rect_around(self, pos):
    rects:list[pygame.Rect] = []
    for tile in self.tiles_around(pos):
      if tile['type'] in PHYSICS_TILES:
          rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
    
    return rects
  
  def render(self, surf, offset = (0, 0)):
    for tile in self.offgrid_tiles:
      surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))
    
    # Rendering only tiles on camera
    # offset is in pixels, when divided by tile_size we get coord of tile in the top left corner 
    # Then we get coord of the top right corner and move it right 1 unit
    for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
      for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
        loc = str(x) + ';' + str(y)
        if loc in self.tilemap:
          tile = self.tilemap[loc]
          surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))
  
  def is_solid_block(self, pos):
    tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
    
    if tile_loc in self.tilemap:
      return self.tilemap[tile_loc]['type'] in PHYSICS_TILES