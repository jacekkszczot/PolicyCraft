# PolicyCraft Architecture

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

Module descriptions:
1. **Web UI** – HTML + CSS templates.
2. **API endpoints** – Flask logic (`app.py`).
3. **NLP pipeline** – text cleaning and feature extraction.
4. **PolicyClassifier** – hybrid rule-based + ML model.
5. **Recommendation Engine** – generates policy improvement suggestions.
6. **DatabaseOperations** – stores users (SQLite) and analyses (JSON).
7. **PDF Generator** – creates PDF reports.
8. **Visualisation** – Plotly charts.

The diagram shows the main data flows and dependencies between components.
