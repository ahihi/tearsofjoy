import unicodedata

import pygame

class browser:
    def __init__(self, items, screen, config, font, select_item, filter_item=None, show_item=None):
        self.items = items
        self.screen = screen
        self.config = config
        self.font = font
        self.select_item = select_item
        self.filter_item = filter_item or (lambda x, f: f in x)
        self.show_item = show_item or (lambda x: x)

        self.reset()

    def reset(self):
        # current filter string
        self.filter = ""
        # indices of self.items matching the current filter string
        self.filtered_ixes = list(range(len(self.items)))
        # current index into self.filtered_ixes
        self.ix = 0
        
    def interact(self, event):
        if event.type == pygame.KEYDOWN:
            print("unicode = {}".format(event.unicode))
            if event.unicode == "\x1b": # esc
                self.select_item(None)
            elif event.key == 273: # up arrow
                self.increment_ix(-1)
            elif event.key == 274: # down arrow
                self.increment_ix(1)
            elif event.unicode == "\r": # return
                item = self.get_selected_item()
                if item != None:
                    self.select_item(item)
            elif event.unicode == "\x7f": # backspace
                self.update_filter(lambda s: s[:-1])
            elif self.is_typeable_key(event.unicode):
                self.update_filter(lambda s: s + event.unicode)
                
    def draw(self):
        self.screen.fill((0, 0, 0))

        spacing_pre = self.config.line_spacing // 2
        spacing_post = self.config.line_spacing - spacing_pre

        items = [self.items[ix] for ix in self.filtered_ixes]
        
        info = pygame.display.Info()
        row_rect = self.font.get_rect("qb")
        n_rows = info.current_h // (row_rect.height + self.config.line_spacing) - 1
        mid_i = n_rows // 2
        y = 0
        for i in range(n_rows):
            color = (255,)*3 if i == mid_i else (128,)*3
            j = i - mid_i + self.ix
            item = items[j] if 0 <= j < len(items) else None
            y += spacing_pre
            if item != None:
                self.font.render_to(self.screen, (0, y), self.show_item(item), color)
            elif i == mid_i:
                self.font.render_to(self.screen, (0, y), "(empty)", (128,)*3)
            y += row_rect.height + spacing_post

        y += spacing_pre
        self.font.render_to(self.screen, (0, y), self.filter, (255,)*3)

    def is_typeable_key(self, ch):
        if len(ch) != 1:
            return False
        
        cat = unicodedata.category(ch)
        return not cat.startswith("C")
        
    def update_filter(self, update):
        last_items_ix = self.filtered_ixes[self.ix] if len(self.filtered_ixes) > 0 else 0
        self.filter = update(self.filter)
        self.filtered_ixes = [i for i, item in enumerate(self.items) if self.filter_item(item, self.filter)]

        pre_ix = None
        post_ix = None
        for ix, items_ix in enumerate(self.filtered_ixes):
            if items_ix < last_items_ix:
                pre_ix = ix
            else:
                post_ix = ix
                break

        if post_ix != None:
            new_ix = post_ix
        elif pre_ix != None:
            new_ix = pre_ix
        else:
            new_ix = 0

        self.ix = new_ix
    
    def increment_ix(self, delta):
        self.ix = max(0, min(len(self.filtered_ixes) - 1, self.ix + delta))
        
    def get_selected_item(self):
        if self.filtered_ixes:
            return self.items[self.filtered_ixes[self.ix]]
        else:
            return None
