
from pathlib import Path
from jgdv.structs.chainguard import ChainGuard
from jgdv.logging import JGDVLogConfig

data    = ChainGuard.load(Path("data/specs.toml"))
config  = JGDVLogConfig()
config.setup(data)
config.set_level("DEBUG")
