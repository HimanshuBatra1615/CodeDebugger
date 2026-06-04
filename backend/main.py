
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from engines.ai_engine import analyze_errors
from engines.correlation_engine import correlate_errors
from models.schemas import AnalysisStatus
from parsers.code_reader import build_code_index
from parsers.log_parser import parse_log_file
from utils.file_utils import detect_primary_language, extract_files_from_zip


app = FastAPI(title="CodeDebugger API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


analyses: dict[str, dict] = {}
progress_queues: dict[str, asyncio.Queue] = {}



async def _run_analysis(
    analysis_id: str,
    code_files: dict[str, bytes],
    log_content: str,
) -> None:
    queue = progress_queues[analysis_id]

    async def emit(step: str, message: str, **extra):
        event = {"type": "progress", "step": step, "message": message, **extra}
        await queue.put(event)

    try:
        analyses[analysis_id]["status"] = AnalysisStatus.PROCESSING

        await emit("parsing", "Parsing log file…")
        log_errors = parse_log_file(log_content)
        await emit("parsing", f"Found {len(log_errors)} error entries", count=len(log_errors))

        await emit("indexing", "Indexing source files…")
        expanded: dict[str, str] = {}
        for filename, raw in code_files.items():
            if filename.lower().endswith(".zip"):
                expanded.update(extract_files_from_zip(raw))
            else:
                try:
                    expanded[filename] = raw.decode("utf-8", errors="replace")
                except Exception:
                    pass

        code_index = build_code_index(expanded)
        await emit(
            "indexing",
            f"Indexed {len(code_index.files)} source files",
            count=len(code_index.files),
        )

        await emit("correlating", "Correlating errors with source code…")
        correlated = correlate_errors(log_errors, code_index)
        await emit(
            "correlating",
            f"Correlated {len(correlated)} errors to source lines",
            count=len(correlated),
        )

        if not correlated:
            await emit(
                "correlating",
                "No source matches found – running analysis on log context only",
            )

        n = len(correlated)
        await emit("analyzing", f"Running AI analysis on {n} error{'s' if n != 1 else ''}…")
        suggestions = await analyze_errors(correlated)

        result = {
            "analysis_id": analysis_id,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "status": AnalysisStatus.COMPLETE,
            "language": detect_primary_language(code_index),
            "files_analyzed": list(code_index.files.keys()),
            "total_log_errors": len(log_errors),
            "correlated": len(correlated),
            "suggestions": [s.model_dump() for s in suggestions],
            "error_message": None,
        }
        analyses[analysis_id].update(result)
        await queue.put({"type": "complete", "result": result})

    except Exception as exc:  
        msg = str(exc)
        analyses[analysis_id]["status"] = AnalysisStatus.ERROR
        analyses[analysis_id]["error_message"] = msg
        await queue.put({"type": "error", "message": msg})



@app.post("/api/analyze")
async def start_analysis(
    background_tasks: BackgroundTasks,
    code_files: list[UploadFile] = File(..., description="Source files or a single .zip archive"),
    log_file: UploadFile = File(..., description="Application log file (.log or .txt)"),
):
    analysis_id = str(uuid.uuid4())[:8]
    analyses[analysis_id] = {
        "analysis_id": analysis_id,
        "status": AnalysisStatus.PENDING,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    progress_queues[analysis_id] = asyncio.Queue()

    code_contents: dict[str, bytes] = {}
    for f in code_files:
        code_contents[f.filename or "unknown"] = await f.read()

    log_bytes = await log_file.read()
    log_text = log_bytes.decode("utf-8", errors="replace")

    background_tasks.add_task(_run_analysis, analysis_id, code_contents, log_text)

    return {"analysis_id": analysis_id, "status": "pending"}


@app.get("/api/analyze/{analysis_id}/progress")
async def stream_progress(analysis_id: str):
    if analysis_id not in progress_queues:
        raise HTTPException(status_code=404, detail="Analysis not found")

    async def generate():
        queue = progress_queues[analysis_id]
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    continue

                yield f"data: {json.dumps(event)}\n\n"

                if event.get("type") in ("complete", "error"):
                    break
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/analyze/{analysis_id}")
async def get_analysis(analysis_id: str):
    if analysis_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analyses[analysis_id]


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
