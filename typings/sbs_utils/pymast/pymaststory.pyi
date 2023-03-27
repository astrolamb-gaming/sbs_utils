from sbs_utils.consoledispatcher import ConsoleDispatcher
from sbs_utils.pymast.pymasttask import DataHolder
from sbs_utils.pymast.pymasttask import PyMastTask
from sbs_utils.engineobject import EngineObject
from sbs_utils.gui import Gui
from sbs_utils.gui import Page
from sbs_utils.pymast.pollresults import PollResults
from sbs_utils.pymast.pymastcomms import PyMastComms
from sbs_utils.pymast.pymastscheduler import PyMastScheduler
from sbs_utils.pymast.pymastscience import PyMastScience
from sbs_utils.tickdispatcher import TickDispatcher
class PyMastStory(object):
    """class PyMastStory"""
    def END (self):
        ...
    def __call__ (self, sim, sched=None):
        """Call self as a function."""
    def __init__ (self) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def add_scheduler (self, sim, label):
        ...
    def assign_player_ship (self, player):
        ...
    def await_comms (self, player, npc, buttons):
        ...
    def await_gui (self, buttons=None, timeout=None, on_message=None):
        ...
    def await_science (self, player, npc, scans):
        ...
    def behave_invert (self, label):
        ...
    def behave_sel (self, *labels):
        ...
    def behave_seq (self, *labels):
        ...
    def behave_until (self, poll_result, label):
        ...
    def delay (self, delay):
        ...
    def disable (self):
        ...
    def enable (self, sim, delay=0, count=None):
        ...
    def get_page (self):
        ...
    def gui_blank (self, style=None):
        ...
    def gui_button (self, message, label, style=None):
        ...
    def gui_checkbox (self, message, value, style=None):
        ...
    def gui_console (self, console, style=None):
        ...
    def gui_console_widget_list (self, console, widgets, style=None):
        ...
    def gui_content (self, content, label, style=None):
        ...
    def gui_drop_down (self, value, values, style=None):
        ...
    def gui_face (self, face, style=None):
        ...
    def gui_hole (self, style=None):
        ...
    def gui_image (self, file, color, label, style=None):
        ...
    def gui_radio (self, message, value, vertical=False, style=None):
        ...
    def gui_row (self, style=None):
        ...
    def gui_section (self, style=None):
        ...
    def gui_ship (self, ship, style=None):
        ...
    def gui_slider (self, val, low, high, show_number=True, label=None, style=None):
        ...
    def gui_text (self, message, style=None):
        ...
    def gui_text_input (self, val, label_message, label, style=None):
        ...
    def jump (self, label):
        ...
    def pop (self):
        ...
    def push (self, label):
        ...
    def schedule_comms (self, player, npc, buttons):
        ...
    def schedule_science (self, player, npc, scans):
        ...
    def schedule_task (self, label):
        ...
    def start (self):
        ...
    def start_client (self):
        ...
    def start_server (self):
        ...
    def watch_event (self, event_tag, label):
        ...
