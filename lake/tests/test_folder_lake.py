"""FolderLake pages a JSONL file. No HTTP."""

from pathlib import Path

from lake.reader import FolderLake

OBLIGORS = Path(__file__).resolve().parents[1] / "data" / "obligors.jsonl"


def test_folder_lake_pages_obligors():
    lake = FolderLake(OBLIGORS)

    first = lake.read_page(page_size=2)
    assert [(row.id, row.sector, row.revenue, row.ltd_ratio, row.credit_score) for row in first.records] == [
        ("1", "Technology", "45000000", "0.35", "720"),
        ("2", "Energy", "12000000", "0.72", "580"),
    ]
    assert first.next_cursor == "2"

    second = lake.read_page(cursor=first.next_cursor, page_size=2)
    assert [row.id for row in second.records] == ["3", "4"]
    assert second.next_cursor == "4"

    last = lake.read_page(cursor=second.next_cursor, page_size=2)
    assert [row.id for row in last.records] == ["5", "6"]
    assert last.records[0].sector == "Energy"
    assert last.next_cursor is None
