--- app.py
+++ app.py
@@
 import streamlit as st
 import pandas as pd
 import numpy as np
 import plotly.graph_objects as go
 from io import BytesIO
 from scipy.signal import argrelextrema
 import ta
+from docx import Document
+from reportlab.platypus import (
+    SimpleDocTemplate,
+    Paragraph,
+    Spacer
+)
+from reportlab.lib.styles import (
+    getSampleStyleSheet
+)

@@
 st.title("📈 MASI PRO V7")

+st.sidebar.header("Paramètres techniques")
+
+sma_short = st.sidebar.slider(
+    "SMA courte",
+    5,
+    100,
+    20
+)
+
+sma_medium = st.sidebar.slider(
+    "SMA moyenne",
+    20,
+    150,
+    50
+)
+
+sma_long = st.sidebar.slider(
+    "SMA longue",
+    50,
+    400,
+    200
+)
+
+rsi_period = st.sidebar.slider(
+    "RSI",
+    5,
+    30,
+    14
+)
+
+macd_fast = st.sidebar.slider(
+    "MACD rapide",
+    5,
+    20,
+    12
+)
+
+macd_slow = st.sidebar.slider(
+    "MACD lente",
+    20,
+    40,
+    26
+)
+
+macd_signal = st.sidebar.slider(
+    "Signal MACD",
+    5,
+    15,
+    9
+)

@@
-@st.cache_data
-def prepare(df):
-
-    d = df.copy()
-
-    d["SMA20"] = ta.trend.sma_indicator(d["Close"], 20)
-    d["SMA50"] = ta.trend.sma_indicator(d["Close"], 50)
-    d["SMA200"] = ta.trend.sma_indicator(d["Close"], 200)

@@
 @st.cache_data
-def prepare(df):
+def prepare(
+    df,
+    sma_short,
+    sma_medium,
+    sma_long,
+    rsi_period,
+    macd_fast,
+    macd_slow,
+    macd_signal
+):

     d = df.copy()

-    d["SMA20"] = ta.trend.sma_indicator(d["Close"], 20)
-    d["SMA50"] = ta.trend.sma_indicator(d["Close"], 50)
-    d["SMA200"] = ta.trend.sma_indicator(d["Close"], 200)
+    d["SMA_SHORT"] = ta.trend.sma_indicator(
+        d["Close"],
+        sma_short
+    )
+
+    d["SMA_MEDIUM"] = ta.trend.sma_indicator(
+        d["Close"],
+        sma_medium
+    )
+
+    d["SMA_LONG"] = ta.trend.sma_indicator(
+        d["Close"],
+        sma_long
+    )

-    d["RSI"] = calculate_excel_rsi(d["Close"], 14)
+    d["RSI"] = calculate_excel_rsi(
+        d["Close"],
+        rsi_period
+    )

-    macd = ta.trend.MACD(d["Close"])
+    macd = ta.trend.MACD(
+        close=d["Close"],
+        window_fast=macd_fast,
+        window_slow=macd_slow,
+        window_sign=macd_signal
+    )

@@
-    return d
-
-    macd = ta.trend.MACD(d["Close"])
-    d["MACD"] = macd.macd()
-    d["SIGNAL"] = macd.macd_signal()
-    d["HISTO"] = d["MACD"] - d["SIGNAL"]
-
-    bb = ta.volatility.BollingerBands(
-        d["Close"],
-        window=20,
-        window_dev=2
-    )
-
-    d["BB_UP"] = bb.bollinger_hband()
-    d["BB_LOW"] = bb.bollinger_lband()
-
     return d

+def generate_pdf(text):
+
+    buffer = BytesIO()
+
+    doc = SimpleDocTemplate(buffer)
+
+    styles = getSampleStyleSheet()
+
+    elements = [
+        Paragraph(
+            "NOTE AU COMITE D'INVESTISSEMENT",
+            styles["Title"]
+        ),
+        Spacer(1, 12)
+    ]
+
+    for line in text.split("\n"):
+
+        if line.strip():
+            elements.append(
+                Paragraph(
+                    line,
+                    styles["BodyText"]
+                )
+            )
+
+    doc.build(elements)
+
+    return buffer.getvalue()

@@
-    df = prepare(raw).dropna().reset_index(drop=True)
+    df = prepare(
+        raw,
+        sma_short,
+        sma_medium,
+        sma_long,
+        rsi_period,
+        macd_fast,
+        macd_slow,
+        macd_signal
+    ).dropna().reset_index(drop=True)

@@
-    score += 25 if last["Close"] > last["SMA200"] else 0
-    score += 25 if last["SMA50"] > last["SMA200"] else 0
-    score += 20 if last["SMA20"] > last["SMA50"] else 0
+    score += 25 if last["Close"] > last["SMA_LONG"] else 0
+    score += 25 if last["SMA_MEDIUM"] > last["SMA_LONG"] else 0
+    score += 20 if last["SMA_SHORT"] > last["SMA_MEDIUM"] else 0

@@
+    achat = 0
+    vente = 0
+
+    if last["Close"] > last["SMA_LONG"\]:
+        achat += 1
+    else:
+        vente += 1
+
+    if last["MACD"] > last["SIGNAL"\]:
+        achat += 1
+    else:
+        vente += 1
+
+    if last["RSI"] > 50:
+        achat += 1
+    else:
+        vente += 1

@@
     with t1:
+
+        st.warning(
+            '''
+            Cette application constitue une aide à la décision.
+
+            Elle ne constitue pas une recommandation
+            d'investissement.
+
+            Les décisions doivent être complétées par une
+            analyse fondamentale et une appréciation du risque.
+            '''
+        )

@@
-        st.plotly_chart(
-            gauge,
-            use_container_width=True
-        )
+        st.plotly_chart(
+            gauge,
+            width="stretch"
+        )

@@
-            "SMA20",
-            "SMA50",
-            "SMA200",
+            "SMA_SHORT",
+            "SMA_MEDIUM",
+            "SMA_LONG",

@@
-        st.plotly_chart(
-            fig,
-            use_container_width=True
-        )
+        st.plotly_chart(
+            fig,
+            width="stretch"
+        )

@@
-        st.plotly_chart(
-            r,
-            use_container_width=True
-        )
+        st.plotly_chart(
+            r,
+            width="stretch"
+        )

@@
-        st.plotly_chart(
-            m,
-            use_container_width=True        )
+        st.plotly_chart(
+            m,
+            width="stretch"
+        )

@@
-                    25 if last["SMA50"] > last["SMA200"] else 0,
-                    20 if last["SMA20"] > last["SMA50"] else 0,
+                    25 if last["SMA_MEDIUM"] > last["SMA_LONG"] else 0,
+                    20 if last["SMA_SHORT"] > last["SMA_MEDIUM"] else 0,

@@
-        st.plotly_chart(
-            radar,
-            use_container_width=True
-        )
+        st.plotly_chart(
+            radar,
+            width="stretch"
+        )

@@
-        st.markdown(commentaire)
+        st.markdown(commentaire)
+
+        st.subheader("Convergence des indicateurs")
+
+        st.write(
+            f"Signaux haussiers : {achat}/3"
+        )
+
+        st.write(
+            f"Signaux baissiers : {vente}/3"
+        )

@@
         st.download_button(
             "📄 Télécharger la note Comité",
             commentaire,
             "Note_Comite_MASI.txt"
         )
+
+        doc = Document()
+
+        doc.add_heading(
+            "NOTE AU COMITE D'INVESTISSEMENT",
+            0
+        )
+
+        doc.add_paragraph(commentaire)
+
+        word_buffer = BytesIO()
+
+        doc.save(word_buffer)
+
+        st.download_button(
+            "📄 Télécharger la note Word",
+            word_buffer.getvalue(),
+            "Note_Comite_MASI.docx"
+        )
+
+        pdf_buffer = generate_pdf(commentaire)
+
+        st.download_button(
+            "📕 Télécharger la note PDF",
+            pdf_buffer,
+            "Note_Comite_MASI.pdf",
+            mime="application/pdf"
+        )
