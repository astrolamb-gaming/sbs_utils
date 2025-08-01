from sbs_utils.helpers import FakeEvent
from sbs_utils.helpers import FrameContext
from sbs_utils.mast.parsers import LayoutAreaParser
def apply_control_styles (control_name, extra_style, layout_item, task):
    ...
def get_client_aspect_ratio (cid):
    ...
def layout_list_box_control (items, template_func=None, title_template=None, section_style=None, title_section_style=None, select=False, multi=False, carousel=False, collapsible=False, read_only=False):
    ...
class LayoutListBoxHeader(object):
    """class LayoutListBoxHeader"""
    def __init__ (self, label, collapse):
        """Initialize self.  See help(type(self)) for accurate signature."""
class LayoutListbox(Column):
    """A widget to list things passing function/lamdas to get the data needed for option display of
    a template """
    def __init__ (self, left, top, tag_prefix, items, item_template=None, title_template=None, section_style=None, title_section_style=None, select=False, multi=False, carousel=False, collapsible=False, read_only=False) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def _on_message (self, event):
        ...
    def _present (self, event):
        """present
        
        builds/manages the content of the widget
        
        :param sim: simulation
        :type sim: Artemis Cosmos simulation
        :param CID: Client ID
        :type CID: int"""
    def calc_max (self, CID):
        ...
    def convert_value (self, item):
        ...
    def default_item_template (self, item):
        ...
    def default_title_template (self):
        ...
    def get_selected (self):
        ...
    def get_selected_index (self):
        ...
    def get_value (self):
        ...
    def invalidate_regions (self):
        ...
    @property
    def items (self):
        ...
    @items.setter
    def items (self, items):
        ...
    def on_carousel_click (self, event):
        ...
    def on_click (self, event):
        ...
    def on_collapse_header (self, event):
        ...
    def on_message (self, event):
        ...
    def on_scroll (self, event):
        ...
    def present (self, event):
        ...
    def redraw_if_showing (self):
        """Redraw if this is already one screen.
        Since sub_region is used if you present too early it will confuse the gui."""
    def represent (self, event):
        ...
    def select_all (self):
        ...
    def select_none (self):
        ...
    def set_col_width (self, width):
        ...
    def set_row_height (self, height):
        ...
    def set_selected_index (self, i, set_cur=True):
        ...
    def set_value (self, value):
        ...
    def update (self, props):
        ...
    @property
    def value (self):
        ...
    @value.setter
    def value (self, v):
        ...
class SubPage(object):
    """A class for use with the layout listbox to make using the procedural gui function work
        """
    def __init__ (self, tag_prefix, region_tag, task, client_id) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def add_content (self, layout_item, runtime_node):
        ...
    def add_row (self):
        ...
    def add_tag (self, layout_item, runtime_node):
        ...
    def get_pending_row (self):
        ...
    def get_tag (self):
        ...
    def next_slot (self, slot, section):
        ...
    def pop_sub_section (self, add, is_rebuild):
        ...
    def present (self, event):
        ...
    def push_sub_section (self, style, layout_item, is_rebuild):
        ...
