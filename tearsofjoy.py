import collections
import os
from types import SimpleNamespace

import pygame
import pygame.freetype

from browser import browser
from proctrl import proctrl

#from joycontrol import logging_default as log, utils
#from joycontrol.controller import Controller

os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV'      , '/dev/fb0')
#os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
#os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

Config = collections.namedtuple("Config", ["bins_root", "font_size", "line_spacing"])
        
class tearsofjoy:
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config

        self.font = pygame.freetype.SysFont(pygame.font.get_default_font(), self.config.font_size)

        bins = sorted((SimpleNamespace(path=path, name=fn) for path, dirs, files in os.walk(self.config.bins_root) for fn in files if os.path.splitext(fn)[1].lower() == ".bin"), key=lambda b: b.name)
        self.browser = browser(
            bins, self.screen, self.config, self.font, self.select_nfc,
            filter_item=lambda b, f: f.lower() in b.name.lower(),
            show_item=lambda b: b.name
        )
        self.proctrl = proctrl(self.screen, self.config, self.font, self.browse_nfc)

        self.ctrl = self.proctrl
        
    def browse_nfc(self):
        #self.browser.reset()
        self.ctrl = self.browser
        pygame.key.set_repeat(200, 40)
        
    def select_nfc(self, nfc):
        self.proctrl.reset()
        self.proctrl.select_nfc(nfc)
        self.ctrl = self.proctrl
        pygame.key.set_repeat()
        
    def interact(self, event):
        return self.ctrl.interact(event)
        
    def draw(self):
        self.ctrl.draw()

def main():
    # check if root
    if not os.geteuid() == 0:
        raise PermissionError('Script must be run as root!')
        
    pygame.init()

    pygame.mouse.set_visible(False)

    the_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    done = False

    tears_of_joy = tearsofjoy(the_screen, Config(
        bins_root="/home/pi/joycontrol/acnh",
        font_size=32,
        line_spacing=8
    ))
        
    while not done:
        for event in pygame.event.get():
            print(event)
            
            is_quit = event.type == pygame.QUIT
        
            if is_quit:
                done = done or True
            else:
                done = done or tears_of_joy.interact(event)
                
        tears_of_joy.draw()
        pygame.display.flip()

main()
