"""Application tracker with status states."""
from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    """Application status states."""
    DRAFT = "draft"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    TECHNICAL = "technical"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(BaseModel):
    """Application with status tracking."""
    id: str
    job_id: str
    company: str
    position: str
    status: ApplicationStatus = ApplicationStatus.DRAFT
    applied_at: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    notes: list[str] = Field(default_factory=list)
    contacts: list[str] = Field(default_factory=list)
    salary_range: Optional[str] = None
    location: Optional[str] = None
    remote: bool = False
    url: Optional[str] = None
    
    def update_status(self, new_status: ApplicationStatus, note: str = "") -> None:
        """Update application status with optional note."""
        self.status = new_status
        self.updated_at = datetime.now().isoformat()
        
        if new_status == ApplicationStatus.APPLIED:
            self.applied_at = self.updated_at
        
        if note:
            self.notes.append(f"[{self.updated_at}] {note}")
    
    def add_note(self, note: str) -> None:
        """Add a note to the application."""
        self.notes.append(f"[{self.updated_at}] {note}")
    
    def add_contact(self, contact: str) -> None:
        """Add a contact person."""
        self.contacts.append(contact)


class ApplicationTracker:
    """Manages all applications."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.applications_file = data_dir / "applications.json"
        self.applications: dict[str, Application] = {}
        self._load()
    
    def _load(self) -> None:
        """Load applications from file."""
        if self.applications_file.exists():
            with open(self.applications_file, "r") as f:
                data = json.load(f)
                for app_data in data.get("applications", []):
                    app = Application(**app_data)
                    self.applications[app.id] = app
    
    def _save(self) -> None:
        """Save applications to file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "applications": [app.model_dump() for app in self.applications.values()]
        }
        with open(self.applications_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def add_application(
        self,
        job_id: str,
        company: str,
        position: str,
        url: Optional[str] = None,
        salary_range: Optional[str] = None,
        location: Optional[str] = None,
        remote: bool = False,
    ) -> Application:
        """Add a new application."""
        app_id = f"{company.lower().replace(' ', '_')}_{job_id}"
        
        app = Application(
            id=app_id,
            job_id=job_id,
            company=company,
            position=position,
            url=url,
            salary_range=salary_range,
            location=location,
            remote=remote,
        )
        
        self.applications[app_id] = app
        self._save()
        return app
    
    def update_status(self, app_id: str, status: ApplicationStatus, note: str = "") -> Optional[Application]:
        """Update application status."""
        if app_id not in self.applications:
            return None
        
        app = self.applications[app_id]
        app.update_status(status, note)
        self._save()
        return app
    
    def add_note(self, app_id: str, note: str) -> Optional[Application]:
        """Add a note to an application."""
        if app_id not in self.applications:
            return None
        
        app = self.applications[app_id]
        app.add_note(note)
        self._save()
        return app
    
    def get_application(self, app_id: str) -> Optional[Application]:
        """Get an application by ID."""
        return self.applications.get(app_id)
    
    def list_applications(self, status: Optional[ApplicationStatus] = None) -> list[Application]:
        """List all applications, optionally filtered by status."""
        apps = list(self.applications.values())
        if status:
            apps = [app for app in apps if app.status == status]
        return sorted(apps, key=lambda x: x.updated_at, reverse=True)
    
    def get_statistics(self) -> dict:
        """Get application statistics."""
        stats = {
            "total": len(self.applications),
            "by_status": {},
            "response_rate": 0.0,
            "interview_rate": 0.0,
        }
        
        for status in ApplicationStatus:
            count = len([app for app in self.applications.values() if app.status == status])
            stats["by_status"][status.value] = count
        
        total = stats["total"]
        if total > 0:
            responded = total - stats["by_status"].get("applied", 0) - stats["by_status"].get("draft", 0)
            stats["response_rate"] = (responded / total) * 100
            
            interviews = stats["by_status"].get("interview", 0) + stats["by_status"].get("technical", 0)
            stats["interview_rate"] = (interviews / total) * 100
        
        return stats
    
    def export_summary(self) -> str:
        """Export a human-readable summary."""
        stats = self.get_statistics()
        
        lines = [
            "📊 Application Tracker Summary",
            "=" * 40,
            f"Total Applications: {stats['total']}",
            f"Response Rate: {stats['response_rate']:.1f}%",
            f"Interview Rate: {stats['interview_rate']:.1f}%",
            "",
            "By Status:",
        ]
        
        for status, count in stats["by_status"].items():
            if count > 0:
                lines.append(f"  {status}: {count}")
        
        lines.extend(["", "Recent Applications:"])
        
        for app in self.list_applications()[:5]:
            lines.append(f"  [{app.status.value}] {app.company} - {app.position}")
        
        return "\n".join(lines)
