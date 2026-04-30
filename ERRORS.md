## [2026-04-30 20:37] - Tokenizer Inspection Stdout Encoding Failure

- **Type**: Process
- **Severity**: Low
- **File**: `scripts/:1`
- **Agent**: Codex
- **Root Cause**: A temporary inspection command printed Unicode comments/docstrings through the Windows cp1252 stdout encoder, which cannot encode some characters.
- **Error Message**:
  ```
  UnicodeEncodeError: 'charmap' codec can't encode characters in position 17-18: character maps to <undefined>
  ```
- **Fix Applied**: Re-ran the inspection with `PYTHONIOENCODING=utf-8`; no project files were modified by the failed command.
- **Prevention**: Set UTF-8 output when running ad hoc Python inspection commands that print Unicode on Windows.
- **Status**: Fixed

---
