# Error Log

## [2026-04-29 22:32] - Generate Failed on Console Encoding

- **Type**: Process
- **Severity**: Medium
- **File**: `scripts/generate_data.py:215`
- **Agent**: Codex
- **Root Cause**: Python ran under a Windows console encoding (`cp1252`) that could not encode emoji output from the generation script before scanning books.
- **Error Message**:
  ```
  UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4c2' in position 2: character maps to <undefined>
  ```
- **Fix Applied**: Re-run the generation command with `PYTHONIOENCODING=utf-8` so script output can be encoded correctly.
- **Prevention**: Set UTF-8 output encoding for Python automation commands that print Unicode symbols on Windows.
- **Status**: Fixed

---
