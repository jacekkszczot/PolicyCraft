# WCAG 2.1 Checklist (AA)

| Criterion | Description | Status | Evidence |
|-----------|------|--------|-------|
| 1.1.1 Alternative text | All images include an `alt` attribute. | ✅ | `templates/*.html` uses `alt` |
| 1.3.1 Information and relationships | Semantic HTML tags (headings, lists). | ✅ | Heading structure in `dashboard.html`. |
| 1.4.3 Contrast (minimum) | Text-to-background contrast ≥ 4.5:1. | ⚠️ | Check colours in `base.css` (#2c3e50 vs #ffffff). |
| 2.1.1 Keyboard | All functionality is keyboard-accessible. | ✅ | Forms and buttons support `tabindex`. |
| 2.4.1 Skip link | “Skip to main content” link added. | ✅ | `base.html` header. |
| 2.4.4 Link titles | Descriptive links without “click here”. | ✅ | Examples in the side menu. |
| 3.3.1 Input errors | Form fields include labels and error messages. | ✅ | `login.html`, `upload.html`. |
| 4.1.2 Name, Role, Value | Interactive elements have correct ARIA/HTML. | ✅ | `dashboard.html` Plotly charts. |

Legend: ✅ compliant, ⚠️ partially, ❌ not compliant.

Notes:
* Contrast of secondary buttons may need adjustment (#95a5a6 vs #ffffff gives 3.0:1).
* Check responsiveness on small mobile devices (<320 px).

_Data: 2025-07-11_
