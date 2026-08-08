from typing import List, Dict


def sort_row_by_position(row: List[Dict]) -> List[Dict]:
    """
    Sort words in a row from left to right.
    """

    return sorted(
        row,
        key=lambda word: word["left"]
    )


def row_to_columns(row: List[Dict]) -> List[str]:
    """
    Convert OCR words from a row into
    left-to-right column values.
    """

    sorted_words = sort_row_by_position(row)

    return [
        word["text"]
        for word in sorted_words
    ]