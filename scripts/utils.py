from enum import Enum
import pygame
import os

BASE_IMG_PATH = 'data/images/'
BASE_SFX_PATH = 'data/sfx/'

def load_image(path):
  img = pygame.image.load(BASE_IMG_PATH + path).convert()
  img.set_colorkey((0, 0, 0))
  return img

def load_images(path):
  images = []
  for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
    images.append(load_image(path + '/' + img_name))
  
  return images

def load_sfx(name, vol):
  sound =  pygame.mixer.Sound(BASE_SFX_PATH + name)
  sound.set_volume(vol)
  return sound

def load_sounds(folder, vol):
  sounds = []
  
  for sfx in sorted(os.listdir(BASE_SFX_PATH + folder)):
    sound = load_sfx(folder + '/' + sfx, vol)
    sounds.append(sound)
  
  return sounds

class Mouse_button(Enum):
  L_CLICK = 1
  M_CLICK = 2
  R_CLICK = 3
  SCROLL_UP = 4
  SCROLL_DOWN = 5