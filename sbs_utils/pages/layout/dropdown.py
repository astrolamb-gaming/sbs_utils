from .bounds import Bounds
from .column import Column
from ...helpers import FrameContext, split_props


class Dropdown(Column):
    def __init__(self, tag, props) -> None:
        super().__init__()
        self.values = props
        self.tag = tag
        prop_list = split_props(props, "$text")
        self._value = prop_list.get("$text", prop_list.get("text",""))
        items = prop_list.get("list","")
        if items == "" or items is None:
            items = "EMPTY"
        
    def _present(self, event):
        ctx = FrameContext.context
        ctx.sbs.send_gui_dropdown(event.client_id, self.region_tag,
            self.tag, self.values,
            self.bounds.left, self.bounds.top, self.bounds.right, self.bounds.bottom)
        
    def on_message(self, event):
        if event.sub_tag == self.tag:
            self.value = event.value_tag
        super().on_message(event)

    def update(self, props):
        self.props = props

    @property
    def value(self):
        return self._value
       
    @value.setter
    def value(self, v):
        self._value= v
        self.update_variable()

    def calc_minimum_bounds(self, available_width=None):

        # We'll use this value regardless
        mb = super().calc_minimum_bounds(available_width)
        if mb is None:
            print("Column min bounds is None")
            return Bounds(0,0,0,0)

        # text = self._value
        # if text == "" or text is None:
        #     text = "X" # Using a short value to represent the minimum width/height needed if empty.

        # default_width is None unless it has an actual value, in which case it is given that max width.
        max_width = available_width if available_width is not None else self.default_width

        props = split_props(self.values, "list")
        item_list = props.get("list", "").split(",")

        # Minimum content width is the largest individual word across all options,
        # so option text does not wrap mid-word when space is constrained.
        largest_word_width = 0
        for item in item_list:
            words = item.split()
            if len(words) == 0:
                words = [item]
            for word in words:
                word_bounds = super().get_bounds_for_text(word, None)
                if word_bounds.width > largest_word_width:
                    largest_word_width = word_bounds.width

        bounds_area = Bounds() # Start with a 0x0 bounds
        for text in item_list:
            text_bounds = super().get_bounds_for_text(text, max_width)
            if text_bounds.height > bounds_area.height:
                bounds_area.height = text_bounds.height

        if bounds_area.width < largest_word_width:
            bounds_area.width = largest_word_width
        bounds_area.grow(mb)
        return bounds_area
