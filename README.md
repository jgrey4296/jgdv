# Deja Vu

Author: John Grey
Date  : 2024-03-04

## Overview
I keep writing these things.

## Examples

### ChainGuard

With Toml Data:

```toml

   key = "value"
   [table]
   key = "other value"
   sub = {key="blah"}
```

```python

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

```


### Strang

```python

example : Strang = Strang("head.meta.data::tail.value")
# Regular string index access:
example[0] == "h"
example[0:4] == "he"
# Section access:
example[0,:] == "head.meta.data"
example[1,:] == "tail.value"
example[0,0] == "head"
example[1,0] == "tail"
```
