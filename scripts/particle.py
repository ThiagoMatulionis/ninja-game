import pygame


class Particle:
  def __init__(self, game, particle_type, pos, velocity=[0,0], frame=0):
    self.game = game
    self.p_type = particle_type
    self.pos = list(pos)
    self.velocity = list(velocity)
    self.animation = self.game.assets['particles'][self.p_type].copy()
    self.animation.frame = frame

  def update(self):
    kill = False
    if self.animation.done:
      kill = True
    
    self.pos[0] = self.pos[0] + self.velocity[0]
    self.pos[1] = self.pos[1] + self.velocity[1]
    self.animation.update()
    
    return kill
  
  def render(self, surf, offset=(0,0)):
    img= self.animation.img()
    
    ## Getting image's center and applying offset
    img_x_center = self.pos[0] - offset[0] - img.get_width() // 2 
    img_y_center = self.pos[1] - offset[1] - img.get_height() // 2
    
    surf.blit(img, (img_x_center, img_y_center))