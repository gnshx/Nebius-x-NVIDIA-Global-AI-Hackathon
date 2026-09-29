# RepoMedic Demo — GitHub Issue Template

Copy this text when creating the demo issue on GitHub.

---

**Title:** `parse_user_id` crashes with `IndexError: list index out of range`

**Body:**

## Bug Report

### Description

The `parse_user_id` function in `src/utils.py` raises an `IndexError` for all valid inputs.

### Steps to Reproduce

```python
from src.utils import parse_user_id

result = parse_user_id("user-123")
# Raises: IndexError: list index out of range
```

### Expected Behavior

`parse_user_id("user-123")` should return `123`.

### Actual Behavior

```
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "src/utils.py", line 15, in parse_user_id
    return int(parts[1])
IndexError: list index out of range
```

### Test Output

```
FAILED tests/test_utils.py::TestParseUserId::test_basic_parse
FAILED tests/test_utils.py::TestParseUserId::test_single_digit
FAILED tests/test_utils.py::TestParseUserId::test_large_id
FAILED tests/test_utils.py::TestParseUserId::test_roundtrip
```

### Additional Context

The function appears to split on the wrong delimiter. The input format is `user-{id}` (hyphen-separated) but the implementation splits on space.

---

**To trigger RepoMedic:** Comment `/repomedic fix` on this issue.
