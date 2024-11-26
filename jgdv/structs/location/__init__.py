"""
A module for working with locations.
Provides two main classes:
Location, like an extended pathlib.Path
JGDVLocations, a mapping of names to locations

"""
from .location import LocationMeta_f, Location
from .errors import LocationError, LocationExpansionError, DirAbsent
from .locations import JGDVLocations
