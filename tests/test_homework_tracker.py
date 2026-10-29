from datetime import date

import pytest

from main import (
    create_assignment,
    get_assignment_summary,
    is_all_assignments_done,
    load_assignments,
    save_assignments,
)


@pytest.mark.parametrize("due_date", ["2026-10-29", "2026/10/29", "2026年10月29日"])
def test_create_assignment_accepts_common_date_formats(due_date):
    assignment = create_assignment(" 数学 ", " 予習ノート ", due_date)

    assert assignment["class_name"] == "数学"
    assert assignment["title"] == "予習ノート"
    assert assignment["due_date"] == "2026-10-29"
    assert assignment["done"] is False


def test_create_assignment_rejects_missing_fields_or_invalid_date():
    with pytest.raises(ValueError):
        create_assignment("", "予習ノート", "2026-10-29")

    with pytest.raises(ValueError):
        create_assignment("数学", "予習ノート", "2026-02-30")


def test_load_assignments_returns_empty_when_file_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("main.DATA_FILE", tmp_path / "missing.json")

    assert load_assignments() == []


def test_load_assignments_rejects_invalid_json(tmp_path, monkeypatch):
    data_file = tmp_path / "assignments.json"
    data_file.write_text("{", encoding="utf-8")
    monkeypatch.setattr("main.DATA_FILE", data_file)

    with pytest.raises(ValueError):
        load_assignments()


def test_load_assignments_validates_schema(tmp_path, monkeypatch):
    data_file = tmp_path / "assignments.json"
    data_file.write_text(
        """
        [
          {"id": "1", "class_name": "数学", "title": "宿題A", "due_date": "2026-10-28", "done": true},
          {"id": "2", "class_name": 99, "title": "broken", "due_date": "2026-10-29", "done": false}
        ]
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr("main.DATA_FILE", data_file)

    loaded = load_assignments()

    assert len(loaded) == 1
    assert loaded[0]["title"] == "宿題A"


def test_get_assignment_summary_counts_due_and_overdue(tmp_path, monkeypatch):
    data_file = tmp_path / "assignments.json"
    assignments = [
        {"id": "a", "class_name": "英語", "title": "単語テスト", "due_date": "2026-10-27", "done": False},
        {"id": "b", "class_name": "理科", "title": "レポート", "due_date": "2026-10-29", "done": False},
        {"id": "c", "class_name": "国語", "title": "読書感想文", "due_date": "2026-10-24", "done": False},
    ]
    data_file.write_text("[]", encoding="utf-8")
    monkeypatch.setattr("main.DATA_FILE", data_file)

    save_assignments(assignments)
    summary = get_assignment_summary(date(2026, 10, 27))

    assert summary["remaining"] == 3
    assert summary["due_today"] == 1
    assert summary["overdue"] == 1


def test_is_all_assignments_done_only_when_every_task_is_done():
    assignments = [
        {"id": "a", "done": True},
        {"id": "b", "done": True},
    ]
    assert is_all_assignments_done(assignments) is True
    assignments[1]["done"] = False
    assert is_all_assignments_done(assignments) is False


def test_get_assignment_summary_can_use_current_assignments():
    assignments = [
        {"due_date": "2026-10-27", "done": False},
        {"due_date": "2026-10-28", "done": True},
    ]

    summary = get_assignment_summary(date(2026, 10, 27), assignments)

    assert summary == {
        "total": 2,
        "remaining": 1,
        "completed": 1,
        "due_today": 1,
        "overdue": 0,
    }
