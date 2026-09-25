"""Stand-in data lake for the local dp-rest API."""

from lake.reader import DEFAULT_PAGE_SIZE, FolderLake, LakeReadError, LakeReader, Page, Record

__all__ = [
    "DEFAULT_PAGE_SIZE",
    "FolderLake",
    "LakeReadError",
    "LakeReader",
    "Page",
    "Record",
]
