import asyncio
import collections
import logging
import os
import sys
from types import SimpleNamespace

import janus

from joycontrol import logging_default as log, utils
from joycontrol.command_line_interface import ControllerCLI
from joycontrol.controller import Controller
from joycontrol.controller_state import ControllerState, button_push
from joycontrol.memory import FlashMemory
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server

import pygame
import pygame.freetype

from browser import browser
from proctrl import proctrl

logger = logging.getLogger(__name__)

os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV'      , '/dev/fb0')

Config = collections.namedtuple("Config", ["bins_root", "font_size", "line_spacing"])
        
class tearsofjoy:
    def __init__(self, screen, config, loop=None):
        self.screen = screen
        self.config = config
        self.loop = loop if loop != None else asyncio.get_event_loop()

        self.ui_q = janus.Queue(loop=self.loop)
        self.joycontrol_q = janus.Queue(loop=self.loop)

        self.font = pygame.freetype.SysFont(pygame.font.get_default_font(), self.config.font_size)

        bins = sorted((SimpleNamespace(path=os.path.join(path, fn), name=fn) for path, dirs, files in os.walk(self.config.bins_root) for fn in files if os.path.splitext(fn)[1].lower() == ".bin"), key=lambda b: b.name)
        self.browser = browser(
            bins, self.screen, self.config, self.font, self.select_nfc,
            filter_item=lambda b, f: f.lower() in b.name.lower(),
            show_item=lambda b: b.name
        )
        self.proctrl = proctrl(self.screen, self.config, self.font, self.browse_nfc, self.joycontrol_q)

        self.ctrl = self.proctrl
        
    def browse_nfc(self):
        #self.browser.reset()
        self.ctrl = self.browser
        pygame.key.set_repeat(200, 40)
        
    def select_nfc(self, nfc):
        if nfc != None:
            with open(nfc.path, "rb") as nfc_fp:
                nfc.data = nfc_fp.read()
                
        self.proctrl.reset()
        self.proctrl.select_nfc(nfc)
        self.ctrl = self.proctrl
        pygame.key.set_repeat()
        
    def interact(self, event):
        return self.ctrl.interact(event)
        
    def draw(self):
        self.ctrl.draw()

    def run_ui(self):
        done = False

        while not done:
            for event in pygame.event.get():
                print(event)
            
                is_quit = event.type == pygame.QUIT
        
                if is_quit:
                    done = True
                else:
                    done = self.interact(event) or done
                
            self.draw()
            pygame.display.flip()

        self.joycontrol_q.sync_q.put(None)
        #sys.exit(0)

    async def run_joycontrol(self):
        factory = controller_protocol_factory(Controller.PRO_CONTROLLER)
        ctl_psm, itr_psm = 17, 19
        transport, protocol = await create_hid_server(
            factory,
            ctl_psm=ctl_psm,
            itr_psm=itr_psm
        )
        controller_state = protocol.get_controller_state()
        
        #controller_state.l_stick_state.set_center()
        #controller_state.r_stick_state.set_center()

        await controller_state.connect()
        print("connected")
        self.proctrl.connected = True
        self.draw()
        
        while True:
            func = await self.joycontrol_q.async_q.get()
            if func != None:
                func(controller_state)
                await controller_state.send()
            else:
                break

if __name__ == '__main__':
    # check if root
    if not os.geteuid() == 0:
        raise PermissionError('Script must be run as root!')

    # setup logging
    #log.configure(console_level=logging.ERROR)
    log.configure()

    pygame.init()

    pygame.mouse.set_visible(False)

    the_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    loop = asyncio.get_event_loop()

    bins_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), "nfc")
    
    tears = tearsofjoy(the_screen, Config(
        bins_root=bins_root,
        font_size=32,
        line_spacing=8
    ), loop=loop)

    loop.run_in_executor(None, tears.run_ui)
    loop.run_until_complete(tears.run_joycontrol())
