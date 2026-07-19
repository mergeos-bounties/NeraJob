from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nerajob.models import ApplicationPackage


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class TestModelValidation:
    def test_default_status_is_draft(self):
        pkg = ApplicationPackage(job_id="test-1")
        assert pkg.status == "draft"

    def test_created_at_and_updated_at_are_set(self):
        pkg = ApplicationPackage(job_id="test-2")
        assert pkg.created_at
        assert pkg.updated_at

    def test_valid_status_accepted(self):
        pkg = ApplicationPackage(job_id="test-3", status="applied")
        assert pkg.status == "applied"

    def test_invalid_status_raises_on_validation(self):
        with pytest.raises(ValidationError):
            ApplicationPackage(job_id="test-4", status="invalid_status")

    def test_all_valid_statuses(self):
        for status in ApplicationPackage.VALID_STATUSES:
            pkg = ApplicationPackage(job_id=f"test-{status}", status=status)
            assert pkg.status == status


class TestStatusTransitions:
    def test_set_status_valid(self):
        pkg = ApplicationPackage(job_id="trans-1")
        pkg.set_status("applied")
        assert pkg.status == "applied"

    def test_set_status_updates_updated_at(self):
        pkg = ApplicationPackage(job_id="trans-2")
        old_updated = pkg.updated_at
        pkg.set_status("interview")
        assert pkg.updated_at >= old_updated

    def test_set_status_invalid_raises(self):
        pkg = ApplicationPackage(job_id="trans-3")
        with pytest.raises(ValueError, match="Invalid status"):
            pkg.set_status("nonexistent")

    def test_full_workflow_transitions(self):
        pkg = ApplicationPackage(job_id="trans-4")
        assert pkg.status == "draft"
        pkg.set_status("applied")
        assert pkg.status == "applied"
        pkg.set_status("interview")
        assert pkg.status == "interview"
        pkg.set_status("offer")
        assert pkg.status == "offer"
        pkg.set_status("accepted")
        assert pkg.status == "accepted"

    def test_rejected_transition(self):
        pkg = ApplicationPackage(job_id="trans-5")
        pkg.set_status("applied")
        pkg.set_status("rejected")
        assert pkg.status == "rejected"


class TestListingAndStats:
    def _patch_app_dir(self, monkeypatch, tmp_path):
        import nerajob.storage as s

        monkeypatch.setattr(s, "APPLICATIONS_DIR", tmp_path / "applications")

    def test_load_applications_returns_list(self, tmp_path, monkeypatch):
        from nerajob.storage import load_applications, save_application

        self._patch_app_dir(monkeypatch, tmp_path)
        pkg1 = ApplicationPackage(job_id="stats-1", status="draft")
        pkg2 = ApplicationPackage(job_id="stats-2", status="applied")
        pkg3 = ApplicationPackage(job_id="stats-3", status="interview")
        save_application(pkg1)
        save_application(pkg2)
        save_application(pkg3)
        all_pkgs = load_applications()
        assert len(all_pkgs) == 3

    def test_stats_summary(self, tmp_path, monkeypatch):
        from nerajob.storage import load_applications, save_application

        self._patch_app_dir(monkeypatch, tmp_path)
        save_application(ApplicationPackage(job_id="s1", status="draft"))
        save_application(ApplicationPackage(job_id="s2", status="applied"))
        save_application(ApplicationPackage(job_id="s3", status="applied"))
        save_application(ApplicationPackage(job_id="s4", status="interview"))
        save_application(ApplicationPackage(job_id="s5", status="offer"))

        packages = load_applications()
        counts: dict[str, int] = {}
        for pkg in packages:
            counts[pkg.status] = counts.get(pkg.status, 0) + 1
        assert counts["draft"] == 1
        assert counts["applied"] == 2
        assert counts["interview"] == 1
        assert counts["offer"] == 1

    def test_update_application_status(self, tmp_path, monkeypatch):
        from nerajob.storage import save_application, update_application_status

        self._patch_app_dir(monkeypatch, tmp_path)
        pkg = ApplicationPackage(job_id="update-1", status="draft")
        save_application(pkg)

        result = update_application_status("update-1", "applied")
        assert result is not None
        assert result.status == "applied"

        result2 = update_application_status("nonexistent", "applied")
        assert result2 is None

    def test_load_nonexistent_application(self, tmp_path, monkeypatch):
        from nerajob.storage import load_application

        self._patch_app_dir(monkeypatch, tmp_path)
        pkg = load_application("no-such-job")
        assert pkg is None
