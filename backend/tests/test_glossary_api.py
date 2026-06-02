"""Tests for the Glossary API endpoints.

Covers full CRUD for glossaries and entries, CSV/Excel import,
and error handling.
"""

from __future__ import annotations

import io
from typing import Any

import openpyxl
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine

client = TestClient(app)


# ---------------------------------------------------------------------------
# Module-level DB lifecycle
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


def _create_glossary(name: str = "Test Glossary", department: str | None = "Cardiology") -> dict[str, Any]:
    """Create a glossary and return its data dict."""
    body: dict[str, Any] = {"name": name}
    if department is not None:
        body["department"] = department
    response = client.post("/api/glossary/", json=body)
    assert response.status_code == 201
    return response.json()


def _add_entry(glossary_id: str, source: str = "catheter", target: str = "导管") -> dict[str, Any]:
    """Add an entry to a glossary."""
    response = client.post(
        f"/api/glossary/{glossary_id}/entries",
        json={"source_term": source, "target_term": target},
    )
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGlossaryCRUD:
    """Test glossary CRUD operations."""

    def test_list_empty(self) -> None:
        """Listing glossaries when none exist returns empty list."""
        response = client.get("/api/glossary/")
        assert response.status_code == 200
        data = response.json()
        assert data["glossaries"] == []

    def test_create_glossary(self) -> None:
        """Create a glossary returns the created glossary."""
        data = _create_glossary("Cardio Terms", "Cardiology")
        assert data["name"] == "Cardio Terms"
        assert data["department"] == "Cardiology"
        assert data["entry_count"] == 0
        assert "id" in data
        assert "created_at" in data

    def test_create_glossary_minimal(self) -> None:
        """Create a glossary with only name."""
        response = client.post("/api/glossary/", json={"name": "Minimal"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal"
        assert data["department"] is None

    def test_list_glossaries(self) -> None:
        """List returns all glossaries with entry counts."""
        g1 = _create_glossary("G1")
        g2 = _create_glossary("G2")

        # Add an entry to g1
        _add_entry(g1["id"])

        response = client.get("/api/glossary/")
        assert response.status_code == 200
        data = response.json()

        glossaries = {g["id"]: g for g in data["glossaries"]}
        assert glossaries[g1["id"]]["entry_count"] == 1
        assert glossaries[g2["id"]]["entry_count"] == 0

    def test_get_glossary(self) -> None:
        """Get a single glossary with entries."""
        g = _create_glossary("GetTest")
        _add_entry(g["id"], "stent", "支架")

        response = client.get(f"/api/glossary/{g['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["glossary"]["name"] == "GetTest"
        assert len(data["entries"]) == 1
        assert data["entries"][0]["source_term"] == "stent"
        assert data["entries"][0]["target_term"] == "支架"

    def test_get_glossary_not_found(self) -> None:
        """Getting a non-existent glossary returns 404."""
        response = client.get("/api/glossary/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Glossary not found"

    def test_update_glossary(self) -> None:
        """Update glossary metadata."""
        g = _create_glossary("Old Name", "Old Dept")
        response = client.put(
            f"/api/glossary/{g['id']}",
            json={"name": "New Name", "department": "New Dept"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["department"] == "New Dept"

    def test_update_glossary_partial(self) -> None:
        """Update only the name."""
        g = _create_glossary("Partial", "Dept")
        response = client.put(
            f"/api/glossary/{g['id']}",
            json={"name": "Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["department"] == "Dept"

    def test_delete_glossary(self) -> None:
        """Delete a glossary removes it and its entries."""
        g = _create_glossary("DeleteMe")
        _add_entry(g["id"], "a", "b")

        response = client.delete(f"/api/glossary/{g['id']}")
        assert response.status_code == 200
        assert response.json()["detail"] == "Glossary deleted"

        # Verify it's gone
        response = client.get(f"/api/glossary/{g['id']}")
        assert response.status_code == 404

    def test_delete_glossary_not_found(self) -> None:
        """Delete a non-existent glossary returns 404."""
        response = client.delete("/api/glossary/nonexistent")
        assert response.status_code == 404


class TestEntriesCRUD:
    """Test entry CRUD operations."""

    def test_add_entry(self) -> None:
        """Add an entry to a glossary."""
        g = _create_glossary("EntryTest")
        data = _add_entry(g["id"], "blood pressure", "血压")
        assert data["source_term"] == "blood pressure"
        assert data["target_term"] == "血压"
        assert data["context_note"] is None

    def test_add_entry_with_context(self) -> None:
        """Add an entry with a context note."""
        g = _create_glossary("CtxTest")
        response = client.post(
            f"/api/glossary/{g['id']}/entries",
            json={
                "source_term": "fever",
                "target_term": "发热",
                "context_note": "General symptom",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["context_note"] == "General symptom"

    def test_add_entry_to_nonexistent_glossary(self) -> None:
        """Adding an entry to a non-existent glossary returns 404."""
        response = client.post(
            "/api/glossary/bad-id/entries",
            json={"source_term": "test", "target_term": "测试"},
        )
        assert response.status_code == 404

    def test_update_entry(self) -> None:
        """Update an entry's fields."""
        g = _create_glossary("UpdEntry")
        e = _add_entry(g["id"], "old", "旧的")

        response = client.put(
            f"/api/glossary/{g['id']}/entries/{e['id']}",
            json={"source_term": "new", "target_term": "新的"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source_term"] == "new"
        assert data["target_term"] == "新的"

    def test_update_entry_partial(self) -> None:
        """Update only the context note."""
        g = _create_glossary("PartEntry")
        e = _add_entry(g["id"], "term", "术语")

        response = client.put(
            f"/api/glossary/{g['id']}/entries/{e['id']}",
            json={"context_note": "Updated note"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source_term"] == "term"
        assert data["context_note"] == "Updated note"

    def test_update_entry_not_found(self) -> None:
        """Update a non-existent entry returns 404."""
        g = _create_glossary("NotFoundEntry")
        response = client.put(
            f"/api/glossary/{g['id']}/entries/99999",
            json={"source_term": "x"},
        )
        assert response.status_code == 404

    def test_delete_entry(self) -> None:
        """Delete an entry from a glossary."""
        g = _create_glossary("DelEntry")
        e = _add_entry(g["id"], "delete", "删除")

        response = client.delete(f"/api/glossary/{g['id']}/entries/{e['id']}")
        assert response.status_code == 200
        assert response.json()["detail"] == "Entry deleted"

        # Verify entry is gone
        resp = client.get(f"/api/glossary/{g['id']}")
        assert len(resp.json()["entries"]) == 0

    def test_delete_entry_not_found(self) -> None:
        """Delete a non-existent entry returns 404."""
        g = _create_glossary("NotFoundDel")
        response = client.delete(f"/api/glossary/{g['id']}/entries/99999")
        assert response.status_code == 404


class TestImport:
    """Test CSV/Excel import."""

    # -- CSV Import -----------------------------------------------------------

    def test_import_csv(self) -> None:
        """Import entries from CSV."""
        g = _create_glossary("CSVImport")

        csv_content = "source_term,target_term,context_note\ncatheter,导管,Cardiovascular\nstent,支架,\n"
        response = client.post(
            f"/api/glossary/{g['id']}/import",
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert response.json()["imported_count"] == 2

        # Verify entries were created
        resp = client.get(f"/api/glossary/{g['id']}")
        assert len(resp.json()["entries"]) == 2

    def test_import_csv_without_context(self) -> None:
        """Import CSV with 2 columns (no context_note)."""
        g = _create_glossary("CSVNoCtx")

        csv_content = "source_term,target_term\nheart,心脏\nlung,肺\n"
        response = client.post(
            f"/api/glossary/{g['id']}/import",
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert response.json()["imported_count"] == 2

    def test_import_csv_empty_rows_skipped(self) -> None:
        """Import CSV with empty rows should skip them."""
        g = _create_glossary("CSVSkipEmpty")

        csv_content = (
            "source_term,target_term,context_note\n"
            "valid,有效,\n"
            ",,\n"
            "also_valid,也有效,test\n"
        )
        response = client.post(
            f"/api/glossary/{g['id']}/import",
            files={"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")},
        )
        assert response.status_code == 200
        assert response.json()["imported_count"] == 2

    def test_import_csv_empty_file(self) -> None:
        """Import empty CSV returns 400."""
        g = _create_glossary("CSVEmpty")
        response = client.post(
            f"/api/glossary/{g['id']}/import",
            files={"file": ("empty.csv", b"source_term,target_term\n", "text/csv")},
        )
        assert response.status_code == 400
        assert "No valid entries" in response.json()["detail"]

    # -- Excel Import ---------------------------------------------------------

    def _make_excel(self, rows: list[dict[str, str]]) -> bytes:
        """Create an Excel file in memory and return bytes."""
        wb = openpyxl.Workbook()
        ws = wb.active
        assert ws is not None
        # Header
        ws.append(["source_term", "target_term", "context_note"])
        for row in rows:
            ws.append([row.get("source_term", ""), row.get("target_term", ""), row.get("context_note", "")])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.read()

    def test_import_excel(self) -> None:
        """Import entries from Excel."""
        g = _create_glossary("ExcelImport")

        excel_bytes = self._make_excel([
            {"source_term": "catheter", "target_term": "导管", "context_note": "Cardiovascular"},
            {"source_term": "stent", "target_term": "支架", "context_note": ""},
        ])
        response = client.post(
            f"/api/glossary/{g['id']}/import",
            files={"file": ("test.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code == 200
        assert response.json()["imported_count"] == 2

        # Verify entries
        resp = client.get(f"/api/glossary/{g['id']}")
        assert len(resp.json()["entries"]) == 2

    def test_import_excel_empty_rows_skipped(self) -> None:
        """Import Excel with empty rows should skip them."""
        g = _create_glossary("ExcelSkipEmpty")

        excel_bytes = self._make_excel([
            {"source_term": "valid", "target_term": "有效", "context_note": ""},
            {"source_term": "", "target_term": "", "context_note": ""},
            {"source_term": "also_valid", "target_term": "也有效", "context_note": "test"},
        ])
        response = client.post(
            f"/api/glossary/{g['id']}/import",
            files={"file": ("test.xlsx", excel_bytes, "application/octet-stream")},
        )
        assert response.status_code == 200
        assert response.json()["imported_count"] == 2

    # -- Invalid file handling ------------------------------------------------

    def test_import_invalid_format(self) -> None:
        """Import a non-CSV/Excel file returns 400."""
        g = _create_glossary("BadFormat")
        response = client.post(
            f"/api/glossary/{g['id']}/import",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_import_to_nonexistent_glossary(self) -> None:
        """Import to a non-existent glossary returns 404."""
        response = client.post(
            "/api/glossary/bad-id/import",
            files={"file": ("test.csv", b"source_term,target_term\nx,y\n", "text/csv")},
        )
        assert response.status_code == 404
