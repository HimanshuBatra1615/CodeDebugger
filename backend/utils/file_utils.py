
import io
import zipfile
import os

from parsers.code_reader import CodeIndex, detect_primary_language  

_TEXT_EXTENSIONS = {
    ".java", ".kt", ".groovy", ".scala",
    ".py", ".js", ".ts", ".mjs", ".cjs",
    ".go", ".cs", ".cpp", ".cc", ".c", ".h",
    ".rs", ".rb", ".php", ".swift", ".dart",
    ".jsx", ".tsx",
    ".xml", ".yaml", ".yml", ".json", ".toml",
    ".properties", ".ini", ".cfg",
    ".md", ".txt",
}

_MAX_FILE_SIZE = 1_000_000  


def extract_files_from_zip(zip_bytes: bytes) -> dict[str, str]:

    results: dict[str, str] = {}

    _SKIP_DIRS = {
        "node_modules", "__pycache__", ".git", "build", "dist",
        "target", ".gradle", "vendor", "venv", ".venv", ".next",
    }

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                if info.file_size > _MAX_FILE_SIZE:
                    continue

                path = info.filename.replace("\\", "/")
                parts = path.split("/")
                if any(p in _SKIP_DIRS for p in parts):
                    continue

                ext = os.path.splitext(path)[1].lower()
                if ext not in _TEXT_EXTENSIONS:
                    continue

                try:
                    raw = zf.read(info.filename)
                    content = raw.decode("utf-8", errors="replace")
                    results[path] = content
                except Exception:
                    continue
    except zipfile.BadZipFile:
        pass

    return results
