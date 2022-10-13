from sbs_utils.mast.mast import Mast
from sbs_utils.mast.maststory import MastStory, ButtonControl
import unittest

Mast.enable_logging()


def mast_story_compile(code=None):
    def decorator(func):
        def wrapper(self, **kargs):
            mast = MastStory()
            errors = mast.compile(code)
            func(self, errors=errors, mast=mast, **kargs)
        return wrapper
    return decorator

def mast_story_compile_file(code=None):
    mast = MastStory()
    errors = mast.from_file(code)
    return (errors, mast)



class TestMastStoryCompile(unittest.TestCase):
    
    @mast_story_compile( code = """
await choice nothing

await choice timeout 1m 1s
    * "Button one"
        -> JumpLabel
    + "Button Two"
        -> JumpLabel
    + "Button Jump" 
    timeout
        -> JumpSomeWhere
end_await


await choice
* "Button one"
    await self comms player
    * "Button one"
        await self comms player
        * "Button one"
            -> JumpLabel
        end_await
    end_await
end_await


""")
    def test_compile_no_err(self, errors, mast):
        if len(errors)>0:
            for err in errors:
                print(err)
        assert(len(errors) == 0)

    
    def test_compile_file_ttt(self):
        (errors, mast) = mast_story_compile_file( code ="tests/mast/ttt.mast")     
        if len(errors)>0:
            for err in errors:
                print(err)
        assert(len(errors) == 0)


if __name__ == '__main__':
    try:
        unittest.main(exit=False)
    except Exception as e:
        print(e.msg)

"""
    Comment,
    Label,
    IfStatements,
InlineLabelStart,
InlineLabelEnd,
InlineLabelBreak,
    PyCode,
Input,
Import,
    Await,  # needs to be before Parallel
    Parallel,  # needs to be before Assign
Cancel,
    Assign,
    End,
    Jump,
    Delay,
"""
