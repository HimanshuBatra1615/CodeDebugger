"""
Code reader.  Builds a CodeIndex from a dict of {filename: content} strings.

CodeIndex provides:
  - files        : {path: content}  (all readable source files)
  - language_map : {path: language} (detected language per file)
"""

import os
from dataclasses import dataclass, field

# ── Language detection by extension ──────────────────────────────────────────

EXT_TO_LANG: dict[str, str] = {
    ".java": "Java",
    ".kt": "Kotlin",
    ".groovy": "Groovy",
    ".scala": "Scala",
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".go": "Go",
    ".cs": "C#",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".dart": "Dart",
    ".jsx": "JavaScript (React)",
    ".tsx": "TypeScript (React)",
}

# Extensions we skip (binary, build artefacts, etc.)
SKIP_EXTENSIONS = {
    ".class", ".jar", ".war", ".ear",
    ".pyc", ".pyo", ".pyd",
    ".o", ".so", ".dll", ".exe", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".zip", ".tar", ".gz", ".7z",
    ".lock", ".sum",
}

# Directories we never recurse into
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".gradle",
    "build", "dist", "target", ".next", ".nuxt",
    "venv", ".venv", "env", ".env", "vendor",
}


@dataclass
class CodeIndex:
    files: dict[str, str] = field(default_factory=dict)
    language_map: dict[str, str] = field(default_factory=dict)


def build_code_index(raw_files: dict[str, str]) -> CodeIndex:
    """
    Build a CodeIndex from a flat {filename: content} dict.
    Keys may contain path separators (e.g. 'src/main/java/App.java').
    """
    index = CodeIndex()

    for path, content in raw_files.items():
        # Normalise separators
        clean_path = path.replace("\\", "/")

        # Skip files in ignored directories
        parts = clean_path.split("/")
        if any(p in SKIP_DIRS for p in parts):
            continue

        ext = os.path.splitext(clean_path)[1].lower()
        if ext in SKIP_EXTENSIONS:
            continue

        if ext not in EXT_TO_LANG:
            continue          # not a recognised source file

        index.files[clean_path] = content
        index.language_map[clean_path] = EXT_TO_LANG[ext]

    return index


def detect_primary_language(index: CodeIndex) -> str:
    """Return the most-common language in the index."""
    from collections import Counter
    if not index.language_map:
        return "Unknown"
    lang_counts = Counter(index.language_map.values())
    return lang_counts.most_common(1)[0][0]
