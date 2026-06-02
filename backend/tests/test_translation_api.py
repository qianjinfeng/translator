"""End-to-end API tests for the translation workflow.

Tests exercise the full pipeline end-to-end using a mock AI provider
so no real model is required.
"""

from __future__ import annotations

import json
import os
import tempfile

from docx import Document
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine

client = TestClient(app)


# ---------------------------------------------------------------------------
# Module-level DB lifecycle (mirrors test_health.py pattern)
# ---------------------------------------------------------------------------


def setup_module() -> None:
    """Create all tables before running tests in this module."""
    Base.metadata.create_all(bind=engine)


def teardown_module() -> None:
    """Drop all tables after running tests."""
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_test_docx(
    texts: list[str] | None = None,
) -> str:
    """Create a temporary DOCX file and return its absolute path."""
    if texts is None:
        texts = [
            "This is a test paragraph for translation.",
            "The patient has a fever and needs treatment.",
            "Blood pressure is within normal range.",
        ]
    doc = Document()
    for t in texts:
        doc.add_paragraph(t)

    fd, path = tempfile.mkstemp(suffix=".docx")
    os.close(fd)
    doc.save(path)
    return path


def _default_config(**overrides: object) -> str:
    """Return a default translation config JSON string."""
    cfg: dict[str, object] = {
        "source_languages": "en",
        "target_languages": "zh",
        "output_mode": "bilingual",
        "ai_provider": "mock",
        "rag_enabled": False,
        "image_translation_enabled": False,
        "glossary_id": None,
    }
    cfg.update(overrides)
    return json.dumps(cfg)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTranslationAPI:
    """Test suite for the translation workflow endpoints."""

    # -- Upload + translate ---------------------------------------------------

    def test_upload_and_translate_docx(self) -> None:
        """Upload a DOCX and verify it gets parsed and translated."""
        docx_path = _create_test_docx()

        with open(docx_path, "rb") as f:
            response = client.post(
                "/api/translation/upload",
                files={
                    "file": (
                        "test.docx",
                        f,
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document",
                    )
                },
                data={"config": _default_config()},
            )

        os.unlink(docx_path)

        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "completed"
        assert data["progress_pct"] == 100.0

    def test_upload_with_custom_config(self) -> None:
        """Upload with non-default config values."""
        docx_path = _create_test_docx(["Only one paragraph."])

        config = _default_config(
            source_languages="en",
            target_languages="zh",
            output_mode="standalone",
            ai_provider="mock",
        )

        with open(docx_path, "rb") as f:
            response = client.post(
                "/api/translation/upload",
                files={"file": ("doc.docx", f, "application/octet-stream")},
                data={"config": config},
            )

        os.unlink(docx_path)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "completed"

        # Verify config was persisted
        task_id = data["task_id"]
        resp = client.get(f"/api/translation/tasks/{task_id}")
        assert resp.status_code == 200
        td = resp.json()["task"]
        assert td["source_languages"] == "en"
        assert td["target_languages"] == "zh"
        assert td["output_mode"] == "standalone"
        assert td["ai_provider"] == "mock"

    # -- Upload error handling ------------------------------------------------

    def test_upload_invalid_file_format(self) -> None:
        """Uploading a non-docx/pdf file should return 400."""
        response = client.post(
            "/api/translation/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
            data={"config": _default_config()},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_upload_missing_config(self) -> None:
        """Upload without the config form field should return 422."""
        docx_path = _create_test_docx(["Missing config."])
        with open(docx_path, "rb") as f:
            response = client.post(
                "/api/translation/upload",
                files={"file": ("t.docx", f, "application/octet-stream")},
            )
        os.unlink(docx_path)
        assert response.status_code == 422

    def test_upload_invalid_config_json(self) -> None:
        """Upload with unparseable config JSON should return 400."""
        docx_path = _create_test_docx(["Bad config."])
        with open(docx_path, "rb") as f:
            response = client.post(
                "/api/translation/upload",
                files={"file": ("t.docx", f, "application/octet-stream")},
                data={"config": "not-json"},
            )
        os.unlink(docx_path)
        assert response.status_code == 400
        assert "Invalid config" in response.json()["detail"]

    def test_upload_empty_file(self) -> None:
        """Uploading an empty file should return 400."""
        response = client.post(
            "/api/translation/upload",
            files={
                "file": ("empty.docx", b"", "application/octet-stream"),
            },
            data={"config": _default_config()},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_with_invalid_provider(self) -> None:
        """An unknown AI provider should cause the task to fail."""
        docx_path = _create_test_docx(["This will fail."])
        config = _default_config(ai_provider="nonexistent")

        with open(docx_path, "rb") as f:
            response = client.post(
                "/api/translation/upload",
                files={"file": ("t.docx", f, "application/octet-stream")},
                data={"config": config},
            )
        os.unlink(docx_path)

        assert response.status_code == 201
        task_id = response.json()["task_id"]

        # Verify the task ended up in failed status
        resp = client.get(f"/api/translation/tasks/{task_id}")
        assert resp.status_code == 200
        td = resp.json()["task"]
        assert td["status"] == "failed"
        assert td["error_message"] is not None

    # -- List tasks -----------------------------------------------------------

    def test_list_tasks(self) -> None:
        """Listing tasks returns all tasks newest first."""
        response = client.get("/api/translation/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    # -- Get task -------------------------------------------------------------

    def test_get_task_not_found(self) -> None:
        """Getting a non-existent task returns 404."""
        response = client.get("/api/translation/tasks/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    def test_get_task_with_segments(self) -> None:
        """A completed task should include segments with translations."""
        # Create a task by uploading
        docx_path = _create_test_docx()
        with open(docx_path, "rb") as f:
            upload_resp = client.post(
                "/api/translation/upload",
                files={"file": ("seg.docx", f, "application/octet-stream")},
                data={"config": _default_config()},
            )
        os.unlink(docx_path)
        assert upload_resp.status_code == 201
        task_id = upload_resp.json()["task_id"]

        # Fetch task detail
        response = client.get(f"/api/translation/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()

        td = data["task"]
        assert td["id"] == task_id
        assert td["status"] == "completed"
        assert td["total_segments"] > 0
        assert td["translated_segments"] == td["total_segments"]
        assert td["progress_pct"] == 100.0

        assert len(data["segments"]) > 0
        for seg in data["segments"]:
            assert "source_text" in seg
            assert "translated_text" in seg
            assert seg["translated_text"] is not None
            # Mock provider prepends language prefix
            assert seg["translated_text"].startswith("[ZH] ")

    # -- Download -------------------------------------------------------------

    def test_download_translated_docx(self) -> None:
        """Download returns the rebuilt DOCX file."""
        docx_path = _create_test_docx(["Download test."])
        with open(docx_path, "rb") as f:
            upload_resp = client.post(
                "/api/translation/upload",
                files={"file": ("dl.docx", f, "application/octet-stream")},
                data={"config": _default_config()},
            )
        os.unlink(docx_path)
        task_id = upload_resp.json()["task_id"]

        response = client.get(f"/api/translation/tasks/{task_id}/download")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument"
        )
        # Response should be actual content (not empty)
        assert len(response.content) > 0

    def test_download_task_not_found(self) -> None:
        """Download for a non-existent task returns 404."""
        response = client.get("/api/translation/tasks/bad-id/download")
        assert response.status_code == 404

    # -- Re-trigger translation -----------------------------------------------

    def test_retranslate_task(self) -> None:
        """Re-triggering translation resets and re-translates."""
        docx_path = _create_test_docx(["Retranslate me."])
        with open(docx_path, "rb") as f:
            upload_resp = client.post(
                "/api/translation/upload",
                files={"file": ("re.docx", f, "application/octet-stream")},
                data={"config": _default_config()},
            )
        os.unlink(docx_path)
        task_id = upload_resp.json()["task_id"]

        # Re-trigger
        response = client.post(
            f"/api/translation/tasks/{task_id}/translate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "completed"

        # Segments should have fresh translations
        resp = client.get(f"/api/translation/tasks/{task_id}")
        assert resp.status_code == 200
        for seg in resp.json()["segments"]:
            assert seg["translated_text"] is not None

    def test_retranslate_nonexistent_task(self) -> None:
        """Re-trigger on a non-existent task returns 404."""
        response = client.post(
            "/api/translation/tasks/missing/translate"
        )
        assert response.status_code == 404
