from sbs_utils.mast.mast_node import DescribableNode
def mast_node (append=True):
    ...
class Label(DescribableNode):
    """class Label"""
    def __init__ (self, name, replace=None, m=None, loc=None, compile_info=None):
        """Initialize self.  See help(type(self)) for accurate signature."""
    def add_child (self, cmd):
        ...
    def add_label (self, name, label):
        ...
    def can_fall_into (self, parent):
        ...
    def can_fallthrough (self, parent):
        ...
    def generate_label_begin_cmds (self, compile_info=None):
        ...
    def generate_label_end_cmds (self, compile_info=None):
        ...
    def parse (lines):
        ...
