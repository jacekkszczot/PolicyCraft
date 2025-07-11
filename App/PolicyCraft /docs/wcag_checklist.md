# WCAG 2.1 Checklist (AA)

| Kryterium | Opis | Status | Dowód |
|-----------|------|--------|-------|
| 1.1.1 Tekst alternatywny | Wszystkie obrazy mają atrybut `alt`. | ✅ | `templates/*.html` używa `alt` |
| 1.3.1 Informacje i relacje | Semantyczne tagi HTML (nagłówki, listy). | ✅ | Struktura nagłówków w `dashboard.html`. |
| 1.4.3 Kontrast (minimum) | Kontrast tekst:tło ≥ 4.5:1. | ⚠️ | Sprawdź kolory w `base.css` (#2c3e50 vs #ffffff). |
| 2.1.1 Klawiatura | Wszystkie funkcje dostępne z klawiatury. | ✅ | Formularze i przyciski obsługują `tabindex`. |
| 2.4.1 Blokuj pomijanie | Link “Skip to main content” dodany. | ✅ | `base.html` nagłówek. |
| 2.4.4 Tytuły linków | Linki opisowe, bez „kliknij tutaj”. | ✅ | Przykłady w menu bocznym. |
| 3.3.1 Błędy wejścia | Pola formularza posiadają etykiety i komunikaty błędów. | ✅ | `login.html`, `upload.html`. |
| 4.1.2 Nazwa, Rola, Wartość | Elementy interaktywne mają poprawny ARIA/HTML. | ✅ | `dashboard.html` wykresy Plotly. |

Legenda: ✅ spełnione, ⚠️ częściowo, ❌ niespełnione.

Notatki:
* Kontrast przycisków sekundarnych wymaga ew. poprawy (#95a5a6 vs #ffffff daje 3.0:1).
* Sprawdź responsywność na urządzeniach mobilnych (<320 px).

_Data: 2025-07-11_
