from typing import Protocol
from jgdv.decorators import Proto

class MyProto_p(Protocol): ...


# Instead of:
class MyInstance(MyProto_p): ...

# This:
@Proto(MyProto_p)
class MyInstance2: ...
