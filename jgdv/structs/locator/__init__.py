"""
Locator provides a key->Location store,
where a Location is a path+metadata specialization of Strang

"""

from ._interface import Location_p, Locator_p
from .location import Location
from .locator import JGDVLocator
