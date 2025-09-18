
from jgdv.struct.chainguard import ChainGuard

data = ChainGuard.load("some.toml")
# Normal key access
data['key'] == "value"
# Key attributes
data.key == "value"
# Chained key attributes
data.table.sub.key == "blah"
# Failable keys
data.on_fail(2).table.sub.key() == "blah"
data.on_fail(2).table.sub.bad_key() == 2
