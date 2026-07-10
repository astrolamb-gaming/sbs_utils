from .bounds import Bounds
from .column import Column
from ...helpers import FrameContext, merge_props, split_props

class Text(Column):
    def __init__(self, tag, message) -> None:
        super().__init__()
        self.message = message
        self.value = message
        self.tag = tag

    def _present(self, event):
        ctx = FrameContext.context
        message = self.message + self.get_cascade_props(True, True, True)
        bounds = Bounds(self.bounds)
        bounds.shrink(self.margin)
        bounds.shrink(self.border)
        bounds.shrink(self.padding)
        ctx.sbs.send_gui_text(event.client_id, self.region_tag,
            self.tag, message,
            bounds.left, bounds.top, bounds.right, bounds.bottom)

    def update(self, message):
        props = split_props(message, "$text")
        text = props.get("$text", props.get("text"))
        if text is None:
            props["$text"] = ""
        elif '`' not in text:
            props["$text"] = "`"+text+"`"
        

        message = merge_props(props)
        self.message = message
        if not self.is_hidden:
            self.mark_visual_dirty()

        # TODO: Find a good way to only recalculate a row instead of the whole layout.
        # if self.min_bounds:
        #     mb = self.calc_minimum_bounds()
        #     if mb.width > self.min_bounds.width or mb.height > self.min_bounds.height:
        #         self.mark_layout_dirty()

    def calc_minimum_bounds(self):

        # We'll use this value regardless
        mb = super().calc_minimum_bounds()
        if mb is None:
            print("Column min bounds is None")
            return Bounds(0,0,0,0)

        # Get the text
        props = split_props(self.message, "$text")
        text = props.get("$text", props.get("text"))
        if text is None:
            return mb

        # default_width is None unless it has an actual value, in which case it is given that max width.
        bounds_area = self.get_bounds_for_text(text, self.default_width)

        bounds_area.grow(mb)
        return bounds_area

    
    @property
    def value(self):
         return self.message
       
    @value.setter
    def value(self, v):
        self.update(v)
