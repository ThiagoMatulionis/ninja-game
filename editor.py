import sys
import pygame

from scripts.utils import Mouse_button, load_images
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0

class Editor:
  def __init__(self):
    pygame.init()
    pygame.display.set_caption('ninja game EDITOR')
    
    self.screen = pygame.display.set_mode((640, 480)) ## X, Y
    self.display = pygame.Surface((320, 240))
    
    self.clock = pygame.time.Clock()
    
    pygame.font.init()
    self.my_font = pygame.font.SysFont('Comic Sans MS', 10)
    
    self.assets = {
      'grass': load_images('tiles/grass'),
      'stone': load_images('tiles/stone'),
      'decor': load_images('tiles/decor'),
      'large_decor': load_images('tiles/large_decor'),
      'spawners': load_images('tiles/spawners'),
    }
    
    self.movement = [
      False,  ## LEFT
      False,  ## RIGHT
      False, ## UP
      False, ## DOWN
    ]
    self.tilemap = Tilemap(self, tile_size=16)
    
    self.map_name = ''
    try:
      file_path = './data/created_maps/'
      load_map = 'movement_intro_v2'
      self.tilemap.load(file_path, load_map + '.json')
      
      self.map_name = load_map + '.json'
    except FileNotFoundError:
      pass
    
    
    self.scroll = [0, 0]
    
    self.tile_list = list(self.assets)
    self.tile_group = 0
    self.tile_variant = 0
    
    self.on_grid = True
    
    self.mpos = (0, 0)
    self.clicking = False
    self.right_clicking = False
    self.pressing_shift = False
    self.pressing_ctrl = False

  def handle_camera_movement(self):
    self.scroll[0] = self.scroll[0] + (self.movement[1] - self.movement[0]) * 3
    self.scroll[1] = self.scroll[1] + (self.movement[3] - self.movement[2]) * 3
    return (int(self.scroll[0]), int(self.scroll[1]))

  def get_img_pos(self):
    if self.on_grid:
      return  (int((self.mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((self.mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
    else:
      return self.mpos

  def handle_selected_img_preview(self, img,):
    selected_img = img.copy()
    selected_img.set_alpha(50)
    
    self.display.blit(selected_img, (5, 5))

  def handle_preview_image(self, img):
    preview_image = img.copy()
    preview_image.set_alpha(100)
    
    img_pos = self.get_img_pos()
    
    if self.on_grid:
      text = self.my_font.render(str(img_pos), False, (255, 255, 255))
      text.set_alpha(100)
      self.display.blit(text, (20, 10))
      self.display.blit(preview_image, (img_pos[0] * self.tilemap.tile_size - self.scroll[0], img_pos[1] * self.tilemap.tile_size - self.scroll[1]))
    else:
      self.display.blit(preview_image, img_pos)

  def handle_one_click_event(self):
    self.handle_offgrid_tile_placing()

  def handle_continuously_click_event(self):
    self.handle_ongrid_tile_placing()
    self.handle_tile_deletion()

  def handle_offgrid_tile_placing(self):
    tile_content = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': self.get_img_pos()}
    
    ## OffGrid tiles
    if self.clicking and not self.on_grid:
        tile_content['pos'] = (tile_content['pos'][0] + self.scroll[0], tile_content['pos'][1] + self.scroll[1])
        self.tilemap.offgrid_tiles.append(tile_content)

  def handle_ongrid_tile_placing(self):
    img_pos = self.get_img_pos()
    if self.clicking and self.on_grid:
        self.tilemap.tilemap[str(img_pos[0]) + ';' + str(img_pos[1])] = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': img_pos}

  def handle_tile_deletion(self):
    img_on_grid_pos = (int((self.mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((self.mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
    
    if self.right_clicking:
      ## OnGrid deletion
      tile_loc = str(img_on_grid_pos[0]) + ';' + str(img_on_grid_pos[1])
      if tile_loc in self.tilemap.tilemap:
        del self.tilemap.tilemap[tile_loc]
      
      ## OffGrid deletion
      for tile in self.tilemap.offgrid_tiles:
        img = self.assets[tile['type']][tile['variant']]
        img_hitbox = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], img.get_width(), img.get_height())
        
        if img_hitbox.collidepoint(self.mpos):
          self.tilemap.offgrid_tiles.remove(tile)

  def handle_user_input(self):
    for event in pygame.event.get():
      # print(str(event.type) + ': '+ str(event.key))
      
      match event.type:
        case pygame.QUIT:
          pygame.quit()
          sys.exit()
        case pygame.MOUSEBUTTONDOWN:
          self.handle_on_mouse_down_event(event)
        case pygame.MOUSEBUTTONUP:
          self.handle_on_mouse_up_event(event)
        case pygame.KEYDOWN:
          self.handle_on_key_down_event(event)
        case pygame.KEYUP:
          self.handle_on_key_up_event(event)

  def handle_on_mouse_down_event(self, event):
    
    if event.button == Mouse_button.L_CLICK.value:
      self.clicking = True
      self.handle_one_click_event()
      
    elif event.button == Mouse_button.R_CLICK.value:
      self.right_clicking = True
    elif self.pressing_shift:
      if event.button == Mouse_button.SCROLL_UP.value:
        self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
      if event.button == Mouse_button.SCROLL_DOWN.value:
        self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
    else:
      if event.button == Mouse_button.SCROLL_UP.value:
        self.tile_group = (self.tile_group - 1) % len(self.tile_list)
        self.tile_variant = 0
      if event.button == Mouse_button.SCROLL_DOWN.value:
        self.tile_group = (self.tile_group + 1) % len(self.tile_list)
        self.tile_variant = 0

  def handle_on_mouse_up_event(self, event):
    match event.button:
      case Mouse_button.L_CLICK.value:
        self.clicking = False
      case Mouse_button.R_CLICK.value:
        self.right_clicking = False

  def handle_on_key_down_event(self, event):
    mods = pygame.key.get_mods()
    
    if event.key == pygame.K_LSHIFT:
      self.pressing_shift = True
    if mods & pygame.KMOD_CTRL:
      self.pressing_ctrl = True
    if event.key == pygame.K_a:
      self.movement[0]= True
    if event.key == pygame.K_d:
      self.movement[1]= True
    if event.key == pygame.K_w:
      self.movement[2] = True
    if event.key == pygame.K_s:
      if self.pressing_ctrl:
        self.tilemap.save('./data/created_maps/')
      else:
        self.movement[3]= True
    if event.key == pygame.K_g:
      self.on_grid = not self.on_grid
    if event.key == pygame.K_t:
      self.tilemap.autotile()

  def handle_on_key_up_event(self, event):
    mods = pygame.key.get_mods()
    
    if event.key == pygame.K_LSHIFT:
      self.pressing_shift = False
    if not mods & self.pressing_ctrl:
      self.pressing_ctrl = False
    if event.key == pygame.K_a:
      self.movement[0] = False
    if event.key == pygame.K_d:
      self.movement[1] = False
    if event.key == pygame.K_w:
      self.movement[2] = False
    if event.key == pygame.K_s:
      self.movement[3]= False

  def run(self):
    while True:
      self.setBackground()
      render_scroll = self.handle_camera_movement()
      self.tilemap.render(self.display, offset=render_scroll)
      
      current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
      
      ## Render scale cause display is grown to be size of screen 
      mpos = pygame.mouse.get_pos()
      self.mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
      
      
      self.handle_preview_image(current_tile_img)
      self.handle_continuously_click_event()
      self.handle_selected_img_preview(current_tile_img)
      
      self.handle_user_input()

      self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
      pygame.display.update()
      self.clock.tick(60)

  def setBackground(self):
    self.display.fill((0, 0, 0))
  

Editor().run()