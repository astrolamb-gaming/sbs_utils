import logging
from .mastscheduler import PollResults, MastRuntimeNode, MastAsyncTask
from .mast import Mast
import sbs
from ..gui import FakeEvent, Gui, Page

from ..pages import layout
from ..tickdispatcher import TickDispatcher

from .errorpage import ErrorPage
from .maststory import AppendText, ButtonControl, MastStory, Choose, Text, Blank, Ship, Face, Row, Section, Style, Refresh, SliderControl, CheckboxControl, DropdownControl, WidgetList, ImageControl, TextInputControl, AwaitGui, Hole
import traceback
from .mastsbsscheduler import MastSbsScheduler 
from .parsers import LayoutAreaParser

class StoryRuntimeNode(MastRuntimeNode):
    def on_message(self, sim, event):
        pass
    def databind(self):
        return False

class FaceRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Face):
        tag = task.main.page.get_tag()
        face = node.face
        if node.code:
            face = task.eval_code(node.code)
        if face is not None:
            self.layout_item = layout.Face(face, tag)
            task.main.page.add_content(self.layout_item, self)

    def poll(self, mast, task, node:Face):
        return PollResults.OK_ADVANCE_TRUE

class RefreshRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Refresh):
        task.main.mast.refresh_schedulers(task.main, node.label)
        

class ShipRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Ship):
        tag = task.main.page.get_tag()
        task.main.page.add_content(layout.Ship(node.ship, tag), self)


class TextRuntimeNode(StoryRuntimeNode):
    current = None
    def enter(self, mast:Mast, task:MastAsyncTask, node: Text):
        self.tag = task.main.page.get_tag()
        msg = ""
        # for databind
        self.node = node
        self.task = task 
        value = True
        if node.code is not None:
            value = task.eval_code(node.code)
        if value:
            msg = task.format_string(node.message)
            self.layout_text = layout.Text(msg, self.tag)
            TextRuntimeNode.current = self
            task.main.page.add_content(self.layout_text, self)

    def databind(self):
        if True:
            return False
        # value = True
        # if self.node.code is not None:
        #     value = self.task.eval_code(self.node.code)
        # if value:
        #     print("BEFORE")
        #     msg = self.task.format_string(self.node.message)
        #     print(f"DATABIND {msg} {self.layout_text.message}")
        #     if self.layout_text.message !=msg:
        #         self.layout_text.message = msg
        #         return True
        # return False
        

class AppendTextRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: AppendText):
        msg = ""
        value = True
        if node.code is not None:
            value = task.eval_code(node.code)
        if value:
            msg = task.format_string(node.message)
            text = TextRuntimeNode.current
            if text is not None:
                text.layout_text.message += '\n'
                text.layout_text.message += msg

class ButtonControlRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: ButtonControl):
        self.data = None
        if node.is_end == False:
            
            self.tag = task.main.page.get_tag()
            value = True
            
            if node.code is not None:
                value = self.task.eval_code(node.code)
            if value:
                msg = task.format_string(node.message)
                task.main.page.add_content(layout.Button(msg, self.tag), self)
            if node.data_code is not None:
                self.data = task.eval_code(node.data_code)
                
        self.node = node
        self.task = task

        
    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            # Jump to the cmds after the button
            self.task.push_label(self.task.active_label, self.node.loc+1, self.data)

    def poll(self, mast:Mast, task:MastAsyncTask, node: ButtonControl):
        if node.is_end:
            self.task.pop_label()
            return PollResults.OK_JUMP
        elif node.end_node:
            self.task.jump(self.task.active_label, node.end_node.loc+1)
            return PollResults.OK_JUMP


class RowRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Row):
        task.main.page.add_row()
        

class BlankRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Blank):
        task.main.page.add_content(layout.Blank(), self)
class HoleRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Hole):
        task.main.page.add_content(layout.Hole(), self)

class SectionRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Section):
        task.main.page.add_section()

class SyleRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Style):
        values =[]
        i = 1
        for ast in node.asts:
            if i >0:
                ratio =  task.main.page.aspect_ratio.x
            else:
                ratio =  task.main.page.aspect_ratio.y
            i=-i
            values.append(LayoutAreaParser.compute(ast, task.get_symbols(),ratio))
        if node.height is not None:
            height = LayoutAreaParser.compute(node.height, task.get_symbols(),ratio)
            task.main.page.set_default_height(height)

        task.main.page.set_section_size(values)


class AwaitGuiRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: AwaitGui):
        seconds = (node.minutes*60+node.seconds)
        if seconds == 0:
            self.timeout = None
        else:
            self.timeout = sbs.app_seconds()+ (node.minutes*60+node.seconds)
        task.main.page.set_button_layout(None)

    def poll(self, mast:Mast, task:MastAsyncTask, node: AwaitGui):
        if self.timeout:
            if self.timeout <= sbs.app_seconds():
                return PollResults.OK_ADVANCE_TRUE
        return PollResults.OK_RUN_AGAIN


class ChooseRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Choose):
        seconds = (node.minutes*60+node.seconds)
        if seconds == 0:
            self.timeout = None
        else:
            self.timeout = sbs.app_seconds()+ (node.minutes*60+node.seconds)

        top = ((task.main.page.aspect_ratio.y - 30)/task.main.page.aspect_ratio.y)*100

        # ast = LayoutAreaParser.parse_e(LayoutAreaParser.lex("100-30px"))
        # top = LayoutAreaParser.compute(ast, {}, task.main.page.aspect_ratio.y)
        button_layout = layout.Layout(None, 0,top,100,100)

        active = 0
        index = 0
        row: Row
        layout_row = layout.Row()
        for button in node.buttons:
            match button.__class__.__name__:
                case "Button":
                    value = True
                    #button.end_await_node = node.end_await_node
                    if button.code is not None:
                        value = task.eval_code(button.code)
                    if value and button.should_present(0):#task.main.client_id):
                        runtime_node = ChoiceButtonRuntimeNode(self, index, task.main.page.get_tag(), button)
                        #runtime_node.enter(mast, task, button)
                        msg = task.format_string(button.message)
                        layout_button = layout.Button(msg, runtime_node.tag)
                        layout_row.add(layout_button)
                        task.main.page.add_tag(runtime_node)
                        active += 1
                case "Separator":
                    # Handle face expression
                    layout_row.add(layout.Blank())
            index+=1

        if active>0:    
            button_layout.add(layout_row)
            task.main.page.set_button_layout(button_layout)
        else:
            task.main.page.set_button_layout(None)

        self.active = active
        self.buttons = node.buttons
        self.button = None



    def poll(self, mast:Mast, task:MastAsyncTask, node: Choose):
        if self.active==0 and self.timeout is None:
            return PollResults.OK_ADVANCE_TRUE


        if self.button is not None:
            if node.assign:
                task.set_value_keep_scope(node.assign, self.button.index)
                return PollResults.OK_ADVANCE_TRUE

            self.button.node.visit(self.button.client_id)
            button = self.buttons[self.button.index]
            self.button = None
            task.jump(task.active_label,button.loc+1)
            return PollResults.OK_JUMP

        if self.timeout:
            if self.timeout <= sbs.app_seconds():
                if node.timeout_label:
                    task.jump(task.active_label,node.timeout_label.loc+1)
                    return PollResults.OK_JUMP
                elif node.end_await_node:
                    task.jump(task.active_label,node.end_await_node.loc+1)
                    return PollResults.OK_JUMP
        return PollResults.OK_RUN_AGAIN


class ChoiceButtonRuntimeNode(StoryRuntimeNode):
    def __init__(self, choice, index, tag, node):
        self.choice = choice
        self.index = index
        self.tag = tag
        self.client_id = None
        self.node = node
        
    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            self.choice.button = self
            self.client_id = event.client_id
    



class SliderControlRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: SliderControl):
        self.tag = task.main.page.get_tag()
        self.node = node
        scoped_val = task.get_value(self.node.var, self.node.value)
        val = scoped_val[0]
        self.scope = scoped_val[1]
        self.layout = layout.Slider(val, node.low, node.high, self.tag)
        self.task = task

        task.main.page.add_content(self.layout, self)

    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            if self.node.is_int:
                self.layout.value = int(event.sub_float)
            else:
                self.layout.value = event.sub_float
            self.task.set_value(self.node.var, self.layout.value, self.scope)


class CheckboxControlRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: SliderControl):
        self.tag = task.main.page.get_tag()
        self.node = node
        scoped_val = task.get_value(self.node.var, False)
        val = scoped_val[0]
        self.scope = scoped_val[1]
        msg = task.format_string(node.message)
        self.layout = layout.Checkbox(msg, self.tag, val)
        self.task = task
        task.main.page.add_content(self.layout, self)

    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            self.layout.value = not self.layout.value
            self.task.set_value(self.node.var, self.layout.value, self.scope)
            self.layout.present(sim, event)

class TextInputControlRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: TextInputControl):
        self.tag = task.main.page.get_tag()
        self.node = node
        label = ""
        if node.label is not None:
            label = task.format_string(node.label)
            if label is None:
                label=""
        scoped_val = task.get_value(self.node.var, "")
        val = scoped_val[0]
        self.scope = scoped_val[1]
        self.layout = layout.TextInput(val, label, self.tag)
        self.task = task
        task.main.page.add_content(self.layout, self)

    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            self.layout.value = event.value_tag
            self.task.set_value(self.node.var, self.layout.value, self.scope)
            self.task.main.paint_refresh = True
            self.layout.present(sim, event)

class DropdownControlRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: DropdownControl):
        self.task = task
        # This is weird label may not be active label
        # May need a fiber
        self.label = task.active_label
        if not node.is_end:
            self.tag = task.main.page.get_tag()
            self.node = node
            scoped_val = task.get_value(self.node.var, "")
            val = scoped_val[0]
            self.scope = scoped_val[1]
            values = task.format_string(node.values)
            self.layout = layout.Dropdown(val, values, self.tag )
            task.main.page.add_content(self.layout, self)


    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            self.layout.value = event.value_tag
            self.task.set_value(self.node.var, self.layout.value, self.scope)
            self.task.push_label(self.label, self.node.loc+1)

    def poll(self, mast:Mast, task:MastAsyncTask, node: DropdownControl):
        if node.is_end:
            task.pop_label(False)
            return PollResults.OK_JUMP
        elif node.end_node:
            # skip on first pass
            self.task.jump(self.task.active_label, node.end_node.loc+1)
            return PollResults.OK_JUMP
    
            
class WidgetListRuntimeNode(MastRuntimeNode):
    def enter(self, mast, task: MastAsyncTask, node:WidgetList):
        task.main.page.set_widget_list(node.console, node.widgets)

class ImageControlRuntimeNode(StoryRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: ImageControl):
        tag = task.main.page.get_tag()
        file = task.format_string(node.file)
        self.layout = layout.Image(file, node.color, tag)
        task.main.page.add_content(self.layout, self)


over =     {
    "Row": RowRuntimeNode,
    "Text": TextRuntimeNode,
    "AppendText": AppendTextRuntimeNode,
    "Face": FaceRuntimeNode,
    "Ship": ShipRuntimeNode,
    "ButtonControl": ButtonControlRuntimeNode,
    "SliderControl": SliderControlRuntimeNode,
    "CheckboxControl": CheckboxControlRuntimeNode,
    "DropdownControl": DropdownControlRuntimeNode,
    "ImageControl":ImageControlRuntimeNode,
    "TextInputControl": TextInputControlRuntimeNode,
    "WidgetList":WidgetListRuntimeNode,
    "Blank": BlankRuntimeNode,
    "Hole": HoleRuntimeNode,
    "AwaitGui": AwaitGuiRuntimeNode,
    "Choose": ChooseRuntimeNode,
    "Section": SectionRuntimeNode,
    "Style": SyleRuntimeNode,
    "Refresh": RefreshRuntimeNode

}

class StoryScheduler(MastSbsScheduler):
    def __init__(self, mast: Mast, overrides=None):
        if overrides:
            super().__init__(mast, over|overrides)
        else:
            super().__init__(mast,  over)
        self.sim = None
        self.paint_refresh = False
        self.errors = []
        self.client_id = None

    def run(self, sim, client_id, page, label="main", inputs=None):
        self.sim = sim
        self.page = page
        self.client_id = client_id
        inputs = inputs if inputs else {}
        self.vars['sim'] = sim
        self.vars['client_id'] = client_id
        self.vars['IS_SERVER'] = client_id==0
        self.vars['IS_CLIENT'] = client_id!=0
        self.vars['page'] = page
        super().start_task( label, inputs)

    def story_tick_tasks(self, sim, client_id):
        self.sim = sim
        self.vars['sim'] = sim
        self.client_id = client_id
        return super().sbs_tick_tasks(sim)

    def refresh(self, label):
        for task in self.tasks:
            if label == task.active_label:
                task.jump(task.active_label)
                self.story_tick_tasks(self.sim, self.client_id)
                Gui.dirty(self.client_id)

    def runtime_error(self, message):
        if self.sim:
            sbs.pause_sim()
        err = traceback.format_exc()
        if not err.startswith("NoneType"):
            message += str(err)
            self.errors = [message]
    def on_event(self, sim, event):
        if event.client_id == self.client_id:
            # is this too chatty?
            self.start_task("__EVENT__", {"event": event})
            

class StoryPage(Page):
    tag = 0
    story_file = None
    inputs = None
    story = None
    def __init__(self) -> None:
        self.gui_state = 'repaint'
        self.story_scheduler = None
        self.layouts = []
        self.pending_layouts = self.pending_layouts = [layout.Layout(None, 0,0, 100, 90)]
        self.pending_row = self.pending_row = layout.Row()
        self.pending_tag_map = {}
        self.tag_map = {}
        self.aspect_ratio = sbs.vec2(1920,1071)
        self.client_id = None
        self.sim = None
        self.console = ""
        self.widgets = ""
        self.pending_console = ""
        self.pending_widgets = ""
        #self.tag = 0
        self.errors = []
        cls = self.__class__
        
        if cls.story is None:
            if cls.story is  None:
                cls.story = MastStory()
                self.errors =  cls.story.from_file(cls.story_file)
        

    def start_story(self, sim, client_id):
        if self.story_scheduler is not None:
            return
        cls = self.__class__
        if len(self.errors)==0:
            self.story_scheduler = StoryScheduler(cls.story)
            if cls.inputs:
                self.story_scheduler.run(sim, client_id, self, inputs=cls.inputs)
            else:
                self.story_scheduler.run(sim, client_id, self)
            TickDispatcher.do_interval(sim, self.tick_mast, 0)

    def tick_mast(self, sim, t):
        if self.story_scheduler:
            self.story_scheduler.story_tick_tasks(sim, self.client_id)

   

    def swap_layout(self):
        self.layouts = self.pending_layouts
        self.tag_map = self.pending_tag_map
        self.console = self.pending_console
        self.widgets = self.pending_widgets
        
        self.tag = 10000
        
        if self.layouts:
            for layout_obj in self.layouts:
                layout_obj.calc()
            
            self.pending_layouts = self.pending_layouts = [layout.Layout(None, 0,0, 100, 90)]
            self.pending_row = self.pending_row = layout.Row()
            self.pending_tag_map = {}
            self.pending_console = ""
            self.pending_widgets = ""
        
        self.gui_state = 'repaint'

    def get_tag(self):
        self.tag += 1
        return str(self.tag)

    def add_row(self):
        if not self.pending_layouts:
            self.pending_layouts = [layout.Layout(None, 20,10, 100, 90)]
        if self.pending_row:
            if len(self.pending_row.columns):
                self.pending_layouts[-1].add(self.pending_row)
        if self.pending_tag_map is None:
            self.pending_tag_map = {}
        self.pending_row = layout.Row()

    def add_tag(self, layout_item):
        if self.pending_tag_map is None:
            self.pending_tag_map = {}

        if hasattr(layout_item, 'tag'):
            self.pending_tag_map[layout_item.tag] = layout_item

    def add_content(self, layout_item, runtime_node):
        if self.pending_layouts is None:
            self.add_row()

        self.add_tag(runtime_node)
        self.pending_row.add(layout_item)

    def set_widget_list(self, console,widgets):
        self.pending_console = console
        self.pending_widgets = widgets
    
    def add_section(self):
        if not self.pending_layouts:
            self.pending_layouts = [layout.Layout(None, 0,0, 100, 90)]
        else:
            self.add_row()
            self.pending_layouts.append(layout.Layout(None, 0,0, 100, 90))

    def set_section_size(self, values):
        #print( f"SIZE: {left} {top} {right} {bottom}")
        if not self.pending_layouts:
            self.add_row()
        l = self.pending_layouts[-1]
        l.set_size(values[0],values[1], values[2], values[3])

    def set_default_height(self, height):
        if not self.pending_layouts:
            self.add_row()
        l = self.pending_layouts[-1]
        l.set_default_height(height)
    

    def set_button_layout(self, layout):
        if self.pending_row and self.pending_layouts:
            if self.pending_row:
                self.pending_layouts[-1].add(self.pending_row)
        
        if not self.pending_layouts:
            self.add_section()
        
        if layout:
            self.pending_layouts.append(layout)

        self.swap_layout()
    
    def present(self, sim, event):
        """ Present the gui """
        if self.gui_state == "errors":
            return
        if self.story_scheduler is None:
            self.start_story(sim, event.client_id)
        else:
            if len(self.story_scheduler.errors) > 0:
                #errors = self.errors.reverse()
                message = "Compile errors\n".join(self.story_scheduler.errors)
                sbs.send_gui_clear(event.client_id)
                sbs.send_client_widget_list(event.client_id, "", "")
                sbs.send_gui_text(event.client_id, message, "error", 0,20,100,100)
                self.gui_state = "errors"
                return

            if self.story_scheduler.paint_refresh:
                if self.gui_state != "repaint":  
                    self.gui_state = "refresh"
                self.story_scheduler.paint_refresh = False
            
            if not self.story_scheduler.story_tick_tasks(sim, event.client_id):
                #self.story_runtime_node.mast.remove_runtime_node(self)
                Gui.pop(sim, event.client_id)
                return
        if len(self.errors) > 0:
            message = "Compile errors\n".join(self.errors)
            sbs.send_gui_clear(event.client_id)
            sbs.send_client_widget_list(event.client_id, "", "")
            sbs.send_gui_text(event.client_id, message, "error", 0,20,100,100)
            self.gui_state = "errors"
            return
        
        sz = sbs.get_screen_size()
        if sz is not None and sz.y != 0:
            aspect_ratio = sz
            if (self.aspect_ratio.x != aspect_ratio.x or 
                self.aspect_ratio.y != aspect_ratio.y):
                self.aspect_ratio = sz
                for layout in self.layouts:
                    layout.aspect_ratio = aspect_ratio
                    layout.calc()
                self.gui_state = 'repaint'

        
        match self.gui_state:
            case  "repaint":
                sbs.send_gui_clear(event.client_id)
                sbs.send_client_widget_list(event.client_id, self.console, self.widgets)
                # Setting this to a state we don't process
                # keeps the existing GUI displayed

                for layout in self.layouts:
                    layout.present(sim,event)
                
                self.gui_state = "presenting"
            case  "refresh":
                for layout in self.layouts:
                    layout.present(sim,event)
                self.gui_state = "presenting"


    def on_message(self, sim, event):
        
        message_tag = event.sub_tag
        runtime_node = self.tag_map.get(message_tag)
        if runtime_node:
            
            runtime_node.on_message(sim, event)
            refresh = False
            for node in self.tag_map.values():
                if node != runtime_node:
                    bound = node.databind()
                    refresh = bound or refresh
            if refresh:
                self.gui_state = "refresh"
            self.present(sim, event)

    def on_event(self, sim, event):
        if self.story_scheduler is None:
            return
        self.story_scheduler.on_event(sim, event)

        

