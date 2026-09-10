import re
from typing import Dict, List, Tuple

from ocr.structured_ocr import SUPPORTED_LANGUAGES


LANGUAGE_MARKERS = {
    "eng": {
        "customer", "date", "product", "amount",
        "city", "status", "information", "paid"
    },
    "deu": {
        "kunde", "datum", "produkt", "betrag",
        "stadt", "status", "informationen", "bezahlt"
    },
    "spa": {
        "cliente", "fecha", "producto", "importe",
        "ciudad", "estado", "información", "pagado"
    },
    "fra": {
        "client", "date", "produit", "montant",
        "ville", "statut", "informations", "payé"
    },
    "ita": {
        "cliente", "data", "prodotto", "importo",
        "città", "stato", "informazioni", "pagato"
    },
    "por": {
        "cliente", "data", "produto", "valor",
        "cidade", "status", "informações", "pago"
    },
    "nld": {
        "klant", "datum", "product", "bedrag",
        "stad", "status", "informatie", "betaald"
    },
    "rus": {
        "клиент", "дата", "товар", "сумма",
        "город", "статус", "информация", "оплачено"
    },
    "ukr": {
        "клієнт", "дата", "товар", "сума",
        "місто", "статус", "інформація", "оплачено"
    },
    "pol": {
        "klient", "data", "produkt", "kwota",
        "miasto", "status", "informacje", "zapłacono"
    },
    "tur": {
        "müşteri", "tarih", "ürün", "tutar",
        "şehir", "durum", "bilgileri", "ödendi"
    },
    "ell": {
        "πελάτης", "ημερομηνία", "προϊόν", "ποσό",
        "πόλη", "κατάσταση", "πληροφορίες", "πληρωμένο"
    },
    "hin": {
        "ग्राहक", "दिनांक", "तारीख", "उत्पाद",
        "राशि", "शहर", "स्थिति", "जानकारी", "भुगतान"
    },
    "mar": {
        "ग्राहक", "दिनांक", "उत्पादन", "रक्कम",
        "शहर", "स्थिती", "माहिती", "भरले"
    },
    "ben": {
        "গ্রাহক", "তারিখ", "পণ্য", "পরিমাণ",
        "শহর", "অবস্থা", "তথ্য", "পরিশোধিত"
    },
    "tam": {
        "வாடிக்கையாளர்", "தேதி", "தயாரிப்பு", "தொகை",
        "நகரம்", "நிலை", "தகவல்", "செலுத்தப்பட்டது"
    },
    "tel": {
        "కస్టమర్", "తేదీ", "ఉత్పత్తి", "మొత్తం",
        "నగరం", "స్థితి", "సమాచారం", "చెల్లించబడింది"
    },
    "guj": {
        "ગ્રાહક", "તારીખ", "ઉત્પાદન", "રકમ",
        "શહેર", "સ્થિતિ", "માહિતી", "ચૂકવેલ"
    },
    "kan": {
        "ಗ್ರಾಹಕ", "ದಿನಾಂಕ", "ಉತ್ಪನ್ನ", "ಮೊತ್ತ",
        "ನಗರ", "ಸ್ಥಿತಿ", "ಮಾಹಿತಿ", "ಪಾವತಿಸಲಾಗಿದೆ"
    },
    "mal": {
        "ഉപഭോക്താവ്", "തീയതി", "ഉൽപ്പന്നം", "തുക",
        "നഗരം", "നില", "വിവരങ്ങൾ", "അടച്ചു"
    },
}


SCRIPT_RANGES = {
    "cyrillic": (
        "\u0400-\u04FF"
    ),
    "greek": (
        "\u0370-\u03FF"
    ),
    "devanagari": (
        "\u0900-\u097F"
    ),
    "bengali": (
        "\u0980-\u09FF"
    ),
    "tamil": (
        "\u0B80-\u0BFF"
    ),
    "telugu": (
        "\u0C00-\u0C7F"
    ),
    "gujarati": (
        "\u0A80-\u0AFF"
    ),
    "kannada": (
        "\u0C80-\u0CFF"
    ),
    "malayalam": (
        "\u0D00-\u0D7F"
    ),
}


SCRIPT_LANGUAGE_MAP = {
    "cyrillic": {"rus", "ukr"},
    "greek": {"ell"},
    "devanagari": {"hin", "mar"},
    "bengali": {"ben"},
    "tamil": {"tam"},
    "telugu": {"tel"},
    "gujarati": {"guj"},
    "kannada": {"kan"},
    "malayalam": {"mal"},
    "latin": {
        "eng", "deu", "spa", "fra",
        "ita", "por", "nld", "pol", "tur"
    },
}


def _normalize_text(text: str) -> List[str]:
    """
    Normalize OCR text into lowercase words.
    """

    return [
        word.strip(".,:;!?()[]{}<>\"'").lower()
        for word in text.split()
        if word.strip()
    ]


def _detect_script(text: str) -> Tuple[str, float]:
    """
    Detect the dominant writing system.

    Returns:
        script name
        script confidence
    """

    if not text.strip():
        return "latin", 0.0

    counts = {
        "cyrillic": 0,
        "greek": 0,
        "devanagari": 0,
        "bengali": 0,
        "tamil": 0,
        "telugu": 0,
        "gujarati": 0,
        "kannada": 0,
        "malayalam": 0,
        "latin": 0,
    }

    letters = 0

    for character in text:

        if character.isalpha():
            letters += 1

        for script, pattern in SCRIPT_RANGES.items():

            if re.match(
                f"[{pattern}]",
                character,
            ):
                counts[script] += 1
                break
        else:
            if character.isalpha():
                counts["latin"] += 1

    if letters == 0:
        return "latin", 0.0

    script = max(
        counts,
        key=counts.get,
    )

    confidence = (
        counts[script] / letters
    ) * 100

    return script, round(confidence, 2)


def _score_languages(
    words: List[str],
    candidates: set,
) -> Dict[str, Dict]:
    """
    Score only languages compatible with the detected script.
    """

    scores = {}

    for language in candidates:

        markers = LANGUAGE_MARKERS.get(
            language,
            set(),
        )

        matches = set(words) & markers

        scores[language] = {
            "score": len(matches),
            "matches": sorted(matches),
        }

    return scores


def detect_language_from_text(text: str) -> Dict:
    """
    Detect the most likely language from document text.

    Detection process:

        1. Normalize text
        2. Detect writing system
        3. Restrict language candidates
        4. Match language-specific markers
        5. Calculate confidence
    """

    words = _normalize_text(text)

    if not words:

        return {
            "language": "eng",
            "language_name": SUPPORTED_LANGUAGES["eng"],
            "confidence": 0.0,
            "script": "latin",
            "script_confidence": 0.0,
            "matched_markers": [],
        }

    script, script_confidence = _detect_script(text)

    candidates = SCRIPT_LANGUAGE_MAP.get(
        script,
        set(SUPPORTED_LANGUAGES.keys()),
    )

    scores = _score_languages(
        words,
        candidates,
    )

    best_language = max(
        scores,
        key=lambda language: scores[language]["score"],
    )

    best_score = scores[best_language]["score"]

    if best_score == 0:

        return {
            "language": (
                next(iter(candidates))
                if candidates
                else "eng"
            ),
            "language_name": SUPPORTED_LANGUAGES[
                next(iter(candidates))
            ]
            if candidates
            else SUPPORTED_LANGUAGES["eng"],
            "confidence": 0.0,
            "script": script,
            "script_confidence": script_confidence,
            "matched_markers": [],
        }

    candidate_marker_count = max(
        len(LANGUAGE_MARKERS[best_language]),
        1,
    )

    marker_confidence = (
        best_score / candidate_marker_count
    ) * 100

    confidence = (
        marker_confidence * 0.7
        + script_confidence * 0.3
    )

    confidence = min(
        max(confidence, 0.0),
        100.0,
    )

    return {
        "language": best_language,
        "language_name": SUPPORTED_LANGUAGES[
            best_language
        ],
        "confidence": round(confidence, 2),
        "script": script,
        "script_confidence": script_confidence,
        "matched_markers": scores[
            best_language
        ]["matches"],
    }


def detect_language_from_words(
    words: List[Dict],
) -> Dict:
    """
    Detect language from structured OCR words.
    """

    text = " ".join(
        word.get("text", "")
        for word in words
        if word.get("text")
    )

    return detect_language_from_text(text)


def get_language_candidates(
    text: str,
    limit: int = 5,
) -> List[Tuple[str, int]]:
    """
    Return strongest language candidates.
    """

    words = _normalize_text(text)

    script, _ = _detect_script(text)

    candidates = SCRIPT_LANGUAGE_MAP.get(
        script,
        set(SUPPORTED_LANGUAGES.keys()),
    )

    scores = []

    for language in candidates:

        markers = LANGUAGE_MARKERS.get(
            language,
            set(),
        )

        matches = set(words) & markers

        scores.append(
            (
                language,
                len(matches),
            )
        )

    scores.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return scores[:limit]


if __name__ == "__main__":

    print("========================================")
    print("       INTELLICAPTURE LANGUAGE DETECTOR")
    print("========================================")

    test_documents = {
        "English": """
        CUSTOMER INFORMATION

        Customer: Rahul Patil
        Date: 14/08/2026
        Product: Laptop
        Amount: 55000
        City: Nagpur
        Status: Paid
        """,

        "German": """
        KUNDENINFORMATION

        Kunde: Rahul Patil
        Datum: 14/08/2026
        Produkt: Laptop
        Betrag: 55000
        Stadt: Nagpur
        Status: Bezahlt
        """,

        "Spanish": """
        INFORMACIÓN DEL CLIENTE

        Cliente: Rahul Patil
        Fecha: 14/08/2026
        Producto: Laptop
        Importe: 55000
        Ciudad: Nagpur
        Estado: Pagado
        """,

        "French": """
        INFORMATIONS CLIENT

        Client: Rahul Patil
        Date: 14/08/2026
        Produit: Laptop
        Montant: 55000
        Ville: Nagpur
        Statut: Payé
        """,
    }

    print()

    for expected, text in test_documents.items():

        result = detect_language_from_text(text)

        print(
            f"{expected:10} -> "
            f"{result['language_name']} "
            f"({result['language']}) | "
            f"Confidence: "
            f"{result['confidence']}% | "
            f"Script: "
            f"{result['script']} "
            f"({result['script_confidence']}%)"
        )

        print(
            "  Markers: "
            + ", ".join(
                result["matched_markers"]
            )
        )

    print()
    print("Supported languages:")

    for code, name in SUPPORTED_LANGUAGES.items():
        print(f"  {code}: {name}")

    print()
    print("========================================")