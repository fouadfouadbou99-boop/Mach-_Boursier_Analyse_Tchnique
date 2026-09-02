# Analyse Chartiste Automatique

Application Streamlit permettant l'analyse technique des marchés financiers.

## Fonctionnalités

- Import Excel
- Graphique interactif Plotly
- Moyennes Mobiles :
  - SMA20
  - SMA50
  - SMA200
- RSI
- MACD
- Détection automatique :
  - Supports
  - Résistances

---

## Format du fichier Excel

Le fichier doit contenir au minimum :

| Date | Close |
|--------|--------|
| 2025-01-01 | 15000 |
| 2025-01-02 | 15120 |

Exemple :

Date , Close

2025-01-01 , 15000

2025-01-02 , 15120

---

## Installation locale

```bash
pip install -r requirements.txt
streamlit run app.py
