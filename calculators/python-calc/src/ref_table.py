SCORE_TABLE: dict[int, str] = {
    1: "A",
    2: "AA",
    3: "AAA",
    4: "B",
    5: "BB",
    6: "BBB",
    7: "C",
    8: "CC",
    9: "CCC",
    10: "-",
}


def get_score(code: int) -> str:
    """Return the grade label for a score key."""
    return SCORE_TABLE.get(code, "N/A")
