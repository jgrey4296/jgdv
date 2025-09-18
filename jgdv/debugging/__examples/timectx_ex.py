from jgdv.debugging.timing import TimeCtx

with TimeCtx() as obj:
    some_func()

logging.info("The Function took: %s seconds", obj.total_s)
