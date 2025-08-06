"""


"""
from __future__ import annotations

# Import:
from typing import Final
from jgdv.debugging import TraceBuilder
from jgdv._abstract.error import JGDVError

##--| Error Messages
MissingSectionName              : Final[str]  = "{cls} has no section {key}"
MissingSectionIndex             : Final[str]  = "{cls} has no section {idx}, only {sections}"
SliceMisMatch                   : Final[str]  = "Mismatch between section slices and word slices"
UnkownSlice                     : Final[str]  = "Slice Logic Failed"
IndexOfEmptyStr                 : Final[str]  = "Tried to Index the empty str"
MalformedData                   : Final[str]  = "Base data malformed"
TooManyUUIDs                    : Final[str]  = "More than One UUID found"
NoUUIDToDiff                    : Final[str]  = "Tried to diff a uuid with a non-uniq strang"
StrangCtorFailure               : Final[str]  = "[{cls}] Stage: {stage}"
CodeRefImportFailed             : Final[str]  = "Attempted import failed, attribute not found"
CodeRefImportNotCallable        : Final[str]  = "Imported 'Function' was not a callable"
CodeRefImportNotClass           : Final[str]  = "Imported 'Class' was not a type"
CodeRefImportCheckFail          : Final[str]  = "Imported Value does not match required type"
CodeRefImportUnknownFail        : Final[str]  = "Imported Code Reference is not of correct type"
CodeRefImportNotValue           : Final[str]  = "Imported Code Reference is not a value"
CodeRefUUIDFail                 : Final[str]  = "Code References shouldn't need UUIDs"

FormatterExpansionTypeFail      : Final[str]  = "Unrecognized expansion type"
FormatterConversionUnknownSpec  : Final[str]  = "Unknown conversion specifier {spec!s}"
FormatterUnkownBodyType         : Final[str]  = "Unknown body type"

NoSkipMark                      : Final[str]  = "Can't push without a skip mark in the last section"


##--| Error Classes
class StrangError(JGDVError):
    """ The Base Error type that Strang's raise """
    pass
