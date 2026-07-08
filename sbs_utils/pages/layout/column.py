from ...mast.parsers import LayoutAreaParser, LayoutAreaNode
from ...gui import get_client_aspect_ratio
from .font import get_font_size
from ...procedural.gui.style import gui_style_def
from .bounds import Bounds, is_out_of_bounds, calc_bounds
from ...helpers import FrameContext
from ...agent import Agent
from .clickable import Clickable
from .dirty import Dirty
import math as math
import weakref

class Column:
    def __init__(self, left=0, top=0, right=0, bottom=0) -> None:
        self._bounds = Bounds(left,top,right,bottom)
        self.min_bounds = None

        self.padding = None
        self.border = None
        self.margin = None

        self.padding_style = None
        self.border_style = None
        self.margin_style = None
        self.bounds_style = None


        self.background_color = None
        self.background_image = "smallWhite"
        self.border_image = "smallWhite"
        self.border_color = None

        self.color = None
        self.default_color = None
        self.justify = None
        self.default_justify = None
        self.font = None
        self.default_font = None

        self.square = False
        """
        `square` is a boolean flag indicating if the column is literally a square when presented. Its bounds will be adjusted based on minimum available hieght/width, whichever is smaller.
        """
        self.default_width = None
        """
        `default_width` is set by calling :class:`Column`.:meth:`set_col_width` in style.py.
        It could be an integer or any style string, e.g. `5px` or `2em`.
        """
        self.default_height = None
        """
        `default_height` is set by calling :class:`Column`.:meth:`set_row_height` in style.py.
        It could be an integer or any style string, e.g. `5px` or `2em`.
        """
        
        self.tag = None
        self.region_tag = ""
        self.click_text = None
        self.click_color = None
        self.click_background = None
        self.click_font = None
        self._click_tag = None
        self.data = None
        self.var_scope_id = None
        self.var_name = None
        self.on_message_cb = None
        self.client_id = None
        self._parent = None
        self._show = True
        """
        :func:`_show` represents the user's desire for a gui element to be displayed. This should only be set using `Column.show()`.
        """
        self._is_shown = True
        """
        :func:`_is_shown` is used internally to ensure that only gui elements that are within the bounds of their parent are displayed.
        If a gui element is outside the bounds of its parent, it will be hidden using `_is_shown = False`. *This is handled by the parent.*
        Don't change this manually. `Column.show()` uses :func:`_show` instead.
        """
        self.is_presenting = False
        """
        Used to determine if true bounds should be used, or if hidden bounds should be used instead. Primary purpose of this is for presenting. When NOT presenting, the true bounds should be used for calculations. If presenting, we hide a gui element (if applicable) using `Bounds.hidden`.
        """

    @property
    def click_tag(self):
        if self._click_tag is not None:
            return self._click_tag
        if self.click_text is not None:
            return f"__click:{self.tag}"
        
    @click_tag.setter
    def click_tag(self, v):
        self._click_tag = v

    @property
    def parent(self):
        if self._parent is None:
            return None

        return self._parent()
        
    @parent.setter
    def parent(self, v):
        
        self._parent = weakref.ref(v)
        

    def mark_layout_dirty(self):
        Dirty.mark_dirty(self.parent)

    def mark_visual_dirty(self):
        #
        # I think the engine handles this wrong, but this workaround 
        # fixes it, or is the right thing to do
        # if self.region_tag != "":
        #     Dirty.mark_dirty(self.parent)
        #     return
        Dirty.mark_dirty(self)

    @property
    def bounds(self):
        # return self._bounds
        if not self.is_presenting:
            # If we're not presenting yet, then we don't want to use Bounds.hidden at all.
            return self._bounds
        # If we are presenting, then we need to check if Bounds.hidden should be used instead.
        if self._show and self._is_shown:
            return self._bounds
        return Bounds.hidden

    @bounds.setter
    def bounds(self, v):
        self._bounds = v


    def set_bounds(self, bounds) -> None:
        self.bounds.left=bounds.left
        self.bounds.top=bounds.top
        self.bounds.right=bounds.right
        self.bounds.bottom=bounds.bottom


    def show(self, _show):
        """
        Use to force the gui element to be hidden, or to allow it to be seen.
        If False - the gui element will always be hidden.
        If True - will be visible assuming that it is within the bounds of its parent.

        Args:
            _show (bool): Should the element be visible.
        """
        if self._show == _show:
            return
        self._show = _show
        self.mark_layout_dirty()

    @property
    def is_hidden(self):
        """
        Use :func:`is_hidden` only to check if the layout item is currently visible to the user.
        It checks both :func:`_show` and :func:`_is_shown`.
        If either of these are False, will return True.
        """
        return not self._show or not self._is_shown
        

    def set_row_height(self, height):
        self.default_height = height

    def set_col_width(self, width):
        self.default_width = width

    def set_padding(self, padding):
        self._padding = padding

    def set_padding(self, padding):
        self._padding = padding

    
    def get_color(self):
        if self.color is not None:
            return self.color
        
        if self.default_color is not None:
            return self.default_color
        return self.color
    
    def get_justify(self):
        if self.justify is not None:
            return self.justify
        if self.default_justify is not None:
            return self.default_justify
        return self.justify
    
    def get_font(self):
        # self.font is set by calc
        if self.font is not None:
            return self.font
        if self.default_font is not None:
            return self.default_font
        return self.font
    
    def get_size_from_stylestring(self, style, aspect_ratio_axis):
        """
        Compute the style to its corresponding value as a percentage of the screen size.
        Args:
            style (str | int | None): The style to parse.
            aspect_ratio_axis (int): The size of the applicable axis, in pixels. Usually gotten using `get_client_aspect_ratio().x` or `.y`.
        Returns:
            int: The percentage of the screen the style indicates.
        """
        # style = getattr(self, style, None)
        if style is not None:
            
            if not isinstance(style, float):
                font_size = get_font_size(self.get_font())
                nodes = LayoutAreaParser.compute(style, None, aspect_ratio_axis, font_size)
                # return LayoutAreaParser.parse_e2(nodes)
                return nodes
        return style
    
    def calc_minimum_bounds(self):
        """
        Get the minimum bounds for use by the parent row.
        If the parent's bounds are smaller than the column's bounds, in either the horizontal or vertical direction, the column will be hidden to prevent overlapping gui elements.
        If the row/column width are not specified, will return a bounds with height and/or width of 0.
        
        NOTE: For some subclasses, this function should probably be overriden.

        Returns:
            Bounds: The bounds object representing the minimum bounds of this column.
        """
        aspect_ratio = get_client_aspect_ratio(self.client_id)
        width = self.get_size_from_stylestring(self.default_width, aspect_ratio.x)
        height = self.get_size_from_stylestring(self.default_width, aspect_ratio.y)
        if width is None:
            width = 0
        if height is None:
            height = 0
        mb = Bounds(0,0,width,height)
        mb.grow(self.padding)
        mb.grow(self.border)
        mb.grow(self.margin)
        return mb
        
    
    def get_cascade_props(self,font = False, color = False, justify = False):
        props = ""
        if font:
            prop = self.get_font()
            if prop is not None:
                props += f"font:{prop};"
        if color:
            prop = self.get_color()
            if prop is not None:
                props += f"color:{prop};"
        if justify:
            prop = self.get_justify()
            if prop is not None:
                props += f"justify:{prop};"
        return props

    def set_margin(self, margin):
        self.margin = margin

    def set_border(self, border):
        self.border = border

    def represent(self, event):
        if self.client_id is None:
            return
        self.present(event)

    def present(self, event):
        # if self.is_hidden:
        #     print("Column is Hidden!!!")
        #     print(self._bounds)
        #     print(self.tag)
        self.client_id = event.client_id
        self.is_presenting = True
        self._pre_present(event)
        self._present(event)
        self._post_present(event)
        self.is_presenting = False

    def _present(self, event):
        pass

    def _pre_present(self, event):
        ctx = FrameContext.context
        if self.border is not None and self.border_color is not None:
            bb = Bounds(self.bounds)
            bb.shrink(self.margin)

            bb_props = f"image:{self.border_image}; color:{self.border_color};draw_layer:1000;"
            ctx.sbs.send_gui_image(event.client_id, self.region_tag,
                "__bb:"+self.tag, bb_props,
                bb.left, bb.top, bb.right, bb.bottom)
            
        if self.background_color is not None:
            props = f"image:{self.background_image}; color:{self.background_color};draw_layer:1000;"
            
            #
            # Bounds include padding, margin for column
            # Layout Calc fills this in
            #
            bg = Bounds(self.bounds)
            bg.shrink(self.margin)
            bg.shrink(self.border)
            # bg.shrink(self.padding)
            ctx.sbs.send_gui_image(event.client_id, self.region_tag,
                "__bg:"+self.tag, props,
                bg.left, bg.top, bg.right, bg.bottom)

    def _post_present(self, event):
        if self.click_text is not None or self.click_tag is not None:
            click_props = ""
            if self.click_text is not None:
                click_props = f"$text:{self.click_text};"
            if self.click_color:
                click_props += f"color: {self.click_color};"
            if self.click_font:
                click_props += f"font: {self.click_font};"
            if self.click_tag is None:
                self.click_tag = f"__click:{self.tag}"
            if self.click_background is not None:
                click_props += f"background_color:{self.click_background};"
            else:
                click_props += f"background_color: white;"

            ctx = FrameContext.context
            #
            #
            #
            bounds = Bounds(self.bounds)
            bounds.shrink(self.margin)
            bounds.shrink(self.border)
            # if self.padding is not None:
            #     bounds.shrink(self.padding)
            
            ctx.sbs.send_gui_clickregion(event.client_id, self.region_tag,
                self.click_tag, click_props,
                bounds.left, bounds.top, bounds.right, bounds.bottom)
            

    def invalidate_regions(self):
        pass


    # I decided to leave this here instead of moving it to bounds.py because it needs the font and client_id information for the current client/object/scope
    def get_bounds_for_text(self, text, max_width=None):
        """
        Get the Bounds area taken up by the specified text. If `max_width` is None, then it will assume the text does not wrap.
        
        Args:
            text (str): The text
            max_width (str|int): If an integer, is the maximum allowable percent width. If a string, is parsed as a stylestring represntative of the maximum allowable width, e.g. "200px" or "5em".
        Returns:
            Bounds: The Bounds of the text.
        """
        sbs = FrameContext.context.sbs
        font = self.get_font()
        if font is None:
            font = "gui-1"
        font = font.strip() # Often has a leading space, which the engine doesn't account for!!!

        sec_font_size = get_font_size(font)
        aspect_ratio = get_client_aspect_ratio(self.client_id)

        width = None
        height = None

        # print(f"Getting bounds for text:\n-----{text}")
        # print(f"Max width: {max_width}")

        if max_width is not None:
            # Max width could be in any format, so we parse it's value and convert it to the pixel values, to match the sbs function's needs.

            if isinstance(max_width, LayoutAreaNode):
                max_width = max_width.value
            if max_width.isdecimal():
                # In this case we're assuming a percent.
                pixels = int(max_width)/100*aspect_ratio.x

            else:
                # Convert the long complicated way...
                area_style = f"area: 0,0,{max_width},0;"
                style = gui_style_def(area_style).get("area")
                percent = Bounds(calc_bounds(style, aspect_ratio, sec_font_size)).width
                pixels = percent/100*aspect_ratio.x


            # These return *pixel* values, not %, so we have to convert
            pixels = math.ceil(pixels) #pixels must be an int
            height = sbs.get_text_block_height(font, text, pixels)
            width = pixels
        else:
            # These return *pixel* values, not %, so we have to convert
            height = sbs.get_text_line_height(font,text)
            width = sbs.get_text_line_width(font, text)
        
        # THese must be ints
        height = math.ceil(height)
        width = math.ceil(width)

        # Should only be -1 if there's an issue with how the engine interprets the font
        if height == -1 or width == -1:
            print(f"Min -1 for {text}")
            return Bounds(0,0,0,0)
        
        print(f"Width: {width}    Height: {height}")
        
        # Now we do the conversion from pixels
        area_style = f"area: 0,0,{width}px,{height}px;"
        style = gui_style_def(area_style).get("area")
        return Bounds(calc_bounds(style, aspect_ratio, sec_font_size))

    def get_min_text_width(self,text):
        """
        Returns the minimum width of the text, in % of screen width.
        Finds the longest word in the text and uses that as the width.
        Then gets the bounds of the text using that word's width.
        
        Args:
            text (str): The text
        Returns:
            int: The width of the longest word in the text.
        """
        longest_word = max(text.split(), key=len)
        return self.get_bounds_for_text(longest_word).width

    def get_min_text_height(self,text,width=None):
        """
        Gets the minimum height of the text with the specified width.
        Intended to be used to get the height of text if you are limited by width.
        E.g. if you use :func:`get_min_text_width`, and use the result as the width.

        Args:
            text (str): The text
            max_width (str|int): If an integer, is the maximum allowable percent width. If a string, is parsed as a stylestring represntative of the maximum allowable width, e.g. "200px" or "5em".
        Returns:
            int: the height of the text, constrained by the width.
        """
        if width is None:
            return self.get_bounds_for_text(text).height
        else:
            return self.get_bounds_for_text(text,width).width

    def is_message_for(self, event):
        """Used by MessageTrigger i.e. gui_message to know if message is for this object

        Args:
            event (EVENT): the engine event

        Returns:
            bool: if the gui_message MessageTrigger should be True
        """
        return event.sub_tag == self.tag or event.sub_tag == self.click_tag
   
    def on_message(self, event):
        if self.tag is None:
            return
        is_click_tag = event.sub_tag == self.click_tag
        is_tag = event.sub_tag == self.tag
        if  not is_click_tag and not is_tag:
            return 
        if self.on_message_cb is not None:
            self.on_message_cb(event, self)
            return
        if is_click_tag:
            Clickable.clicked[event.client_id] = self
        

    def update(self, props):
        pass

    def calc(self, client_id):
        pass # Unused but here to be compatible with sub sections

    def on_end_presenting(self, client_id):
        pass
    def on_begin_presenting(self, client_id):
        pass

    def update_variable(self):
        if self.var_scope_id:
            scope = Agent.get(self.var_scope_id)
            if scope is not None:
                scope.set_variable(self.var_name, self.value)

    def get_variable(self, default=None):
        if self.var_scope_id:
            scope = Agent.get(self.var_scope_id)
            if scope is not None:
                return scope.get_variable(self.var_name, default)
        return default

    @property
    def value(self):
        return None
    @value.setter
    def value(self, a):
        pass
        

"""
This should probably be put in the docs somewhere, but for now:

NOTE: Padding, Margin, Border

`self._bounds` is always the entire bounds of the gui element, including the contents area, the padding, the border, and the margins.

Margins are the outer gaps between other elements and the layout item's *apparent* boundary.

Border is another outer gap inside of the margin, but which can be colored. 
- Note: If using `border`, you must also specify `border-color` or it won't be used.
- Note: If you use `border`, if you don't specify a `background`, then the background will be filled with the border's color.

Padding is an inner gap between the gui element's contents and its border.


Universal order of operations to handle these:
_pre_present: 
	- Bounds.shrink(margin)
	- Draw border
	- Bounds.shrink(border)
	- Draw background

_present:
	- Bounds.shrink(margin)
	- Bounds.shrink(border)
    - Account for extra things like sliders
    - Present self (if applicable, e.g. send_gui_text)
	- Bounds.shrink(padding)
	- Present children (if applicable)

_post_present:
	- Bounds.shrink(margin)
	- Bounds.shrink(border)
	- Draw extra things like sliders
    - Draw clickregion

"""

