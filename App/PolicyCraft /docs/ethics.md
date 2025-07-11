# Aspekty etyczne PolicyCraft

PolicyCraft służy do analizy polityk uniwersyteckich dotyczących generatywnej AI. Poniżej podsumowujemy kluczowe zagadnienia etyczne projektu.

## 1. Unikanie stronniczości (Bias)
* Model hybrydowy wykorzystuje proste słowa kluczowe oraz wytrenowany klasyfikator LR na niewielkim korpusie.
* Ryzyko: nadreprezentacja terminologii uczelni anglojęzycznych.
* Mitigacja: testy na różnych typach instytucji (USA, UK, PL, JP) oraz wskaźnik **fairness** w skrypcie `evaluate_models.py`.

## 2. Prywatność i ochrona danych
* System nie gromadzi danych osobowych studentów / pracowników.
* Analizowane pliki polityk są publicznie dostępne.
* Dane użytkowników (loginy) przechowywane lokalnie w SQLite, hasła haszowane Bcrypt.

## 3. Bezpieczeństwo modeli
* Brak zewnętrznych API – cały inference lokalnie.
* Modele i reguły są przejrzyste (interpretowalność poprzez endpoint `/api/explain/<id>`).

## 4. Transparentność
* Kod open-source (MIT).  
* Diagram architektury w `docs/architecture.md`.

## 5. Odpowiedzialne wykorzystanie
System nie zastępuje ocen eksperta; wyniki należy interpretować w kontekście polityki i kultury danej uczelni.

---
_Data: 2025-07-11, Autor: Jacek Robert Kszczot_
