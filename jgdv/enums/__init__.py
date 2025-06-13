"""
Some Enum's I Keep writing
"""
import enum

class LoopControl_e(enum.Enum):
    """
      Describes how to continue an accumulating loop.
      (like walking a a tree)

    yesAnd     : is a result, and try others.
    yes        : is a result, don't try others, Finish.
    noBut      : not a result, try others.
    no         : not a result, don't try others, Finish.
    """
    yesAnd  = enum.auto()  # noqa: N815
    yes     = enum.auto()
    noBut   = enum.auto()  # noqa: N815
    no      = enum.auto()

    @classmethod
    def loop_yes_set(cls) -> set:
        return  {cls.yesAnd, cls.yes, True}

    @classmethod
    def loop_no_set(cls) -> set:
        return  {cls.no, cls.noBut, False, None}

class CurrentState_e(enum.Enum):
    """
      Enumeration of the different states a task can be in.
    """
    TEARDOWN        = enum.auto()
    SUCCESS         = enum.auto()
    FAILED          = enum.auto()
    HALTED          = enum.auto()
    WAIT            = enum.auto()
    READY           = enum.auto()
    RUNNING         = enum.auto()
    EXISTS          = enum.auto()
    INIT            = enum.auto()

    DEFINED         = enum.auto()
    DECLARED        = enum.auto()
    ARTIFACT        = enum.auto()

class ActionResult_e(enum.Enum):
    """
      Enums for how a task can describe its response
    """
    SUCCEED  = enum.auto()
    FAIL     = enum.auto()
    SKIP     = enum.auto()
    HALT     = enum.auto()

class TaskPolicyEnum(enum.Flag):
    """
      Combinable Policy Types:
      breaker  : fails fast
      bulkhead : limits extent of problem and continues
      retry    : trys to do the action again to see if its resolved
      timeout  : waits then fails
      cache    : reuses old results
      fallback : uses defined alternatives
      cleanup  : uses defined cleanup actions
      debug    : triggers pdb
      pretend  : pretend everything went fine
      accept   : accept the failure

      breaker will overrule bulkhead
    """
    BREAKER  = enum.auto()
    BULKHEAD = enum.auto()
    RETRY    = enum.auto()
    TIMEOUT  = enum.auto()
    CACHE    = enum.auto()
    FALLBACK = enum.auto()
    CLEANUP  = enum.auto()
    DEBUG    = enum.auto()
    PRETEND  = enum.auto()
    ACCEPT   = enum.auto()
