"""
Log file parser.  Splits a raw log into error blocks and extracts:
  - log level (ERROR / FATAL / WARN / CRITICAL)
  - timestamp
  - exception type and message
  - stack frames (via stack_trace_parser)

Supports:
  Java Log4j   : 2024-01-01 10:00:00,000 ERROR [logger] - message
  Java Logback : 2024-01-01 10:00:00.000 ERROR 1234 --- [thread] pkg : message
  Python       : 2024-01-01 10:00:00,000 ERROR logger: message
  Python TB    : Traceback (most recent call last): ...
  Node.js      : Error: message \n    at ...
  Generic      : any line containing ERROR/FATAL/CRITICAL
"""

import re
from models.schemas import ParsedLogError, StackFrame
from parsers.stack_trace_parser import parse_stack_frames

# ── Patterns ─────────────────────────────────────────────────────────────────

# Matches any common log timestamp prefix
TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}"
)

# Extracts log level anywhere in a line
LEVEL_RE = re.compile(
    r"\b(ERROR|FATAL|CRITICAL|WARN(?:ING)?|INFO|DEBUG|TRACE)\b", re.I
)

# Extracts timestamp from the beginning of a line
TS_EXTRACT = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)"
)

# Java / Python exception class: "SomeException: message"
EXCEPTION_RE = re.compile(
    r"^([A-Za-z][\w.]*(?:Exception|Error|Fault|Panic|Throwable))[:\s]+(.*)",
    re.M
)

# Python Traceback header
TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\):", re.I)

# Levels that mean we definitely care
ERROR_LEVELS = {"ERROR", "FATAL", "CRITICAL"}


# ── Public API ────────────────────────────────────────────────────────────────

def parse_log_file(content: str) -> list[ParsedLogError]:
    """
    Parse a full log file and return only error-level entries.
    """
    blocks = _split_into_blocks(content)
    errors: list[ParsedLogError] = []

    for block in blocks:
        entry = _parse_block(block)
        if entry and entry.level.upper() in ERROR_LEVELS:
            errors.append(entry)

    return errors


# ── Internal helpers ──────────────────────────────────────────────────────────

def _split_into_blocks(content: str) -> list[str]:
    """
    Split log content into logical blocks.  A new block begins when:
      1. We see a timestamped line that also contains a log level, OR
      2. We see a Python "Traceback" header, OR
      3. We see a bare "Error:" / exception header (Node.js style)
    Lines that continue the previous entry (stack frames, context) are
    appended to the current block.
    """
    lines = content.splitlines()
    blocks: list[str] = []
    current: list[str] = []

    for line in lines:
        # A new block begins only at a timestamped log line or a Python traceback.
        # Exception-class lines (e.g. "NullPointerException: …") must NOT start a
        # new block — they are continuation lines that belong to the preceding entry.
        is_new_entry = (
            (TIMESTAMP_RE.match(line) and bool(LEVEL_RE.search(line)))
            or bool(TRACEBACK_RE.match(line))
        )

        if is_new_entry and current:
            blocks.append("\n".join(current))
            current = [line]
        elif is_new_entry:
            current = [line]
        else:
            if current:           # continuation line
                current.append(line)
            elif line.strip():    # orphan line with content
                current = [line]

    if current:
        blocks.append("\n".join(current))

    return [b.strip() for b in blocks if b.strip()]


def _parse_block(block: str) -> ParsedLogError | None:
    """
    Extract a ParsedLogError from a single log block.
    Returns None if the block doesn't represent an error.
    """
    lines = block.splitlines()
    if not lines:
        return None

    header = lines[0]

    # ── Level ─────────────────────────────────────────────────────────────────
    level_match = LEVEL_RE.search(header)
    if not level_match:
        # Try Python traceback: level is on the last line (e.g. "KeyError: 'name'")
        if TRACEBACK_RE.match(header):
            level = "ERROR"
        else:
            level = "ERROR"   # treat unlabelled exception lines as ERROR
    else:
        level = level_match.group(1).upper()
        if level == "WARNING":
            level = "WARN"

    # ── Timestamp ─────────────────────────────────────────────────────────────
    ts_match = TS_EXTRACT.match(header)
    timestamp = ts_match.group(1) if ts_match else None

    # ── Exception type & message ───────────────────────────────────────────────
    exception_type = "UnknownError"
    message = header

    exc_match = EXCEPTION_RE.search(block)
    if exc_match:
        exception_type = exc_match.group(1).split(".")[-1]  # short name
        message = exc_match.group(2).strip() or header
    else:
        # Strip timestamp and level prefix to get the message
        msg = TIMESTAMP_RE.sub("", header)
        msg = LEVEL_RE.sub("", msg)
        msg = re.sub(r"[-\[\]|:]+", " ", msg).strip()
        if msg:
            message = msg

    # ── Stack frames ──────────────────────────────────────────────────────────
    frames = parse_stack_frames(block)

    return ParsedLogError(
        level=level,
        message=message[:300],       # truncate very long messages
        exception_type=exception_type,
        stack_frames=frames,
        raw_text=block[:2000],
        timestamp=timestamp,
    )
