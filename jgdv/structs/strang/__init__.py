"""
Strang, a Structured String class.

Strangs are str's, and can be used as str's.
But they validate their format, and allow access to sub parts. eg::

    v = Strang("group::body.name")
    v[0:] == "group"
    v[1:] == "body.name"
    v[1:0] == "body"
    v[1:1] == "name"

There is also a specialized strang CodeReference.
for easily importing code::

    v = CodeReference("fn::jgdv.identity_fn")
    assert(callable(v()))
    assert(v() == jgdv.identity_fn)

"""

from ._interface import Strang_p, Importable_p
from .strang import Strang
from .code_ref import CodeReference
from .errors import StrangError
