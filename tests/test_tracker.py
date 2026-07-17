"""Tests for application tracker."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nerajob.apply.tracker import Application, ApplicationTracker, ApplicationStatus


def test_application_status_transitions():
    """Test all valid status transitions."""
    app = Application(
        id="test_1",
        job_id="job_1",
        company="Test Corp",
        position="Engineer"
    )
    
    # Initial state
    assert app.status == ApplicationStatus.DRAFT
    
    # Transition to applied
    app.update_status(ApplicationStatus.APPLIED, "Submitted application")
    assert app.status == ApplicationStatus.APPLIED
    assert app.applied_at is not None
    assert len(app.notes) == 1
    
    # Transition to interview
    app.update_status(ApplicationStatus.INTERVIEW, "Phone screen scheduled")
    assert app.status == ApplicationStatus.INTERVIEW
    assert len(app.notes) == 2
    
    # Transition to offer
    app.update_status(ApplicationStatus.OFFER, "Received offer!")
    assert app.status == ApplicationStatus.OFFER
    
    # Accept offer
    app.update_status(ApplicationStatus.ACCEPTED, "Accepted!")
    assert app.status == ApplicationStatus.ACCEPTED


def test_application_notes():
    """Test adding notes to application."""
    app = Application(
        id="test_2",
        job_id="job_2",
        company="Another Corp",
        position="Developer"
    )
    
    app.add_note("First note")
    app.add_note("Second note")
    
    assert len(app.notes) == 2
    assert "First note" in app.notes[0]
    assert "Second note" in app.notes[1]


def test_application_contacts():
    """Test adding contacts to application."""
    app = Application(
        id="test_3",
        job_id="job_3",
        company="Contact Corp",
        position="Manager"
    )
    
    app.add_contact("john@example.com")
    app.add_contact("jane@example.com")
    
    assert len(app.contacts) == 2
    assert "john@example.com" in app.contacts
    assert "jane@example.com" in app.contacts


def test_tracker_add_application():
    """Test adding applications to tracker."""
    with TemporaryDirectory() as tmpdir:
        tracker = ApplicationTracker(Path(tmpdir))
        
        app = tracker.add_application(
            job_id="job_123",
            company="Test Company",
            position="Senior Engineer",
            url="https://example.com/job/123",
            salary_range="$100k-$150k",
            location="Remote",
            remote=True
        )
        
        assert app.company == "Test Company"
        assert app.position == "Senior Engineer"
        assert app.status == ApplicationStatus.DRAFT
        
        # Verify it's saved
        loaded = tracker.get_application(app.id)
        assert loaded is not None
        assert loaded.company == "Test Company"


def test_tracker_update_status():
    """Test updating application status in tracker."""
    with TemporaryDirectory() as tmpdir:
        tracker = ApplicationTracker(Path(tmpdir))
        
        app = tracker.add_application(
            job_id="job_456",
            company="Status Corp",
            position="Developer"
        )
        
        # Update status
        updated = tracker.update_status(
            app.id,
            ApplicationStatus.INTERVIEW,
            "Phone screen scheduled for Monday"
        )
        
        assert updated is not None
        assert updated.status == ApplicationStatus.INTERVIEW
        assert len(updated.notes) == 1
        
        # Verify it's persisted
        loaded = tracker.get_application(app.id)
        assert loaded.status == ApplicationStatus.INTERVIEW


def test_tracker_list_by_status():
    """Test listing applications filtered by status."""
    with TemporaryDirectory() as tmpdir:
        tracker = ApplicationTracker(Path(tmpdir))
        
        # Add multiple applications
        app1 = tracker.add_application("job_1", "Company A", "Engineer")
        app2 = tracker.add_application("job_2", "Company B", "Developer")
        app3 = tracker.add_application("job_3", "Company C", "Manager")
        
        # Update some statuses
        tracker.update_status(app1.id, ApplicationStatus.APPLIED)
        tracker.update_status(app2.id, ApplicationStatus.INTERVIEW)
        
        # List all
        all_apps = tracker.list_applications()
        assert len(all_apps) == 3
        
        # List by status
        applied = tracker.list_applications(status=ApplicationStatus.APPLIED)
        assert len(applied) == 1
        assert applied[0].company == "Company A"
        
        interview = tracker.list_applications(status=ApplicationStatus.INTERVIEW)
        assert len(interview) == 1
        assert interview[0].company == "Company B"


def test_tracker_statistics():
    """Test application statistics."""
    with TemporaryDirectory() as tmpdir:
        tracker = ApplicationTracker(Path(tmpdir))
        
        # Add applications with different statuses
        app1 = tracker.add_application("job_1", "Company A", "Engineer")
        app2 = tracker.add_application("job_2", "Company B", "Developer")
        app3 = tracker.add_application("job_3", "Company C", "Manager")
        
        tracker.update_status(app1.id, ApplicationStatus.APPLIED)
        tracker.update_status(app2.id, ApplicationStatus.INTERVIEW)
        tracker.update_status(app3.id, ApplicationStatus.OFFER)
        
        stats = tracker.get_statistics()
        
        assert stats["total"] == 3
        assert stats["by_status"]["applied"] == 1
        assert stats["by_status"]["interview"] == 1
        assert stats["by_status"]["offer"] == 1
        assert stats["response_rate"] > 0
        assert stats["interview_rate"] > 0


def test_tracker_export_summary():
    """Test exporting human-readable summary."""
    with TemporaryDirectory() as tmpdir:
        tracker = ApplicationTracker(Path(tmpdir))
        
        # Add some applications
        app1 = tracker.add_application("job_1", "Company A", "Engineer")
        tracker.update_status(app1.id, ApplicationStatus.APPLIED)
        
        summary = tracker.export_summary()
        
        assert "Application Tracker Summary" in summary
        assert "Total Applications: 1" in summary
        assert "Company A" in summary


if __name__ == "__main__":
    test_application_status_transitions()
    test_application_notes()
    test_application_contacts()
    test_tracker_add_application()
    test_tracker_update_status()
    test_tracker_list_by_status()
    test_tracker_statistics()
    test_tracker_export_summary()
    print("✅ All application tracker tests passed!")
