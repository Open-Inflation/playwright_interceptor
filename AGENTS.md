# Project Guidelines

- Always fix the underlying problem instead of masking it with a try block. If a fix is impossible, leave the behavior as is and clearly describe what does not work, why, and what was attempted.
- Keep modules focused. A new feature should live in its own file to avoid overloading existing ones.
- Browser engines and their configs are stored in `browser_engines.py`.
- Engine configs are passed to `BaseAPI` by calling `BrowserEngine.NAME(**options)`.

