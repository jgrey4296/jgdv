"""
DKey, a str extension for doing things with str format expansion::

    a_key             = DKey("{blah}")
    some_data         = {"blah": "bloo")
    a_key(some_data)  == "bloo"

DKey's manage things such as redirection::

    redirect_key             = DKey("{blah_}")
    some_data                = {"blah_": "bloo", "bloo": "aweg"}
    redirect_key(some_data)  == "aweg"

Also treating input data as a chainmap::

    a_key                  = DKey("{blah}")
    data_1                 = {"not_blah"  : "bloo"}
    data_2                 = {"blah"      : "aweg"}
    a_key(data_1, data_2)  == "aweg"

DKey can also handle multi subkey expansion::

    a_multikey        = DKey("{blah} : {bloo}")
    data              = {"blah": "aweg", "bloo": "qqqq"}
    a_multikey(data)  == "aweg  : qqqq"

"""
from ._interface      import Key_p, DKeyMark_e
from ._util._interface import ExpInst_d
from .errors          import DKeyError
from .dkey            import DKey
from ._util.decorator import DKeyed, DKeyExpansionDecorator

from .keys import SingleDKey, MultiDKey, NonDKey, IndirectDKey

from .special.import_key     import ImportDKey
from .special.args_keys      import ArgsDKey, KwargsDKey
from .special.str_key        import StrDKey
from .special.path_key       import PathDKey
