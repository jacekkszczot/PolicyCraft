# Architektura PolicyCraft

```mermaid
graph TD
    A[Web UI (Flask templates)] --> B(API endpoints)
    B --> C[NLP pipeline]
    C --> D[PolicyClassifier]
    C --> E[Recommendation Engine]
    B --> F[DatabaseOperations]
    F -->|JSON| G[Analyses storage]
    F -->|SQLite| H[User auth]
    B --> I[PDF Generator]
    B --> J[Visualisation]
```

Opis modułów:
1. **Web UI** – szablony HTML + CSS.
2. **API endpoints** – logika Flask (`app.py`).
3. **NLP pipeline** – czyszczenie tekstu, ekstrakcja cech.
4. **PolicyClassifier** – hybrydowy model reguły + ML.
5. **Recommendation Engine** – generuje sugestie poprawy polityki.
6. **DatabaseOperations** – przechowuje użytkowników (SQLite) i analizy (JSON).
7. **PDF Generator** – tworzy raporty PDF.
8. **Visualisation** – wykresy Plotly.

Diagram pokazuje główne przepływy danych i zależności między komponentami.
