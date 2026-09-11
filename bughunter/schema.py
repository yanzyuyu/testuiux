from enum import Enum
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class IssueType(str, Enum):
    TEXT_OVERLAP = "TEXT_OVERLAP"
    ELEMENT_COLLISION = "ELEMENT_COLLISION"
    HORIZONTAL_OVERFLOW = "HORIZONTAL_OVERFLOW"
    TEXT_TRUNCATION = "TEXT_TRUNCATION"
    BROKEN_ASSET = "BROKEN_ASSET"
    CONTRAST_LOW = "CONTRAST_LOW"
    LAYOUT_SHIFT = "LAYOUT_SHIFT"


class BoundingBox(BaseModel):
    ymin: int = Field(ge=0, le=1000)
    xmin: int = Field(ge=0, le=1000)
    ymax: int = Field(ge=0, le=1000)
    xmax: int = Field(ge=0, le=1000)


class VisualIssue(BaseModel):
    type: IssueType
    severity: SeverityLevel
    description: str
    suggested_fix: str
    box: BoundingBox


class ViewportResult(BaseModel):
    viewport_name: str
    width: int
    height: int
    screenshot_path: str
    annotated_path: str = ""
    issues: list[VisualIssue] = Field(default_factory=list)


class AuditReport(BaseModel):
    target_url: str
    timestamp: str
    viewports: list[ViewportResult] = Field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return sum(len(vp.issues) for vp in self.viewports)

    @property
    def critical_count(self) -> int:
        return sum(
            1
            for vp in self.viewports
            for issue in vp.issues
            if issue.severity == SeverityLevel.CRITICAL
        )

    @property
    def warning_count(self) -> int:
        return sum(
            1
            for vp in self.viewports
            for issue in vp.issues
            if issue.severity == SeverityLevel.WARNING
        )
