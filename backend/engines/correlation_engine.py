
import os
import difflib
from models.schemas import ParsedLogError, CorrelatedError
from parsers.code_reader import CodeIndex

CONTEXT_WINDOW = 8



def correlate_errors(
    log_errors: list[ParsedLogError],
    code_index: CodeIndex
) -> list[CorrelatedError]:

    results: list[CorrelatedError] = []
    seen: set[str] = set()         

    for error in log_errors:
        if not error.stack_frames:
            continue

        for frame in error.stack_frames:
            match = _find_source_file(frame.file, code_index)
            if match is None:
                continue

            source_path, source_content = match
            key = f"{source_path}:{frame.line}"
            if key in seen:
                continue
            seen.add(key)

            context = _extract_context(source_content, frame.line)
            language = code_index.language_map.get(source_path, "Unknown")

            results.append(CorrelatedError(
                error=error,
                source_file=os.path.basename(source_path),
                line=frame.line,
                method=frame.method,
                code_context=context,
                language=language,
            ))
            break   

    return results



def _find_source_file(
    target: str,
    code_index: CodeIndex
) -> tuple[str, str] | None:

    target_base = os.path.basename(target).lower()
    file_paths = list(code_index.files.keys())

    for path in file_paths:
        if os.path.basename(path).lower() == target_base:
            return path, code_index.files[path]

    basenames = [os.path.basename(p).lower() for p in file_paths]
    close = difflib.get_close_matches(target_base, basenames, n=1, cutoff=0.70)
    if close:
        for path in file_paths:
            if os.path.basename(path).lower() == close[0]:
                return path, code_index.files[path]

    close_path = difflib.get_close_matches(target.lower(), [p.lower() for p in file_paths], n=1, cutoff=0.50)
    if close_path:
        for path in file_paths:
            if path.lower() == close_path[0]:
                return path, code_index.files[path]

    return None


def _extract_context(content: str, error_line: int) -> str:

    lines = content.splitlines()
    total = len(lines)
    if total == 0:
        return "(empty file)"

    effective = min(error_line, total)
    start = max(0, effective - CONTEXT_WINDOW - 1)
    end   = min(total, effective + CONTEXT_WINDOW)
    if start >= end:
        start, end = max(0, total - CONTEXT_WINDOW * 2), total

    snippet: list[str] = []
    for i in range(start, end):
        lineno = i + 1
        is_err = (lineno == error_line) or (error_line > total and lineno == end)
        marker = "→" if is_err else " "
        snippet.append(f"{lineno:5d} {marker}  {lines[i]}")

    if error_line > total:
        snippet.append(f"       (note: error line {error_line} beyond file length {total})")

    return "\n".join(snippet)
