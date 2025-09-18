from jgdv.debugging.timing import TimeDec


@TimeDec()
def basic():
    time.sleep(10)

basic()
