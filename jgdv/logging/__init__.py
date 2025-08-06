"""
:class:`JGDVLogConfig<jgdv.logging.config.JGDVLogConfig>` provides a single config point for logging,
both to files and stdout/error. The Log Config is a singleton.

Different loggers can be configured using ``TOML``,
which is parsed into the structure :class:`LoggerSpec<jgdv.logging.logger_spec.LoggerSpec>`.

The module also provides some logging extensions:

- :class:`JGDVLogger<jgdv.logging.logger.JGDVLogger>`
- :class:`JGDVLogRecord<jgdv.logging.record.JGDVLogRecord>`
- :class:`LogCall<jgdv.logging.decorators.LogCall>`, a decorator.

"""

from ._interface import LogLevel_e
from .config import JGDVLogConfig
