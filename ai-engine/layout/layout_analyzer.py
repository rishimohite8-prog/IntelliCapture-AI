from typing import Dict, List
from statistics import mean


# ============================================================
# LAYOUT TYPES
# ============================================================

TABLE = "TABLE"
ROW_REGISTER = "ROW_REGISTER"
FORM = "FORM"
FREE_FORM = "FREE_FORM"


# ============================================================
# GEOMETRY HELPERS
# ============================================================

def _center_x(word: Dict) -> float:
    return word["left"] + word["width"] / 2


def _center_y(word: Dict) -> float:
    return word["top"] + word["height"] / 2


# ============================================================
# LINE GROUPING
# ============================================================

def _group_into_lines(
    words: List[Dict],
    y_tolerance: int = 15
) -> List[List[Dict]]:

    if not words:
        return []

    sorted_words = sorted(
        words,
        key=lambda word: (
            word["top"],
            word["left"]
        )
    )

    lines = []

    for word in sorted_words:

        word_y = _center_y(word)

        best_line = None
        best_distance = None

        for line in lines:

            line_y = mean(
                _center_y(item)
                for item in line
            )

            distance = abs(
                word_y - line_y
            )

            if distance <= y_tolerance:

                if (
                    best_distance is None
                    or distance < best_distance
                ):
                    best_line = line
                    best_distance = distance

        if best_line is not None:
            best_line.append(word)
        else:
            lines.append([word])

    for line in lines:
        line.sort(
            key=lambda word: word["left"]
        )

    return lines


# ============================================================
# LINE INFORMATION
# ============================================================

def _line_information(
    lines: List[List[Dict]]
) -> List[Dict]:

    information = []

    for line in lines:

        if not line:
            continue

        left = min(
            word["left"]
            for word in line
        )

        right = max(
            word["left"] + word["width"]
            for word in line
        )

        top = min(
            word["top"]
            for word in line
        )

        bottom = max(
            word["top"] + word["height"]
            for word in line
        )

        information.append(
            {
                "words": line,
                "text": " ".join(
                    word["text"]
                    for word in line
                ),
                "left": left,
                "right": right,
                "top": top,
                "bottom": bottom,
                "width": right - left,
                "height": bottom - top,
                "word_count": len(line),
            }
        )

    return information


# ============================================================
# LABEL DETECTION
# ============================================================

def _looks_like_label(text: str) -> bool:

    text = text.strip()

    if not text:
        return False

    return ":" in text


def _count_key_value_lines(
    line_info: List[Dict]
) -> int:

    return sum(
        1
        for line in line_info
        if _looks_like_label(line["text"])
    )


# ============================================================
# X-POSITION CLUSTERS
# ============================================================

def _cluster_x_positions(
    lines: List[List[Dict]],
    tolerance: int = 35
) -> List[Dict]:

    clusters = []

    for line_index, line in enumerate(lines):

        for word in line:

            x = _center_x(word)

            best_cluster = None
            best_distance = None

            for cluster in clusters:

                cluster_x = mean(
                    cluster["positions"]
                )

                distance = abs(
                    x - cluster_x
                )

                if distance <= tolerance:

                    if (
                        best_distance is None
                        or distance < best_distance
                    ):
                        best_cluster = cluster
                        best_distance = distance

            if best_cluster is None:

                clusters.append(
                    {
                        "positions": [x],
                        "lines": {line_index},
                    }
                )

            else:

                best_cluster["positions"].append(x)
                best_cluster["lines"].add(line_index)

    return clusters


# ============================================================
# COLUMN ALIGNMENT
# ============================================================

def _calculate_column_alignment(
    lines: List[List[Dict]]
) -> float:

    if len(lines) < 3:
        return 0.0

    clusters = _cluster_x_positions(lines)

    if not clusters:
        return 0.0

    line_count = len(lines)

    strong_columns = 0

    for cluster in clusters:

        appearances = len(
            cluster["lines"]
        )

        if appearances >= max(
            3,
            int(line_count * 0.60)
        ):
            strong_columns += 1

    # TABLE requires at least 3 repeated columns.
    if strong_columns < 3:
        return 0.0

    return min(
        strong_columns / len(clusters),
        1.0
    )


# ============================================================
# ROW CONSISTENCY
# ============================================================

def _calculate_row_consistency(
    lines: List[List[Dict]]
) -> float:

    if len(lines) < 2:
        return 0.0

    counts = [
        len(line)
        for line in lines
        if line
    ]

    if not counts:
        return 0.0

    average = mean(counts)

    if average == 0:
        return 0.0

    deviations = [
        abs(count - average) / average
        for count in counts
    ]

    return max(
        0.0,
        1.0 - mean(deviations)
    )


# ============================================================
# HORIZONTAL ROW ALIGNMENT
# ============================================================

def _calculate_horizontal_alignment(
    line_info: List[Dict]
) -> float:

    if len(line_info) < 3:
        return 0.0

    lefts = [
        line["left"]
        for line in line_info
    ]

    rights = [
        line["right"]
        for line in line_info
    ]

    avg_left = mean(lefts)
    avg_right = mean(rights)

    span = avg_right - avg_left

    if span <= 0:
        return 0.0

    left_deviation = mean(
        abs(value - avg_left)
        for value in lefts
    )

    right_deviation = mean(
        abs(value - avg_right)
        for value in rights
    )

    left_score = max(
        0.0,
        1.0 - left_deviation / span
    )

    right_score = max(
        0.0,
        1.0 - right_deviation / span
    )

    return (
        left_score + right_score
    ) / 2


# ============================================================
# VERTICAL SPACING CONSISTENCY
# ============================================================

def _calculate_spacing_consistency(
    line_info: List[Dict]
) -> float:

    if len(line_info) < 3:
        return 0.0

    centers = sorted(
        (
            line["top"] + line["bottom"]
        ) / 2
        for line in line_info
    )

    gaps = [
        centers[index + 1] - centers[index]
        for index in range(len(centers) - 1)
    ]

    if not gaps:
        return 0.0

    average = mean(gaps)

    if average <= 0:
        return 0.0

    deviations = [
        abs(gap - average) / average
        for gap in gaps
    ]

    return max(
        0.0,
        1.0 - mean(deviations)
    )


# ============================================================
# AVERAGE WORDS PER ROW
# ============================================================

def _calculate_average_words_per_line(
    line_info: List[Dict]
) -> float:

    if not line_info:
        return 0.0

    return mean(
        line["word_count"]
        for line in line_info
    )


# ============================================================
# LAYOUT CLASSIFICATION
# ============================================================

def classify_layout(
    words: List[Dict]
) -> str:

    if not words:
        return FREE_FORM

    lines = _group_into_lines(words)

    line_info = _line_information(lines)

    if not line_info:
        return FREE_FORM

    # --------------------------------------------------------
    # FORM
    # --------------------------------------------------------

    key_value_count = _count_key_value_lines(
        line_info
    )

    if key_value_count >= 2:
        return FORM

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    column_alignment = _calculate_column_alignment(
        lines
    )

    row_consistency = _calculate_row_consistency(
        lines
    )

    horizontal_alignment = _calculate_horizontal_alignment(
        line_info
    )

    spacing_consistency = _calculate_spacing_consistency(
        line_info
    )

    average_words_per_line = _calculate_average_words_per_line(
        line_info
    )

    # --------------------------------------------------------
    # TABLE
    # --------------------------------------------------------

    if (
        len(line_info) >= 3
        and average_words_per_line >= 3
        and column_alignment >= 0.50
        and row_consistency >= 0.55
    ):
        return TABLE

    # --------------------------------------------------------
    # ROW REGISTER
    #
    # IMPORTANT:
    # A row register must contain multiple words/fields
    # per row. This prevents scattered single-word layouts
    # from being incorrectly classified as ROW_REGISTER.
    # --------------------------------------------------------

    if (
        len(line_info) >= 3
        and average_words_per_line >= 2
        and row_consistency >= 0.60
        and horizontal_alignment >= 0.70
        and spacing_consistency >= 0.55
    ):
        return ROW_REGISTER

    # --------------------------------------------------------
    # FREE FORM
    # --------------------------------------------------------

    return FREE_FORM


# ============================================================
# DOCUMENT ANALYSIS
# ============================================================

def analyze_layout(
    words: List[Dict]
) -> Dict:

    lines = _group_into_lines(words)

    line_info = _line_information(lines)

    layout_type = classify_layout(words)

    return {
        "layout_type": layout_type,

        "statistics": {
            "word_count": len(words),

            "line_count": len(lines),

            "key_value_lines": _count_key_value_lines(
                line_info
            ),

            "column_alignment": round(
                _calculate_column_alignment(lines),
                3
            ),

            "row_consistency": round(
                _calculate_row_consistency(lines),
                3
            ),

            "horizontal_alignment": round(
                _calculate_horizontal_alignment(
                    line_info
                ),
                3
            ),

            "spacing_consistency": round(
                _calculate_spacing_consistency(
                    line_info
                ),
                3
            ),

            "average_words_per_line": round(
                _calculate_average_words_per_line(
                    line_info
                ),
                3
            ),
        },

        "lines": line_info,
    }