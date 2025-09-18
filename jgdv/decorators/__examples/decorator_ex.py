
from jgdv.decorators import Decorator

class MyDecorator(Decorator):

    def _wrap_fn_h[**In](self, fn:Func[In, int]) -> Decorated[In, int|None]:

        def myfunc(*vals:In.args) -> int|None:
            if bool(vals[0]):
                return fn(*vals)
            return None

        return myfunc


@MyDecorator()
def a_func(val:int) -> int:
        return 2

assert(a_func(0) is None)
assert(a_func(5) is 2)
