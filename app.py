import streamlit as st
2
import pandas as pd
3
import numpy as np
4
import plotly.graph_objects as go
5
import ta
6
 
7
from io import BytesIO
8
from scipy.signal import argrelextrema
9
 
10
# =====================================================
11
# CONFIGURATION
12
# =====================================================
13
 
14
st.set_page_config(
15
page_title="MASI Pro V4",
16
page_icon="📈",
17
layout="wide"
18
)
19
 
20
st.title("📈 MASI Pro V4")
21
 
22
# =====================================================
23
# CHARGEMENT
24
# =====================================================
25
 
26
@st.cache_data
27
def load_data(file):
28
 
29
df = pd.read_excel(
30
file,
31
sheet_name="Data_masi",
32
engine="openpyxl"
33
)
34
 
35
df.columns = df.columns.str.strip()
36
 
37
df["Date"] = pd.to_datetime(
38
df["Date"],
39
errors="coerce"
40
)
41
 
42
df["Close"] = pd.to_numeric(
43
df["Close"],
44
errors="coerce"
45
)
46
 
47
df = (
48
df
49
.dropna(subset=["Date", "Close"])
50
.sort_values("Date")
51
.reset_index(drop=True)
52
)
53
 
54
return df
55
 
56
 
57
# =====================================================
58
# INDICATEURS
59
# =====================================================
60
 
61
def add_indicators(df):
62
 
63
df["SMA20"] = ta.trend.sma_indicator(
64
df["Close"],
65
window=20
66
)
67
 
68
df["SMA50"] = ta.trend.sma_indicator(
69
df["Close"],
70
window=50
71
)
72
 
73
df["SMA200"] = ta.trend.sma_indicator(
74
df["Close"],
75
window=200
76
)
77
 
78
df["RSI"] = ta.momentum.rsi(
79
df["Close"],
80
window=14
81
)
82
 
83
macd = ta.trend.MACD(df["Close"])
84
 
85
df["MACD"] = macd.macd()
86
 
87
df["SIGNAL"] = macd.macd_signal()
88
 
89
df["HISTO"] = (
90
df["MACD"]
91
- df["SIGNAL"]
92
)
93
 
94
bb = ta.volatility.BollingerBands(
95
close=df["Close"],
96
window=20,
97
window_dev=2
98
)
99
 
100
df["BB_UP"] = bb.bollinger_hband()
101
df["BB_LOW"] = bb.bollinger_lband()
102
 
103
return df
104
 
105
 
106
# =====================================================
107
# SUPPORTS / RESISTANCES
108
# =====================================================
109
 
110
def detect_sr(df):
111
 
112
prices = df["Close"].values
113
 
114
minima = argrelextrema(
115
prices,
116
np.less,
117
order=5
118
)[0]
119
 
120
maxima = argrelextrema(
121
prices,
122
np.greater,
123
order=5
124
)[0]
125
 
126
supports = prices[minima]
127
resistances = prices[maxima]
128
 
129
return supports, resistances
130
 
131
 
132
# =====================================================
133
# SCORE
134
# =====================================================
135
 
136
def calculate_score(df):
137
 
138
score = 0
139
 
140
last = df.iloc[-1]
141
 
142
if last["Close"] > last["SMA200"]:
143
score += 25
144
 
145
if last["SMA50"] > last["SMA200"]:
146
score += 25
147
 
148
if last["SMA20"] > last["SMA50"]:
149
score += 20
150
 
151
if last["MACD"] > last["SIGNAL"]:
152
score += 15
153
 
154
if 45 <= last["RSI"] <= 70:
155
score += 15
156
 
157
return min(score, 100)
158
 
159
 
160
# =====================================================
161
# BACKTEST
162
# =====================================================
163
 
164
def run_backtest(df):
165
 
166
buy_signal = (
167
(df["SMA20"] > df["SMA50"])
168
&
169
(df["MACD"] > df["SIGNAL"])
170
&
171
(df["RSI"] > 50)
172
)
173
 
174
sell_signal = (
175
(df["SMA20"] < df["SMA50"])
176
|
177
(df["MACD"] < df["SIGNAL"])
178
|
179
(df["RSI"] < 45)
180
)
181
 
182
position = False
183
entry_price = None
184
trades = []
185
 
186
for i in range(len(df)):
187
 
188
price = df["Close"].iloc[i]
189
 
190
if (not position) and buy_signal.iloc[i]:
191
 
192
position = True
193
entry_price = priceition and sell_signal.iloc[i]:
194
 
195
perf = (
196
(e)
197
/ entry_price
198
) * 100
199
 
200
trades.append(perf)
201
 
202
position = False
203
entry_price = None
204
 
205
return trades
206
 
207
 
208
# =====================================================
209
# APPLICATION
210
# =====================================================
211
 
212
uploaded_file = st.file_uploader(
213
"Importer Data_masi.xlsx",
214
type=["xlsx"]
215
)
216
 
217
if uploaded_file:
218
 
219
try:
220
 
221
df = load_data(uploaded_file)
222
 
223
df = add_indicators(df)
224
 
225
df = df.dropna()
226
 
227
score = calculate_score(df)
228
 
229
supports, resistances = detect_sr(df)
230
 
231
last = df.iloc[-1]
232
 
233
st.header("🎯 Résumé")
234
 
235
c1, c2, c3 = st.columns(3)
236
 
237
c1.metric(
238
"Cours",
239
round(last["Close"], 2)
240
)
241
 
242
c2.metric(
243
"RSI",
244
round(last["RSI"], 2)
245
)
246
 
247
c3.metric(
248
"Score",
249
score
250
)
251
 
252
# ==========================================
253
# GRAPHIQUE
254
# ==========================================
255
 
256
fig = go.Figure()
257
 
258
fig.add_trace(
259
go.Scatter(
260
x=df["Date"],
261
y=df["Close"],
262
name="MASI"
263
)
264
)
265
 
266
fig.add_trace(
267
go.Scatter(
268
x=df["Date"],
269
y=df["SMA20"],
270
name="SMA20"
271
)
272
)
273
 
274
fig.add_trace(
275
go.Scatter(
276
x=df["Date"],
277
y=df["SMA50"],
278
name="SMA50"
279
)
280
)
281
 
282
fig.add_trace(
283
go.Scatter(
284
x=df["Date"],
285
y=df["SMA200"],
286
name="SMA200"
287
)
288
)
289
 
290
fig.add_trace(
291
go.Scatter(
292
x=df["Date"],
293
y=df["BB_UP"],
294
name="BB Haut"
295
)
296
)
297
 
298
fig.add_trace(
299
go.Scatter(
300
x=df["Date"],
301
y=df["BB_LOW"],
302
name="BB Bas"
303
)
304
)
305
 
306
st.plotly_chart(
307
fig,
308
use_container_width=True
309
)
310
 
311
# ==========================================
312
# BACKTEST
313
# ==========================================
314
 
315
st.header("📊 Backtest")
316
 
317
trades = run_backtest(df)
318
 
319
if len(trades) > 0:
320
 
321
winrate = (
322
np.mean(
323
np.array(trades) > 0
324
) * 100
325
)
326
 
327
performance = sum(trades)
328
 
329
b1, b2, b3 = st.columns(3)
330
 
331
b1.metric(
332
"Trades",
333
len(trades)
334
)
335
 
336
b2.metric(
337
"Win Rate",
338
f"{winrate:.1f}%"
339
)
340
 
341
b3.metric(
342
"Performance",
343
f"{performance:.2f}%"
344
)
345
 
346
else:
347
 
348
st.warning(
349
"Aucun trade détecté."
350
)
351
 
352
# ==========================================
353
# EXPORT
354
# ==========================================
355
 
356
buffer = BytesIO()
357
 
358
with pd.ExcelWriter(
359
buffer,
360
engine="openpyxl"
361
) as writer:
362
 
363
df.to_excel(
364
writer,
365
sheet_name="Analyse",
366
index=False
367
)
368
 
369
st.
