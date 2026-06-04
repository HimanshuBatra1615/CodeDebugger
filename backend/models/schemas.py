from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


class StackFrame(BaseModel):
    class_name: str = ""
    method: str = ""
    file: str
    line: int


class ParsedLogError(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    level: str
    message: str
    exception_type: str = "UnknownError"
    stack_frames: list[StackFrame] = []
    raw_text: str = ""
    timestamp: Optional[str] = None


class CorrelatedError(BaseModel):
    error: ParsedLogError
    source_file: str
    line: int
    method: str = ""
    code_context: str
    language: str


class Suggestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    severity: Severity
    error_type: str
    source_file: str
    line: int
    method: str = ""
    root_cause: str
    suggestion: str
    fixed_code: str
    confidence: float
    original_context: str = ""


class AnalysisResult(BaseModel):
    analysis_id: str
    scanned_at: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    language: str = "Unknown"
    files_analyzed: list[str] = []
    total_log_errors: int = 0
    correlated: int = 0
    suggestions: list[Suggestion] = []
    error_message: Optional[str] = None
