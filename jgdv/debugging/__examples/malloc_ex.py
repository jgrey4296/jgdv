from jgdv.debugging import MallocTool

with MallocTool(frame_count=1) as dm:
    dm.whitelist(__file__)
    dm.blacklist("*.venv")
    val = 2
    dm.snapshot("before")
    vals = [random.random() for x in range(1000)]
    a_dict = {"blah": 23, "bloo": set([1,2,3,4])}
    dm.snapshot("after")
    empty_dict = {"basic": [10, 20]}
    vals = None
    dm.snapshot("cleared")

dm.compare("before", "after", filter=True, fullpath=False)
