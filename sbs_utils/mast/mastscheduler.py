from __future__ import annotations
from enum import IntEnum
from typing import List
from .mast import *
import time
import traceback
from ..agent import Agent, get_task_id
from ..helpers import FrameContext
from ..procedural.futures import Promise


class MastRuntimeNode:
    def enter(self, mast, scheduler, node):
        pass
    def leave(self, mast, scheduler, node):
        pass
    
    def poll(self, mast, scheduler, node):
        return PollResults.OK_ADVANCE_TRUE


# class MastAsyncTask:
#     pass

# Using enum.IntEnum 
class PollResults(IntEnum):
     OK_JUMP = 1
     OK_ADVANCE_TRUE = 2
     OK_ADVANCE_FALSE=3
     OK_RUN_AGAIN = 4
     OK_YIELD=5 # This will advance, but run again
     FAIL_END = 100
     OK_END = 99

class EndRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task, node:End):
        if node.if_code:
            value = task.eval_code(node.if_code)
            if not value:
                return PollResults.OK_ADVANCE_TRUE
        return PollResults.OK_END

class ReturnIfRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task, node:ReturnIf):
        if node.if_code:
            value = task.eval_code(node.if_code)
            if not value:
                return PollResults.OK_ADVANCE_TRUE
        task.pop_label(False, False)
        return PollResults.OK_JUMP

class FailRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task, node:Fail):
        if node.if_code:
            value = task.eval_code(node.if_code)
            if not value:
                return PollResults.OK_ADVANCE_TRUE
    
        return PollResults.FAIL_END
    
class YieldRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task, node:Yield):
        if node.if_code:
            value = task.eval_code(node.if_code)
            if not value:
                return PollResults.OK_ADVANCE_TRUE
        if node.result is None:
            return PollResults.OK_YIELD
        if node.result.lower() == 'fail':
            return PollResults.FAIL_END
        if node.result.lower() == 'success':
            return PollResults.OK_END
        return PollResults.OK_RUN_AGAIN
    
class ChangeRuntimeNode(MastRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: Change):
        self.task = task
        self.node = node
        self.value = task.eval_code(node.value) 

    def test(self):
        prev = self.value
        self.value = self.task.eval_code(self.node.value) 
        return prev!=self.value
        

    def poll(self, mast:Mast, task:MastAsyncTask, node: Change):
        if node.await_node and node.await_node.end_await_node:
            task.jump(task.active_label,node.await_node.end_await_node.loc+1)
            return PollResults.OK_JUMP
        return PollResults.OK_RUN_AGAIN




class AssignRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task:MastAsyncTask, node:Assign):
        #try:
        value = task.eval_code(node.code)
        start = task.get_variable(node.lhs) 
        match node.oper:
            case Assign.EQUALS:
                pass
            case Assign.INC:
                value = start + value
            case Assign.DEC:
                value = start - value
            case Assign.MUL:
                value = start * value
            case Assign.MOD:
                value = start % value
            case Assign.DIV:
                value = start / value
            case Assign.INT_DIV:
                value = start // value


        if "." in node.lhs or "[" in node.lhs:
            task.exec_code(f"""{node.lhs} = __mast_value""",{"__mast_value": value}, None )
            
        elif node.scope: 
            task.set_value(node.lhs, value, node.scope)
        else:
            task.set_value_keep_scope(node.lhs, value)
            
        # except:
        #     task.main.runtime_error(f"assignment error {node.lhs}")
        #     return PollResults.OK_END

        return PollResults.OK_ADVANCE_TRUE

class PyCodeRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task:MastAsyncTask, node:PyCode):
        def export(cls):
            add_to = task.main.inventory.collections
            def decorator(*args, **kwargs):
                # if 'task' in inspect.signature(cls).parameters:
                #     kwargs['task'] = task
                #add_to[cls.__name__] = cls
                return cls(*args, **kwargs)
            add_to[cls.__name__] = decorator
            return decorator

        def export_var(name, value, shared=False):
            if shared:
                #
                #task.main.mast.vars[name] = value
                Agent.SHARED.set_inventory_value(name, value, None)
            else:
                # task.main.vars[name] = value
                task.main.set_inventory_value(name, value, None)
                




        task.exec_code(node.code,{"export": export, "export_var": export_var}, None )
        return PollResults.OK_ADVANCE_TRUE

class FuncCommandRuntimeNode(MastRuntimeNode):
    def enter(self, mast, task:MastAsyncTask, node:FuncCommand):
        self.value = task.eval_code(node.code)
        self.is_await = node.is_await
        if self.is_await and not isinstance(self.value, Promise):
            self.is_await = False

    def poll(self, mast, task:MastAsyncTask, node:FuncCommand):
        #
        # await the promise to complete
        #
        if node.is_await and self.value is not None and not self.value.done():
            return PollResults.OK_RUN_AGAIN
        return PollResults.OK_ADVANCE_TRUE

class JumpRuntimeNode(MastRuntimeNode):
    def poll(self, mast:Mast, task:MastAsyncTask, node:Jump):
        if node.if_code:
            value = task.eval_code(node.if_code)
            if not value:
                return PollResults.OK_ADVANCE_TRUE
            
        if node.push:
            args = node.args
            if node.args is not None:
                args = task.eval_code(node.args)
            task.push_label(node.label, data=args)
        elif node.pop_jump:
            task.pop_label(True,True)
            task.jump(node.label)
        elif node.pop_push:
            task.pop_label(True,True)
            task.push_label(node.label)
        elif node.pop:
            task.pop_label(True,True)
        else:
            task.jump(node.label)
        return PollResults.OK_JUMP



class LoopStartRuntimeNode(MastRuntimeNode):
    def enter(self, mast, task:MastAsyncTask, node:LoopStart):
        #scoped_val = task.get_scoped_value(node.name, Scope.TEMP, None)
        scoped_cond = task.get_scoped_value(node.name+"__iter", None, Scope.TEMP)
        # The loop is running if cond
        if scoped_cond is None:
            # set cond to true to show we have initialized
            # setting to -1 to start it will be made 0 in poll
            if node.is_while:
                task.set_value(node.name, -1, Scope.TEMP)
                task.set_value(node.name+"__iter", True, Scope.TEMP)
            else:
                value = task.eval_code(node.code)
                try:
                    _iter = iter(value)
                    task.set_value(node.name+"__iter", _iter, Scope.TEMP)
                except TypeError:
                    task.set_value(node.name+"__iter", False, Scope.TEMP)

    def poll(self, mast, task, node:LoopStart):
        # All the time if iterable
        # Value is an index
        current = task.get_scoped_value(node.name, None, Scope.TEMP)
        scoped_cond = task.get_scoped_value(node.name+"__iter", None, Scope.TEMP)
        if node.is_while:
            current += 1
            task.set_value(node.name, current, Scope.TEMP)
            if node.code:
                value = task.eval_code(node.code)
                if value == False:
                    inline_label = f"{task.active_label}:{node.name}"
                    # End loop clear value
                    task.set_value(node.name, None, Scope.TEMP)
                    task.set_value(node.name+"__iter", None, Scope.TEMP)
                    task.jump(task.active_label, node.end.loc+1)
                    return PollResults.OK_JUMP

            
        elif scoped_cond == False:
            print("Possible badly formed for")
            # End loop clear value
            task.set_value(node.name, None, Scope.TEMP)
            task.set_value(node.name+"__iter", None, Scope.TEMP)
            task.jump(task.active_label, node.end.loc+1)
            #task.jump_inline_end(inline_label, False)
            return PollResults.OK_JUMP
        else:
            try:
                current = next(scoped_cond)
                task.set_value(node.name, current, Scope.TEMP)
            except StopIteration:
                # done iterating jump to end
                task.set_value(node.name, None, Scope.TEMP)
                task.set_value(node.name+"__iter", None, Scope.TEMP)
                task.jump(task.active_label, node.end.loc+1)
                return PollResults.OK_JUMP
        return PollResults.OK_ADVANCE_TRUE

class LoopEndRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task, node:LoopEnd):
        if node.loop == True:
            task.jump(task.active_label, node.start.loc)
            return PollResults.OK_JUMP
        return PollResults.OK_ADVANCE_TRUE

class LoopBreakRuntimeNode(MastRuntimeNode):
    def enter(self, mast, task:MastAsyncTask, node:LoopBreak):
        scoped_val = task.get_value(node.start.name, None)
        index = scoped_val[0]
        scope = scoped_val[1]
        if index is None:
            scope = Scope.TEMP
        self.scope = scope

    def poll(self, mast, task, node:LoopBreak):
        if node.if_code:
            value = task.eval_code(node.if_code)
            if not value:
                return PollResults.OK_ADVANCE_TRUE
            
        if node.op == 'break':
            #task.jump_inline_end(inline_label, True)
            task.set_value(node.start.name, None, self.scope)
            task.set_value(node.start.name+"__iter", None, Scope.TEMP)
            task.jump(task.active_label, node.start.end.loc+1)
            # End loop clear value
            
            return PollResults.OK_JUMP
        elif node.op == 'continue':
            task.jump(task.active_label, node.start.loc)
            #task.jump_inline_start(inline_label)
            return PollResults.OK_JUMP
        return PollResults.OK_ADVANCE_TRUE

class IfStatementsRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task, node:IfStatements):
        """ """
        # if this is THE if, find the first true branch
        if node.if_op == "if":
            activate = self.first_true(task, node)
            if activate is not None:
                task.jump(task.active_label, activate+1)
                return PollResults.OK_JUMP
        else:
            # Everything else jumps to past the endif
            activate = node.if_node.if_chain[-1]
            task.jump(task.active_label, activate+1)
            return PollResults.OK_JUMP

    def first_true(self, task: MastAsyncTask, node: IfStatements):
        cmd_to_run = None
        for i in node.if_chain:
            test_node = task.cmds[i]
            if test_node.code:
                value = task.eval_code(test_node.code)
                if value:
                    cmd_to_run = i
                    break
            elif test_node.end == 'else:':
                cmd_to_run = i
                break
            elif test_node.end == 'end_if':
                cmd_to_run = i
                break

        return cmd_to_run

class MatchStatementsRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task, node:MatchStatements):
        """ """
        # if this is THE if, find the first true branch
        if node.op == "match":
            activate = self.first_true(task, node)
            if activate is not None:
                task.jump(task.active_label, activate+1)
                return PollResults.OK_JUMP
        else:
            # Everything else jumps to past the endif
            activate = node.match_node.chain[-1]
            task.jump(task.active_label, activate+1)
            return PollResults.OK_JUMP

    def first_true(self, task: MastAsyncTask, node: MatchStatements):
        cmd_to_run = None
        for i in node.chain:
            test_node = task.cmds[i]
            if test_node.code:
                value = task.eval_code(test_node.code)
                if value:
                    cmd_to_run = i
                    break
            elif test_node.end == 'case_:':
                cmd_to_run = i
                break
            elif test_node.end == 'end_match':
                cmd_to_run = i
                break

        return cmd_to_run


class ParallelRuntimeNode(MastRuntimeNode):
    def enter(self, mast, task: MastAsyncTask, node:Parallel):
        #vars = {} | task.vars if node.labels is not None else None
        vars = {} | task.inventory.collections
        
        if node.code:
            inputs = task.eval_code(node.code)
            vars = vars | inputs
        if isinstance(node.labels, list):
            if node.all:
                task = task.main.start_all_task(node.labels, vars, task_name=node.name, conditional=None)
            elif node.any:
                task = task.main.start_any_task(node.labels, vars, task_name=node.name, conditional=None)
        
        elif node.await_task and node.name:
            task = task.get_variable(node.name)        
        else:
            task = task.start_task(node.labels, vars, task_name=node.name)

        self.task = task if node.await_task else None
        self.timeout = FrameContext.sim_seconds + (node.minutes*60+node.seconds)
        
    def poll(self, mast, task: MastAsyncTask, node:Parallel):
        if self.task:
            if not self.task.done:
                return PollResults.OK_RUN_AGAIN
            if node.fail_label and self.task.done and self.task.result == PollResults.FAIL_END:
                task.jump(task.active_label,node.fail_label.loc+1)
        if node.timeout_label and self.timeout < FrameContext.sim_seconds:
            task.jump(task.active_label,node.timeout_label.loc+1)


        return PollResults.OK_ADVANCE_TRUE
    
class BehaviorRuntimeNode(MastRuntimeNode):
    def enter(self, mast, task: MastAsyncTask, node:Behavior):
        vars = {} | task.inventory.collections if node.labels is not None else None
        if node.code:
            inputs = task.eval_code(node.code)
            vars = vars | inputs
        if isinstance(node.labels, list):
            if node.sequence:
                task = task.main.start_sequence_task(node.labels, vars, task_name=node.name, conditional=node.conditional)
            elif node.fallback:
                task = task.main.start_fallback_task(node.labels, vars, task_name=node.name, conditional=node.conditional)

        self.task = task # if node.is_await else None
        self.timeout = FrameContext.sim_seconds + (node.minutes*60+node.seconds)
        
    def poll(self, mast, task: MastAsyncTask, node:Behavior):
        if self.task:
            if not self.task.done:
                return PollResults.OK_RUN_AGAIN
            if node.is_yield:
                return self.task.result
            if node.fail_label and self.task.done and self.task.result == PollResults.FAIL_END:
                task.jump(task.active_label,node.fail_label.loc+1)
            elif node.until == "success" and self.task.done:
                if  self.task.result == PollResults.FAIL_END:
                    return self.task.rewind()
            elif node.until == "fail" and self.task.done:
                if  self.task.result != PollResults.FAIL_END:
                    return self.task.rewind()
        if node.timeout_label and self.timeout < FrameContext.sim_seconds:
            task.jump(task.active_label,node.timeout_label.loc+1)

        return PollResults.OK_ADVANCE_TRUE


class TimeoutRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task: MastAsyncTask, node:Timeout):
        # if you run into this its from another sub-label
        if node.await_node and node.await_node.end_await_node:
            task.jump(task.active_label,node.await_node.end_await_node.loc+1)

class AwaitFailRuntimeNode(MastRuntimeNode):
    def poll(self, mast, task: MastAsyncTask, node:AwaitFail):
        # if you run into this its from another sub-label
        if node.await_node and node.await_node.end_await_node:
            task.jump(task.active_label,node.await_node.end_await_node.loc+1)


class EndAwaitRuntimeNode(MastRuntimeNode):
    pass


class AwaitConditionRuntimeNode(MastRuntimeNode):
    def enter(self, mast:Mast, task:MastAsyncTask, node: AwaitCondition):
        seconds = (node.minutes*60+node.seconds)
        self.timeout = None
        if seconds != 0:
            self.timeout = FrameContext.sim_seconds + (node.minutes*60+node.seconds)

    def poll(self, mast:Mast, task:MastAsyncTask, node: AwaitCondition):
        value = task.eval_code(node.code)
        if value:
            return PollResults.OK_ADVANCE_TRUE

        if self.timeout is not None and self.timeout <= FrameContext.sim_seconds:
            if node.timeout_label:
                task.jump(task.active_label,node.timeout_label.loc+1)
                return PollResults.OK_JUMP
            elif node.end_await_node:
                task.jump(task.active_label,node.end_await_node.loc+1)
                return PollResults.OK_JUMP
        return PollResults.OK_RUN_AGAIN


#class MastScheduler:
#    pass

class PushData:
    def __init__(self, label, active_cmd, data=None, resume_node=None):
        self.label = label
        self.active_cmd = active_cmd
        self.data = data
        self.runtime_node = resume_node


class MastAsyncTask(Agent):
    main: 'MastScheduler'
    dependent_tasks = {}
    
    def __init__(self, main: 'MastScheduler', inputs=None, conditional= None):
        super().__init__()
        self.id = get_task_id()
        self.done = False
        self.runtime_node = None
        self.main= main
        #self.vars= inputs if inputs else {}
        if inputs:
            self.inventory.collections = dict(self.inventory.collections, **inputs)
            #self.inventory.collections |= inputs
        self.result = None
        self.label_stack = []
        self.active_label = None
        self.events = {}
        #self.vars["mast_task"] = self
        self.set_inventory_value("mast_task", self)
        #self.redirect = None
        self.pop_on_jump = 0
        self.pending_pop = None
        self.pending_jump = None
        self.pending_push = None
        self.add()
    
    def push_label(self, label, activate_cmd=0, data=None):
        #print("PUSH")
        if self.active_label:
            self.pending_push = PushData(self.active_label, self.active_cmd, data)
            self.label_stack.append(self.pending_push)
        self.jump(label, activate_cmd)

    def push_inline_block(self, label, activate_cmd=0, data=None):
        #
        # This type of push resumes running the same runtime node 
        # that was active when the push occurred
        # This done by Buttons, Dropdown and event
        #
        #print("PUSH JUMP POP")
        push_data = PushData(self.active_label, self.active_cmd, data, self.runtime_node)
        self.label_stack.append(push_data)
        self.pop_on_jump += 1
        self.pending_jump = (label,activate_cmd)
        #print(f"PUSH: {label}")
        #self.jump(label, activate_cmd)



    def pop_label(self, inc_loc=True, true_pop=False):
        if len(self.label_stack)>0:
            #
            # Actual Pop was called in an inline block
            # So unwind the inline_blocks
            #
            if true_pop:
                while self.pop_on_jump>0:
                    # if this is a jump and there are tested push
                    # get back to the main flow
                    self.pop_on_jump-=1
                    push_data = self.label_stack.pop()
            elif self.pop_on_jump >0:
                self.pop_on_jump-=1
                # push_data: PushData
                # push_data = self.label_stack.pop()
                # return
            push_data: PushData
            push_data = self.label_stack.pop()
            #print(f"POP: {push_data.label}")
            #print(f"POP DATA {push_data.label} {push_data.active_cmd} len {len(self.label_stack)}")
            if self.pending_jump is None:
                if inc_loc:
                    #print(f"I inc'd {push_data.runtime_node}")
                    self.pending_pop = (push_data.label, push_data.active_cmd+1, push_data.runtime_node)
                else:
                    #print(f"I DID NOT inc {push_data.runtime_node}")
                    self.pending_pop = (push_data.label, push_data.active_cmd, push_data.runtime_node)

    def add_event(self, event_name, event):
        event_data = PushData(self.active_label, event.loc)
        self.events[event_name] = event_data

    def run_event(self, event_name, event):
        ev_data = self.events.get(event_name)
        if ev_data is not None:
            self.push_inline_block(ev_data.label, ev_data.active_cmd+1,{"event": event})
            self.tick()

    def jump(self, label = "main", activate_cmd=0):
        self.pending_jump = (label,activate_cmd)
        while self.pop_on_jump>0:
            # if this is a jump and there are tested push
            # get back to the main flow
            self.pop_on_jump-=1
            push_data = self.label_stack.pop()
            #print(f"POP: {push_data.label}")
    
    
    def do_jump(self, label = "main", activate_cmd=0):
           
        if label == "END":
            self.active_cmd = 0
            self.runtime_node = None
            self.done = True
        else:
            # label_runtime_node = Agent.SHARED.get_inventory_value(label)
            if isinstance(label, str): 
                label_runtime_node = self.main.mast.labels.get(label)
            else:
                label_runtime_node = label

            if label_runtime_node is not None:
                #
                #
                # Why is this here?
                #  Why remove the assignments 
                # Looking to remove or move to known place where Main Ends
                #
                #if self.active_label == "main":
                #    self.main.mast.prune_main()
                    
                self.cmds = label_runtime_node.cmds
                self.active_label = label
                self.active_cmd = activate_cmd
                self.runtime_node = None
                self.done = False
                self.next()
            else:
                self.runtime_error(f"""Jump to label "{label}" not found""")
                self.active_cmd = 0
                self.runtime_node = None
                self.done = True

    def do_resume(self, label, activate_cmd, runtime_node):
        label_runtime_node = self.main.mast.labels.get(label)
        if label_runtime_node is not None:
            self.cmds = self.main.mast.labels[label].cmds
            self.active_label = label
            self.active_cmd = activate_cmd
            self.runtime_node = runtime_node
            self.done = False
        else:
            self.runtime_error(f"""Jump to label "{label}" not found""")
            self.active_cmd = 0
            self.runtime_node = None
            self.done = True

    def get_symbols(self):
        # m1 = self.main.mast.vars | self.main.vars
        mast_inv = Agent.SHARED.inventory.collections
        m1 = mast_inv | self.main.inventory.collections
        m1 =   m1 | self.inventory.collections 
        for st in self.label_stack:
            data = st.data
            if data is not None:
                m1 =   m1 | data
        # if self.redirect and self.redirect.data:
        #     m1 = self.redirect.data | m1
        return m1

    def set_value(self, key, value, scope):
        if scope == Scope.SHARED:
            # self.main.mast.vars[key] = value
            Agent.SHARED.set_inventory_value(key, value)
        elif scope == Scope.TEMP:
            self.set_inventory_value(key, value)
            #self.vars[key] = value
        else:
            self.set_inventory_value(key, value)
            #self.vars[key] = value

    def set_value_keep_scope(self, key, value):
        scoped_val = self.get_value(key, value)
        scope = scoped_val[1]
        if scope is None:
            scope = Scope.TEMP
        # elif scope == Scope.UNKNOWN:
        #     scope = Scope.NORMAL
        self.set_value(key,value, scope)

    def get_value(self, key, defa):
        data = None
        # if self.redirect:
        #     data = self.redirect.data
        if len(self.label_stack) > 0:
            data = self.label_stack[-1].data
        if data is not None:
            val = data.get(key, None)
            if val is not None:
                return (val, Scope.TEMP)
        val = self.get_inventory_value(key, None)
        #val = self.vars.get(key, None)
        if val is not None:
            return (val, Scope.NORMAL)
        return self.main.get_value(key, defa)
    
    def get_scoped_value(self, key, defa, scope):
        if scope == Scope.SHARED:
            return self.main.get_value(key, defa)
        if scope == Scope.TEMP:
            data = None
            # if self.redirect:
            #     data = self.redirect.data
            if len(self.label_stack) > 0:
                data = self.label_stack[-1].data
            if data is not None:
                val = data.get(key, None)
                if val is not None:
                    return val
        val = self.get_inventory_value(key, None)
        return val
        

    def get_variable(self, key, default=None):
        value = self.get_value(key, default)
        return value[0]
    
    def set_variable(self, key, value):
        self.set_value_keep_scope(key,value)

    def call_leave(self):
        if self.runtime_node:
            cmd = self.cmds[self.active_cmd]
            self.runtime_node.leave(self.main.mast, self, cmd)
            self.runtime_node = None

    def format_string(self, message):
        if isinstance(message, str):
            return message
        allowed = self.get_symbols()
        # logger = logging.getLogger("mast.story")
        # for k,v in allowed.items():
        #     if k == "myslot":
        #         logger.info(f"{k}: {v}")
        value = eval(message, {"__builtins__": Mast.globals}, allowed)
        return value
    
    def compile_and_format_string(self, value):
        if isinstance(value, str) and "{" in value:
            value = f'''f"""{value}"""'''
            code = compile(value, "<string>", "eval")
            value = self.format_string(code)
        return value



    def eval_code(self, code):
        value = None
        try:
            allowed = self.get_symbols()
            value = eval(code, {"__builtins__": Mast.globals}, allowed)
        except:
            self.runtime_error(traceback.format_exc())
            self.done = True
        finally:
            pass
        return value

    def exec_code(self, code, vars, gbls):
        try:
            if vars is not None:
                allowed = vars | self.get_symbols()
            else:                
                allowed = self.get_symbols()
            if gbls is not None:
                g = Mast.globals | gbls
            else:
                g = Mast.globals
            exec(code, {"__builtins__": g}, allowed)
        except:
            self.runtime_error(traceback.format_exc())
            self.done = True
        finally:
            pass
        

    def start_task(self, label = "main", inputs=None, task_name=None)->MastAsyncTask:
        inputs= self.inventory.collections|inputs if inputs else self.inventory.collections
        return self.main.start_task(label, inputs, task_name)
    
    def tick(self):
        cmd = None
        FrameContext.task = self
        try:
            if self.done:
                # should unschedule
                return PollResults.OK_END

            count = 0
            while not self.done:
                if self.pending_jump:
                    jump_data = self.pending_jump
                    self.pending_jump = None
                    # Jump takes precedence
                    self.pending_pop = None
                    self.do_jump(*jump_data)
                elif self.pending_pop:
                    # Pending jump trumps pending pop
                    pop_data = self.pending_pop
                    self.pending_pop = None
                    if pop_data[2] is not None:
                        self.do_resume(*pop_data)
                    else:    
                        self.do_jump(pop_data[0], pop_data[1])

                count += 1
                # avoid tight loops
                if count > 1000:
                    break

                if self.runtime_node:
                    cmd = self.cmds[self.active_cmd]
                    # Purged Assigned are seen as Comments
                    if cmd.__class__== "Comment":
                        self.next()
                        continue

                    #print(f"{cmd.__class__} running {self.runtime_node.__class__}")
                    result = self.runtime_node.poll(self.main.mast, self, cmd)
                    match result:
                        case PollResults.OK_ADVANCE_TRUE:
                            self.result = result
                            self.next()
                        case PollResults.OK_YIELD:
                            self.result = result
                            self.next()
                            break
                        case PollResults.OK_ADVANCE_FALSE:
                            self.result = result
                            self.next()
                        case PollResults.OK_END:
                            self.result = result
                            self.done = True
                            return PollResults.OK_END
                        case PollResults.FAIL_END:
                            self.result = result
                            return PollResults.FAIL_END

                        case PollResults.OK_RUN_AGAIN:
                            break
                        case PollResults.OK_JUMP:
                            continue
            return PollResults.OK_RUN_AGAIN
        except BaseException as err:
            self.main.runtime_error(str(err))
            return PollResults.OK_END

        

    def runtime_error(self, rte):
        cmd = None
        logger = logging.getLogger("mast.runtime")
        logger.error(rte)
        s = "mast RUNTIME ERROR\n" 
        if self.runtime_node:
            cmd = self.cmds[self.active_cmd]
        if cmd is None:
            s += f"\n      mast label: {self.active_label}"
        else:
            file_name = Mast.get_source_file_name(cmd.file_num)
            s += f"\n      line: {cmd.line_num} in file: {file_name}"
            s += f"\n      label: {self.active_label}"
            s += f"\n      loc: {cmd.loc} cmd: {cmd.__class__.__name__}\n"
            if cmd.line:
                s += f"\n===== code ======\n\n{cmd.line}\n\n==================\n"
            else:
                s += "\nNOTE: to see code Set Mast.include_code to True is script.py only during development.\n\n"
        s += '\n'+rte

        logger = logging.getLogger("mast.runtime")
        logger.error(s)

        self.main.runtime_error(s)
        self.done = True


    def next(self):
        if self.runtime_node:
            self.call_leave()
            #cmd = self.cmds[self.active_cmd]
            self.active_cmd += 1
        
        if self.active_cmd >= len(self.cmds):
            # move to the next label
            #
            # The first time Main is run, all shared 
            # Assignment should be purged
            # to avoid multiple assignments
            #
            self.main.mast.prune_main()

            active = self.main.mast.labels.get(self.active_label)
            next = active.next
            if next is None:
                self.done = True
                return False
            return self.jump(next.name)
            
        try:
            cmd = self.cmds[self.active_cmd]
            runtime_node_cls = self.main.nodes.get(cmd.__class__.__name__, MastRuntimeNode)
            
            self.runtime_node = runtime_node_cls()
            #print(f"RUNNER {self.runtime_node.__class__.__name__}")
            self.runtime_node.enter(self.main.mast, self, cmd)
        except BaseException as err:
            self.main.runtime_error(str(err))
        
        return True
    
    @classmethod
    def add_dependency(cls, id, task):
        the_set = MastAsyncTask.dependent_tasks.get(id, set())
        the_set.add(task)
        MastAsyncTask.dependent_tasks[id]=the_set

    @classmethod
    def stop_for_dependency(cls, id):
        the_set = MastAsyncTask.dependent_tasks.get(id, set())
        for task in the_set:
            task.done = True
        MastAsyncTask.dependent_tasks.pop(id, None)

class MastBehaveTask(Agent):
    def __init__(self):
        super().__init__()
        self.id = get_task_id()
        self.add()


class MastAllTask(MastBehaveTask):
    def __init__(self, main) -> None:
        super().__init__()
        self.tasks = []
        self.main= main
        self.conditional = None
        self.done = False
        self.result = None
        self.active_label = ""

    def tick(self) -> PollResults:
        if self.conditional is not None and self.task.get_variable(self.conditional):
            self.done = True
            return PollResults.OK_END
        for t in list(self.tasks):
            self.result = t.tick()
            if self.result == PollResults.OK_END:
                self.tasks.remove(t)
                t.destroyed()
        if len(self.tasks):
            return PollResults.OK_RUN_AGAIN
        self.done = True
        return PollResults.OK_END

    def run_event(self, event_name, event):
        for t in list(self.tasks):
            t.run_event(event_name, event)
            
        
class MastAnyTask(MastBehaveTask):
    def __init__(self, main) -> None:
        super().__init__()
        self.tasks = []
        self.main= main
        self.conditional = None
        self.done = False
        self.result = None
        self.active_label = ""

    def tick(self) -> PollResults:
        if self.conditional is not None and self.task.get_variable(self.conditional):
            self.done = True
            return PollResults.OK_END
        for t in self.tasks:
            self.result = t.tick()
            if self.result == PollResults.OK_END:
                self.done = True
                return PollResults.OK_END
        if len(self.tasks):
            return PollResults.OK_RUN_AGAIN
        self.done = True
        return PollResults.OK_END
    def run_event(self, event_name, event):
        for t in list(self.tasks):
            t.run_event(event_name, event)

class MastSequenceTask(MastBehaveTask):
    def __init__(self, main, labels, conditional) -> None:
        super().__init__()
        self.task = None
        self.main= main
        self.labels = labels
        self.conditional = conditional
        self.current_label = 0
        self.done = False
        self.result = None

    @property
    def active_label(self):
        self.task.active_label

    def rewind(self):
        self.current_label = 0
        self.done = False
        label = self.labels[self.current_label]
        self.task.jump(label)
        # The task was removed, re-add
        self.main.tasks.append(self)
        return PollResults.OK_JUMP

    def tick(self) -> PollResults:
        if self.conditional is not None and self.task.get_variable(self.conditional):
            self.done = True
            return PollResults.OK_END
        self.result = self.task.tick()
        if self.result == PollResults.OK_END:
            self.current_label += 1
            if self.current_label >= len(self.labels):
                self.done = True
                return PollResults.OK_END
            # so if this fails as a sequence it reruns the sequence?
            label = self.labels[self.current_label]
            #TODO: I'm not sure why just jump didn't work
            self.task.do_jump(label)
            
            return PollResults.OK_JUMP
        if self.result == PollResults.FAIL_END:
                self.done = True
                return PollResults.FAIL_END
        return PollResults.OK_RUN_AGAIN
    def run_event(self, event_name, event):
        self.task.run_event(event_name, event)

class MastFallbackTask(MastBehaveTask):
    def __init__(self, main,  labels, conditional) -> None:
        super().__init__()
        self.task = None
        self.main= main
        self.labels = labels
        self.conditional = conditional
        self.current_selection = 0
        self.done = False
        self.result = None
        

    @property
    def active_label(self):
        self.task.active_label

    def rewind(self):
        self.current_selection = 0
        self.done = False
        label = self.labels[self.current_selection]
        self.task.do_jump(label)
        self.main.tasks.append(self)
        return PollResults.OK_JUMP

    def tick(self) -> PollResults:
        if self.conditional is not None and  self.task.get_variable(self.conditional):
            self.done = True
            return PollResults.OK_END
        self.result = self.task.tick()
        if self.result == PollResults.FAIL_END:
            self.current_selection += 1
            if self.current_selection >= len(self.labels):
                self.done = True
                return PollResults.FAIL_END
            # so if this fails as a sequence it reruns the sequence?
            label = self.labels[self.current_selection]
            #TODO: I'm not sure why just jump didn't work
            # 
            self.task.do_jump(label)
            #self.result = self.task.tick()
            return PollResults.OK_JUMP
        if self.result == PollResults.OK_END:
            self.done = True
            #print(f"Fallback ended {self.task.active_label}")
            return PollResults.OK_END
        return PollResults.OK_RUN_AGAIN
    def run_event(self, event_name, event):
        self.task.run_event(event_name, event)
    



class MastScheduler(Agent):
    runtime_nodes = {
        "End": EndRuntimeNode,
        "ReturnIf": ReturnIfRuntimeNode,
        "Fail": FailRuntimeNode,
        "Yield": YieldRuntimeNode,
        "Jump": JumpRuntimeNode,
        "IfStatements": IfStatementsRuntimeNode,
        "MatchStatements": MatchStatementsRuntimeNode,
        "LoopStart": LoopStartRuntimeNode,
        "LoopEnd": LoopEndRuntimeNode,
        "LoopBreak": LoopBreakRuntimeNode,
        "PyCode": PyCodeRuntimeNode,
        "FuncCommand": FuncCommandRuntimeNode,
        "Behavior": BehaviorRuntimeNode,
        "Parallel": ParallelRuntimeNode,
        "Assign": AssignRuntimeNode,
        "AwaitCondition": AwaitConditionRuntimeNode,
            "AwaitFail": AwaitFailRuntimeNode,
            "Change": ChangeRuntimeNode,
            "Timeout": TimeoutRuntimeNode,
        "EndAwait": EndAwaitRuntimeNode,
    }

    def __init__(self, mast: Mast, overrides=None):
        super().__init__()
        # Schedulers use task Id
        self.id = get_task_id()
        self.add()
        if overrides is None:
            overrides = {}
        self.nodes = MastScheduler.runtime_nodes | overrides
        self.mast = mast
        self.tasks = []
        self.name_tasks = {}
        self.inputs = None
        #self.vars = {"mast_scheduler": self}
        self.set_inventory_value("mast_scheduler", self)
        self.done = []
        self.mast.add_scheduler(self)
        self.test_clock = 0
        self.active_task = None
        

    def runtime_error(self, message):
        print("mast level runtime error:\n {message}")
        pass

    def get_seconds(self, clock):
        """ Gets time for a given clock default is just system """
        if clock == 'test':
            self.test_clock += 0.2
            return self.test_clock
        return time.time()


    def start_all_task(self, labels = "main", inputs=None, task_name=None, conditional=None)-> MastAllTask:
        all_task = MastAllTask(self)
        if not isinstance(labels, list):
            return self.start_task(label, inputs, task_name)
        
        for label in labels:
            t = self._start_task(label, inputs, None)
            t.jump(label)
            all_task.tasks.append(t)

        #self.on_start_task(t)
        self.tasks.append(all_task)
        if task_name is not None:
            self.active_task.set_value(task_name, all_task, Scope.NORMAL)
        return all_task

    def start_any_task(self, labels = "main", inputs=None, task_name=None, conditional=None)->MastAnyTask:
        any_task = MastAnyTask(self)
        # if single label no need for any
        if not isinstance(labels, list):
            return self.start_task(label, inputs, task_name)
        
        for label in labels:
            t = self._start_task(label, inputs, None)
            t.jump(label)
            any_task.tasks.append(t)

        #self.on_start_task(t)
        self.tasks.append(any_task)
        if task_name is not None:
            self.active_task.set_value(task_name, any_task, Scope.NORMAL)
        return any_task

    def start_sequence_task(self, labels = "main", inputs=None, task_name=None, conditional=None)->MastSequenceTask:
        # if single label no need for any
        if not isinstance(labels, list):
            return self.start_task(labels, inputs, task_name)

        seq_task = MastSequenceTask(self, labels, conditional)    
        t = self._start_task(labels[0], inputs, None)
        t.jump(labels[0])
        seq_task.task = t

        #self.on_start_task(t)
        self.tasks.append(seq_task)
        if task_name is not None:
            self.active_task.set_value(task_name, seq_task, Scope.NORMAL)
        return seq_task

    def start_fallback_task(self, labels = "main", inputs=None, task_name=None, conditional=None)->MastFallbackTask:
        # if single label no need for any
        if not isinstance(labels, list):
            return self.start_task(labels, inputs, task_name)

        seq_task = MastFallbackTask(self, labels, conditional)    
        t = self._start_task(labels[0], inputs, None)
        t.jump(labels[0])
        seq_task.task = t

        #self.on_start_task(t)
        self.tasks.append(seq_task)
        if task_name is not None:
            self.active_task.set_value(task_name, seq_task, Scope.NORMAL)
        return seq_task


    def _start_task(self, label = "main", inputs=None, task_name=None)->MastAsyncTask:
        if self.inputs is None:
            self.inputs = inputs

        # if self.mast and self.mast.labels.get(label,  None) is None:
        #     raise Exception(f"Calling undefined label {label}")
        t= MastAsyncTask(self, inputs)
        return t


    def start_task(self, label = "main", inputs=None, task_name=None)->MastAsyncTask:
        t = self._start_task(label, inputs, task_name)
        if task_name is not None:
            t.set_value(task_name, t, Scope.NORMAL)
        t.jump(label)
        self.tasks.append(t)
        self.on_start_task(t)
        return t

    def on_start_task(self, t):
        self.active_task = t
        t.tick()
    def cancel_task(self, name):
        if isinstance(name, str):
            data = self.active_task.get_variable(name)
        else:
            data = name
        # Assuming its OK to cancel none
        if data is not None:
            self.done.append(data)

    def is_running(self):
        if len(self.tasks) == 0:
            return False
        return True

    def get_value(self, key, defa=None):
        val = Mast.globals.get(key, None)
        if val is not None:
            return (val, Scope.SHARED)
        #val = self.mast.vars.get(key, None)
        val = Agent.SHARED.get_inventory_value(key, None)
        if val is not None:
            return (val, Scope.SHARED)
        #val = self.vars.get(key, defa)
        val = self.get_inventory_value(key, None)
        return (val, Scope.NORMAL)

    def get_variable(self, key):
        val = self.get_value(key)
        return val[0]
    
    def set_variable(self, key):
        val = self.get_value(key)
        return val[0]

    def tick(self):
        restore = FrameContext.task
        for task in self.tasks:
            self.active_task = task
            FrameContext.task = task
            
            res = task.tick()
            FrameContext.task = None
            if res == PollResults.OK_END:
                self.done.append(task)
            elif task.done:
                self.done.append(task)
        FrameContext.task = restore
        
        if len(self.done):
            for rem in self.done:
                if rem in self.tasks:
                    self.tasks.remove(rem)
            self.done = []

        if len(self.tasks):
            return True
        else:
            return False

