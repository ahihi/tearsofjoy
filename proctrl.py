import re
from types import SimpleNamespace

from joycontrol.controller_state import button_push

import pygame

class proctrl:
    def __init__(self, screen, config, font, browse_nfc, joycontrol_q):
        self.screen = screen
        self.config = config
        self.font = font
        self.browse_nfc = browse_nfc
        self.nfc = None
        self.joycontrol_q = joycontrol_q
        self.connected = False
        
        self.buttons = SimpleNamespace(
            ls_up = "2",
            ls_down = "w",
            ls_left = "q",
            ls_right = "e",
            ls_push = "1",
            up = "s",
            down = "x",
            left = "z",
            right = "c",
            a = "i",
            b = "u",
            x = "7",
            y = "y",
            rs_up = "j",
            rs_down = "m",
            rs_left = "n",
            rs_right = ",",
            rs_push = "k",
            l = "3",
            zl = "4",
            r = "6",
            zr = "5",
            plus = "t",
            minus = "r",
            home = "g",
            capture = "f",
            nfc_load = "v",
            nfc_use = "b"
        )
        self.keys = {k: b for b, k in self.buttons.__dict__.items()}
        self.button_size = 1.0/14.0
        self.reset()

    def reset(self):
        self.buttons_down = {}
        
    def interact(self, event):
        if event.type == pygame.KEYDOWN:
            # key down

            if event.unicode == "\x1b": # esc
                return True

            # is this a key mapped to one of the buttons?
            button = self.keys.get(event.unicode)
            if button != None and self.is_enabled(button):
                self.buttons_down[button] = event.key

                # is this an analog stick or an actual button?
                stick_match = re.match(r"^(l|r)s_(.*)$", button)
                if stick_match:
                    left = stick_match.group(1) == "l"
                    #get_stick = (lambda cs: cs.l_stick_state) if left else (lambda cs: cs.r_stick_state)
                    get_stick = (lambda side: lambda cs: getattr(cs, "{}_stick_state".format(side)))(stick_match.group(1))
                    #direction = stick_match.group(2)
                        
                    set_direction = (lambda d: lambda s: getattr(s, "set_{}".format(d))())(stick_match.group(2))

                    self.joycontrol_q.sync_q.put(lambda cs: set_direction(get_stick(cs)))
                elif button == "nfc_load":
                    self.browse_nfc()
                elif button == "nfc_use":
                    self.joycontrol_q.sync_q.put((lambda data: lambda cs: cs.set_nfc(data))(self.nfc.data))
                else:
                    # press the button
                    self.joycontrol_q.sync_q.put(lambda cs: cs.button_state.set_button(button, pushed=True))
        elif event.type == pygame.KEYUP:
            # key up
            
            # does this match one of the buttons being pressed?
            for button, key in self.buttons_down.items():
                if key == event.key:
                    # release the button
                    del self.buttons_down[button]

                    # is this an analog stick or an actual button?
                    # TODO: refactor
                    stick_match = re.match(r"^(l|r)s_(.*)$", button)
                    if stick_match:
                        pass
                    elif button == "nfc_load":
                        pass
                    elif button == "nfc_use":
                        pass
                    else:
                        self.joycontrol_q.sync_q.put(lambda cs: cs.button_state.set_button(button, pushed=False))
                    break

    def draw(self):        
        self.screen.fill((0, 0, 0))
        #self.font.render_to(self.screen, (100, 100), self.text, (255, 0, 255))
        #self.font.render_to(self.screen, (50, 50), repr(self.buttons_down), (255, 0, 255))

        button_size = self.get_button_size()
        cross_offset_y = button_size + button_size
        info = pygame.display.Info()

        center_x = info.current_w * 0.5
        left_center_x = info.current_w * 0.25
        right_center_x = info.current_w * 0.75
        
        self.draw_buttons((left_center_x - 3*button_size, cross_offset_y), lambda c: (c[0], c[1] + button_size), ["l", "zl"])
        self.draw_cross((left_center_x, cross_offset_y), "ls_up", "ls_down", "ls_left", "ls_right", "ls_push")
        self.draw_cross((left_center_x, cross_offset_y + 4*button_size), "up", "down", "left", "right")
        
        self.draw_buttons((right_center_x + 3*button_size, cross_offset_y), lambda c: (c[0], c[1] + button_size), ["r", "zr"])
        self.draw_cross((right_center_x, cross_offset_y), "x", "b", "y", "a")
        self.draw_cross((right_center_x, cross_offset_y + 4*button_size), "rs_up", "rs_down", "rs_left", "rs_right", "rs_push")

        self.draw_buttons((center_x - 0.5*button_size, cross_offset_y), lambda c: (c[0] + button_size, c[1]), ["minus", "plus"])
        self.draw_buttons((center_x - 0.5*button_size, cross_offset_y + button_size), lambda c: (c[0] + button_size, c[1]), ["capture", "home"])

        if self.nfc != None:
            nfc_label = self.nfc.name
            nfc_label_size = button_size * 0.2
            nfc_label_rect = self.font.get_rect(nfc_label, size=nfc_label_size)
            nfc_label_rect.center = (center_x, cross_offset_y + 2.5*button_size - nfc_label_rect.height)

            self.font.render_to(self.screen, nfc_label_rect, nfc_label, (255, 255, 255), size=nfc_label_size)

        rect = pygame.Rect(0, 0, button_size, button_size)
        rect.center = (center_x - 0.5*button_size, cross_offset_y + 3*button_size)
        self.draw_button("nfc_load", rect)
        rect.center = (center_x + 0.5*button_size, cross_offset_y + 3*button_size)
        self.draw_button("nfc_use", rect)

    def is_enabled(self, button):
        is_disabled_nfc_use = button == "nfc_use" and self.nfc == None
        is_stick = re.match(r"^[lr]s_", button)
        return self.connected and not (is_disabled_nfc_use or is_stick)
        
    def select_nfc(self, nfc):
        self.nfc = nfc
                
    def get_button_size(self):
        return self.button_size * pygame.display.Info().current_w       
                
    def draw_button(self, button, rect):
        down = button in self.buttons_down
        color = (255, 0, 255) if down else (255, 255, 255)
        if not self.is_enabled(button):
            color = tuple(map(lambda c: 0.5*c, color))
            
        key_label = self.buttons.__dict__[button]
        key_label_size = rect.height * 0.4
        key_label_rect = self.font.get_rect(key_label, size=key_label_size)
        key_label_rect.center = rect.center
        
        button_label = button
        button_label_size = rect.height * 0.2
        button_label_rect = self.font.get_rect(button_label, size=button_label_size)
        button_label_rect.center = (rect.centerx, rect.bottom - 1.0*button_label_rect.height)

        pygame.draw.rect(self.screen, color, rect, 2)
        self.font.render_to(self.screen, key_label_rect, key_label, color, size=key_label_size)
        self.font.render_to(self.screen, button_label_rect, button_label, tuple(map(lambda c: 0.5*c, color)), size=button_label_size)            

    def draw_cross(self, center, up_button, down_button, left_button, right_button, center_button = None):
        button_size = self.get_button_size()
        rect = pygame.Rect(0, 0, button_size, button_size)

        rect.center = (center[0], center[1] - button_size)
        self.draw_button(up_button, rect)
        rect.center = (center[0], center[1] + button_size)
        self.draw_button(down_button, rect)
        rect.center = (center[0] - button_size, center[1])
        self.draw_button(left_button, rect)
        rect.center = (center[0] + button_size, center[1])
        self.draw_button(right_button, rect)
        if center_button:
            rect.center = center
            self.draw_button(center_button, rect)

    def draw_buttons(self, center, next_center, buttons):
        button_size = self.get_button_size()
        rect = pygame.Rect(0, 0, button_size, button_size)
        rect.center = center
        for button in buttons:
            self.draw_button(button, rect)
            rect.center = next_center(rect.center)
