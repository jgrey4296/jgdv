from jgdv.debugging.trace_context import TraceContext

obj = TraceContext(targets=("call", "line", "return"),
                   targets=("trace","call","called"))
with obj:
        other.do_something()

obj.assert_called("package.module.class.method")
