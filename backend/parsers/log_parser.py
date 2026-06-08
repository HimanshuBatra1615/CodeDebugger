
import re
from models.schemas import ParsedLogError, StackFrame
from parsers.stack_trace_parser import parse_stack_frames

TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}"
)

LEVEL_RE = re.compile(
    r"\b(ERROR|FATAL|CRITICAL|WARN(?:ING)?|INFO|DEBUG|TRACE)\b", re.I
)

TS_EXTRACT = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)"
)

EXCEPTION_RE = re.compile(
    r"^([A-Za-z][\w.]*(?:Exception|Error|Fault|Panic|Throwable))[:\s]+(.*)",
    re.M
)

TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\):", re.I)

ERROR_LEVELS = {"ERROR", "FATAL", "CRITICAL"}



def parse_log_file(content: str) -> list[ParsedLogError]:

    blocks = _split_into_blocks(content)
    errors: list[ParsedLogError] = []

    for block in blocks:
        entry = _parse_block(block)
        if entry and entry.level.upper() in ERROR_LEVELS:
            errors.append(entry)

    return errors



def _split_into_blocks(content: str) -> list[str]:

    lines = content.splitlines()
    blocks: list[str] = []
    current: list[str] = []

    for line in lines:

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
            if current:           
                current.append(line)
            elif line.strip():   
                current = [line]

    if current:
        blocks.append("\n".join(current))

    return [b.strip() for b in blocks if b.strip()]


def _parse_block(block: str) -> ParsedLogError | None:

    lines = block.splitlines()
    if not lines:
        return None

    header = lines[0]

    level_match = LEVEL_RE.search(header)
    if not level_match:
        if TRACEBACK_RE.match(header):
            level = "ERROR"
        else:
            level = "ERROR"  
    else:
        level = level_match.group(1).upper()
        if level == "WARNING":
            level = "WARN"

    ts_match = TS_EXTRACT.match(header)
    timestamp = ts_match.group(1) if ts_match else None

    exception_type = "UnknownError"
    message = header

    exc_match = EXCEPTION_RE.search(block)
    if exc_match:
        exception_type = exc_match.group(1).split(".")[-1]  # short name
        message = exc_match.group(2).strip() or header
    else:
        msg = TIMESTAMP_RE.sub("", header)
        msg = LEVEL_RE.sub("", msg)
        msg = re.sub(r"[-\[\]|:]+", " ", msg).strip()
        if msg:
            message = msg

    frames = parse_stack_frames(block)

    return ParsedLogError(
        level=level,
        message=message[:300],      
        exception_type=exception_type,
        stack_frames=frames,
        raw_text=block[:2000],
        timestamp=timestamp,
    )
