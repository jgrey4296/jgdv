# Changelog

All notable changes to this project will be documented in this file.

<!-- towncrier release notes start -->

# Jgdv 1.3.0 (2025-08-14)

No significant changes.


## [1.2.0] - 2025-06-15
(Generated using [git-cliff](https://git-cliff.org/)

### Features

- Bumpver target for docs conf.py
- Param parse tests
- Stdlib protocols
- Tests for sec_d
- Strang subclass tests
- Strang args
- SubAlias_m
- Dkey expansion control
- Sourcechain_d tests
- Literalparam to core
- Unwrapping of genericaliases for paramspecs
- Param builder mixin tests

### Bug Fixes

- Positional param parsing
- Strang hashing
- Codereference.from_value
- Type coercion in dkey
- Dkey empty str building

### Dependencies

- Version 1.1.0 -> 1.2.0

### Refactoring

- Decorators module
- Cli tests
- Errors module
- Dkey module
- Strang module
- Strang typing
- Decorators typing
- Dkey typing
- Locator typing
- Decorator interface
- Chainguard typing
- Strang creation and typing
- Strang processing and access
- Decorators to use __annotations__
- Simplify initial processing
- Annotate mixin
- Coderef to pass tests
- Dkey
- Annotation subclass naming
- Dkey
- Decorator typing
- Preprocessable_p to _abstract
- Dkey
- Dkey to be a strang
- Obsolete dkey formatter
- Strang_i
- Dkey
- Locator
- Dkey
- Locator
- Decorator auto build
- Merge branch 'refactor.strang'
- Dkey.specialised -> dkey.special
- Strang to use SubAlias_m
- Mixins.annotate
- Subalias
- Dkey marks
- Dkey expansion
- Pathy
- Logging config
- Cli.param_spec
- Cli param building and parsing
- Dkey marks
- Strang slicing to util class

## [1.1.0] - 2025-04-23

### Features

- @Mixin appends by default now
- Subfile can be updated with (key, [subs])
- Logdel
- Human numbers test
- Malloc tool
- Debugging test stubs
- Dkey.var_name for signature checking
- Null handler for interrupt
- Merge branch 'refactor.logging'

### Bug Fixes

- Logging setup mistakes
- Subclasser module default
- Coderef usage
- Tests for validating signatures
- Don't keep generated autoapi files

### Dependencies

- Version 1.0.1 -> 1.1.0

### Refactoring

- Types
- Time_ctx
- Timing ctx managers
- Decorator typing
- Tracktime decorator to timeblock_ctx
- Structs.regex -> rxmatcher
- Pathy import guard to __init__
- Timeblock_ctx entry/exit_msg -> enter/exit
- Sub file
- Log colour setup
- Logging filters/formatters
- Jinja templates for autoapi
- Rst files to src tree
- Errors submodule
- Types into _abstract
- Doc templates
- Move all doc files into src tree
- Docs -> jgdv/_docs/

### Testing

- Path key
- Param spec short consume

## [1.0.1] - 2025-03-02

### Bug Fixes

- Bad import

### Dependencies

- Version 1.0.0 -> 1.0.1

## [1.0.0] - 2025-03-01

### Features

- Sub_many fn
- Safe_import to coderef
- Tagfile comments
- Failhandler_p
- Zip/compression mixin
- Trace helper
- Branch 'feature.guarded_chain'
- Initial key code
- Initial location code
- Initial str struct name
- Initial locations pass
- Debugging signal handler and trace builder
- Strang functionality
- Add Strang annotations
- Branch 'feature.strang'
- Strict preprocessing for strangs
- Initial cli code
- Param spec
- Param spec type annotation
- Param spec subclasses
- Branch 'features.cli'
- Basic Location implementation
- Enum mixin and bump to py3.12
- 312 types
- Pathy
- Type aliases
- Pathy joining
- Pathy contain, format, expand
- Pathy time comparison
- Pathy walking
- Branch 'feature.312'
- Verstr and lambda types
- Paramspec type tests
- Stackprinter to formatting
- Multi enum checking for locations
- Additional errors for cli parsing
- Chainguard fallback(none) test
- Prelude
- Logging decorators
- Logger extension
- Log spec as bool
- Mut/NoMut types
- Tests for core dkeys
- Prefer local expansion for dkeys
- Merge branch 'feature.alt.expander'
- Initial decorators code
- CheckProtocol
- @Mixin and @WithProto
- Merge branch 'features.decorators'
- Stdlib path refactor
- Positional matching for pathy
- Merge branch 'feature.pathy'
- Test for unexpected dkey args
- DKeyed add_sources method
- Dkey insistence
- Dkey extra kwargs for subclasses
- Release to conf
- Versioning tasks
- Custom templates
- Merge branch 'docs'
- Fallback factorys for dkey expansion
- Error traceback item control
- Traceback control in decorators
- @Mixin(..., allow_inheritance=bool, silent=bool)
- Todo tests
- Dkeyparser tests
- Class getitem to TraceBuilder
- Decorator __new__ and DoMaybe
- Plugin_selector
- Metalord stub
- Singleton
- Merge branch 'feature.metalord'
- Policy enum

### Bug Fixes

- Typo
- Typo
- Strang metaclass
- Tests
- Strang with_head behaviour
- Strang
- Oversights of refactor
- Chainguard to behave like dict for iter
- Param spec sorting
- Arg parsing forced help
- Arg parsing head --help
- Missing exc_info handling
- Positional params
- Dkeyformatter parse semantics
- Coercion bugs
- Location building
- Extra sources recursion
- DKeyed.redirects
- Forced multikeys
- Indirect key hashing
- Dkey expansion check
- Dkeyed.add_sources -> dkey.add_sources
- Import
- Imports
- Path mod
- Autoapi dir
- Typo and handling cached_property
- Param spec name parsing
- Indirect key expansion
- Key expansion conversion
- Logging
- Chainguard update mutability fail

### Dependencies

- Version 0.3.2 -> 1.0.0

### Refactoring

- Docs
- Branch 'docs' into linux-main
- Tagfile and substitutionfile
- Tags files
- Tag splitting into update method
- Coderef
- Remove mentions of doot from dkey
- Simplify import structure
- Location imports
- Decorator
- Decorators
- Decorators, with tests
- Time tracking decorator
- Struct str
- Strang to jgdv.structs.strang
- Codereference to use strang
- Locations to use Strang
- Post_process to be local to strang subtype
- Weakrefs in global locations store
- Obsolete name module
- Guarded_chain -> chainguard
- Tomlguard -> chainguard
- Strang format methods
- Location metadata
- Strang subclassing
- Arg parser
- Repl stub
- Uncecessary parts of argparser_p
- Param specs
- Parse machine to separate file
- Types
- Errors
- Logging to have style control
- Dkey decorator accessors to classmethods
- Jgdv formatters
- Locations expansion logic
- Dkey expansion
- Decorators
- Arg parsing to handle unordered args
- Errors
- Dkey
- Path expansion tests from strang to dkey
- Indirect key to core
- Base expansion
- Expansion class names, KeyMark
- Locations -> locator
- Expansion to use ExpInst
- Param_spec into module
- Obsolete
- Annotate
- Pathy types enum -> NewTypes
- Class decorators
- Key expansion
- DKey.ExpInst and DKey.Mark
- DKeyMark_e.REDIRECT and TASK
- DKeyed auto registration
- Decorator _mod_class -> _wrap_class
- Docs
- Doot build task
- Decorators
- Cli params
- @mixin and @proto
- Annotation naming
- Interface definitions
- ChainGuard interface
- Logging interface
- Files interface
- Cli interface
- ExpInst -> _interface.ExpInst_d
- Dkey module to have .core
- Strang interface
- Dkey

### [Merge]

- Branch 'linux-main'

## [0.3.2] - 2024-09-12

### Dependencies

- Version 0.3.1 -> 0.3.2

### Refactoring

- Unneeded dependencies

## [0.3.1] - 2024-09-06

### Bug Fixes

- Colour condition logic
- Typo

### Dependencies

- Version 0.3.0 -> 0.3.1

## [0.3.0] - 2024-09-06

### Features

- Extendable subprinters
- Branch 'linux-main'

### Bug Fixes

- Print children registration
- Log config typo
- Variable error
- Wrong condition ordering

### Dependencies

- Version 0.2.0 -> 0.3.0

### Refactoring

- Use of doot error

### [Merge]

- Branch 'linux-main'

## [0.2.0] - 2024-08-25

### Features

- Known tag method
- TimeCtx
- Protocols
- Basic code_ref tests
- Branch 'features.coderef' into linux-main
- Structured_name tests
- Initial colour, config and capture code
- Add and use logger spec
- Subprinter setup
- Branch 'features.logging' into linux-main

### Bug Fixes

- Tests

### Dependencies

- Version 0.1.3 -> 0.2.0

## [0.1.3] - 2024-05-31

### Features

- Decorators and human numbers
- Enums
- Tag files
- Bookmark files
- Logging context and filter
- Util chain_get and slice
- Pytest tempdir fixture
- Regex struct
- Factory protocol
- Branch 'cleanup' into linux-main
- Branch 'linux-main'
- More protocols
- Todo agenda
- Branch 'linux-main'

### Dependencies

- Changelog
- Version 0.1.2 -> 0.1.3

### Refactoring

- Remove mentions of doot
- Remove to re-add as branches
- Use pydantic for bookmarks/tags

## [0.1.2] - 2024-04-16

### Features

- Github publish workflow

### Bug Fixes

- Dependency
- Dependency

### Dependencies

- Version 0.1.0 -> 0.1.1
- Version 0.1.1 -> 0.1.2

## [0.1.0] - 2024-04-15

### Features

- Wiki as submodule
- Wiki as submodule

### Dependencies

- Version 0.0.1 -> 0.1.0

### Refactoring

- Naming to nominate package
- Structure
- Name

<!-- generated by git-cliff -->
