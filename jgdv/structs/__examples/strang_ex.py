from jgdv.structs.strang import Strang

example : Strang = Strang("head.meta.data::tail.value")
# Regular string index access:
example[0] == "h"
example[0:4] == "he"
# Section access:
example[0,:] == "head.meta.data"
example[1,:] == "tail.value"
example[0,0] == "head"
example[1,0] == "tail"
