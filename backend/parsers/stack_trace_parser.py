"""
Stack trace frame extraction for Java, Python, Node.js, and Go runtimes.
Each parser returns a list of StackFrame objects from a raw block of text.
"""

import re
import os
from models.schemas import StackFrame

# ── Java ──────────────────────────────────────────────────────────────────────
# at com.example.service.UserService.processUser(UserService.java:42)
# at com.example.Main.<init>(Main.java:10)
JAVA_FRAME = re.compile(
    r"\s+at\s+([\w$.<>]+)\.([\w$<>]+)\s*\(([\w$]+\.(?:java|kt|groovy|scala)):(\d+)\)"
)

# ── Python ────────────────────────────────────────────────────────────────────
# File "/path/to/module.py", line 42, in function_name
PYTHON_FRAME = re.compile(
    r'\s+File\s+"([^"]+\.py)",\s+line\s+(\d+),\s+in\s+([\w<>]+)'
)

# ── Node.js / TypeScript ──────────────────────────────────────────────────────
# at FunctionName (path/to/file.js:42:15)
# at path/to/file.js:42:15
NODE_FRAME = re.compile(
    r"\s+at\s+(?:([\w.]+(?:\s+\[as\s+\w+\])?)\s+)?\(?([^()]+\.(?:js|ts|mjs|cjs)):(\d+):\d+\)?"
)

# ── Go ────────────────────────────────────────────────────────────────────────
# /path/to/file.go:42 +0x...
GO_FRAME = re.compile(r"([/\w._-]+\.go):(\d+)\s+\+0x")


def _basename(path: str) -> str:
    return os.path.basename(path.replace("\\", "/"))


def parse_stack_frames(text: str) -> list[StackFrame]:
    """
    Detect the runtime from the text and extract all stack frames.
    Returns the innermost (most application-specific) frames first.
    """
    frames: list[StackFrame] = []

    # Java / Kotlin / Groovy
    java_hits = JAVA_FRAME.findall(text)
    if java_hits:
        for class_name, method, file, line in java_hits:
            frames.append(StackFrame(
                class_name=class_name,
                method=method,
                file=file,
                line=int(line)
            ))
        return _filter_app_frames(frames)

    # Python
    python_hits = PYTHON_FRAME.findall(text)
    if python_hits:
        for filepath, line, func in python_hits:
            frames.append(StackFrame(
                class_name="",
                method=func,
                file=_basename(filepath),
                line=int(line)
            ))
        return frames

    # Node.js
    node_hits = NODE_FRAME.findall(text)
    if node_hits:
        for func, filepath, line in node_hits:
            base = _basename(filepath)
            # Skip internal Node modules
            if filepath.startswith("node:") or "node_modules" in filepath:
                continue
            frames.append(StackFrame(
                class_name="",
                method=func.strip(),
                file=base,
                line=int(line)
            ))
        return frames

    # Go
    go_hits = GO_FRAME.findall(text)
    if go_hits:
        for filepath, line in go_hits:
            frames.append(StackFrame(
                class_name="",
                method="",
                file=_basename(filepath),
                line=int(line)
            ))
        return frames

    return frames


def _filter_app_frames(frames: list[StackFrame]) -> list[StackFrame]:
    """
    Prefer user application frames over standard-library / framework frames.
    Heuristic: skip frames whose class starts with known stdlib prefixes.
    """
    STDLIB_PREFIXES = (
        "java.", "javax.", "sun.", "com.sun.", "jdk.",
        "org.springframework.", "org.hibernate.",
        "org.apache.catalina.", "org.apache.tomcat.",
        "org.junit.", "org.mockito.",
        "kotlin.", "groovy.",
        "scala.",
    )
    app_frames = [
        f for f in frames
        if not any(f.class_name.startswith(p) for p in STDLIB_PREFIXES)
    ]
    return app_frames if app_frames else frames
