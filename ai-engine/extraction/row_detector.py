from typing import List, Dict


def group_words_into_rows(
    words: List[Dict],
    y_tolerance: int = 15
) -> List[List[Dict]]:
    """
    Group OCR words into rows using their vertical position.

    Words with similar Y positions are treated as belonging
    to the same document row.
    """

    if not words:
        return []

    sorted_words = sorted(
        words,
        key=lambda word: word["top"]
    )

    rows = []

    for word in sorted_words:

        word_center_y = (
            word["top"] + word["height"] / 2
        )

        placed = False

        for row in rows:

            row_center_y = sum(
                item["top"] + item["height"] / 2
                for item in row
            ) / len(row)

            if abs(word_center_y - row_center_y) <= y_tolerance:

                row.append(word)
                placed = True
                break

        if not placed:
            rows.append([word])

    # Sort every row from left to right
    for row in rows:
        row.sort(key=lambda word: word["left"])

    return rows