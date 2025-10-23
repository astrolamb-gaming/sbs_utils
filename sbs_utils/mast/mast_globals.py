from .. import faces, scatter
import math
import itertools
import logging
import random
from .. import fs
import sys
from inspect import getmembers, isfunction

import builtins as __builtin__
from ..helpers import FrameContext
def mast_print(*args, use_mast_scope=True, **kwargs):
    task = FrameContext.task 
    if use_mast_scope and len(args)==1 and task is not None:
        return __builtin__.print(task.compile_and_format_string(args[0]))
    #    args[0] = ">>>"+args[0]
    return __builtin__.print(*args, **kwargs)


class MastGlobals:
    globals = {
        "math": math, 
        "faces": faces,
        "scatter": scatter,
        "random": random,
        "print": mast_print, 
        "dir":dir, 
        "itertools": itertools,
        "next": next,
        "len": len,
        "reversed": reversed,
        "int": int,
        "str": str,
        "hex": hex,
        "min": min,
        "max": max,
        "abs": abs,
        "sim": None,
        "map": map,
        "filter": filter,
        "list": list,
        "set": set,
        "iter": iter,
        "sorted": sorted,
        "mission_dir": fs.get_mission_dir(),
        "data_dir": fs.get_artemis_data_dir(),
        #"MastDataObject": MastDataObject,
        "range": range,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
        "__build_class__":__build_class__, # ability to define classes
        "__name__":__name__ # needed to define classes?
    }

    def import_python_function(func, name=None):
        """
        Import a python function as a global and optionally specify a name for it.
        Args:
            func (Callable): The python function
            name (str|None): The name assinged to the function (optional, default is None).
        """
        if name:
            MastGlobals.globals[name] = func
        else:
            MastGlobals.globals[func.__name__] = func
        

    def import_python_module(mod_name, prepend=None):
        """
        Import all functions within a python module as globals and optionally add a prepend to the function names.
        For example, the functions in the `scatter` module are added as global functions with 'scatter' prepended to the name like so:
        ```python
        MastGlobals.import_python_module('sbs_utils.scatter', 'scatter')
        ```
        This allows the functions in the scatter module to be called, e.g. `scatter_arc(...args)`
        Args:
            mod_name (str): The name of the module
            prepend (str): The string to prepend to the function names
        """
        from importlib import import_module
        sca = sys.modules.get(mod_name)
        if sca is None:
            sca = import_module(mod_name)
        if sca:
            for (name, func) in getmembers(sca,isfunction):
                if prepend == None:
                    MastGlobals.globals[name] = func
                elif prepend == True:
                    MastGlobals.globals[f"{mod_name}_{name}"] = func
                elif isinstance(prepend, str):
                    MastGlobals.globals[f"{prepend}_{name}"] = func


