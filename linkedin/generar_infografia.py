"""Infografía estática de 1080×1350 px con tres gráficas estadísticas del análisis, hecha con Plotly y Kaleido.

Cada panel usa los datos procesados del proyecto, sin recalcular resultados (../data/processed/):
1. Lata de 355 ml: distribución de la prima de Coca-Cola sobre Pepsi tienda por tienda (pares_lata.csv), con los mismos
   cortes del histograma del reporte (−10 a 40%, cada 2.5 puntos) y la mediana de resultados.json.
2. Botella familiar por litro: prima por cadena con IC90 (prima_desglose.csv), como en la gráfica 03 del análisis.
3. Botella familiar por envase: diferencia de lo que se paga por botella, tienda por tienda (pares_familiar.csv, columnas
   pesos_a = Pepsi 3 L y pesos_b = Coca-Cola 2.75 L).
Colores del proyecto: verde = positivo (Coca-Cola más cara), rojo = negativo (más barata), dorado = referencia.

Uso: python generar_infografia.py   (requiere plotly, kaleido, pandas, numpy)
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

AQUI = Path(__file__).resolve().parent
PROY = AQUI.parent
sys.path.insert(0, str(PROY / "src"))
import charts as C  # noqa: E402  (paleta del proyecto)

PROC = PROY / "data/processed"
SALIDA = AQUI / "infografia_coca_cola_pepsi.png"

# ----------------------------------------------------------------------------- datos (solo lectura)
RES = {k: v["cifra"] for k, v in json.loads((PROC / "resultados.json").read_text(encoding="utf-8")).items()}
PL = pd.read_csv(PROC / "pares_lata.csv")
PF = pd.read_csv(PROC / "pares_familiar.csv")
DES = pd.read_csv(PROC / "prima_desglose.csv")
CAD = DES[(DES.comparacion == "familiar") & (DES.por == "formato")].sort_values("brecha_pct", ascending=False)
ENV = (PF.pesos_b / PF.pesos_a - 1) * 100          # Coca-Cola 2.75 L frente a Pepsi 3 L, por botella
PCT_MAS_BARATA = (ENV < 0).mean() * 100
PCT_IGUAL = (ENV == 0).mean() * 100
PCT_MAS_CARA = (ENV > 0).mean() * 100

# ----------------------------------------------------------------------------- diseño
W, H = 1080, 1350
FONT = "Segoe UI, Arial, sans-serif"
BG, PANEL = C.FIG, C.BOX
TXT, TXT2, MUTED = C.TEXT, C.TEXT2, C.MUTED
GREEN, RED, GOLD, NEUTRAL, GREEN_T, RED_T = C.GREEN, C.RED, C.GOLD, C.NEUTRAL, C.GREEN_T, C.RED_T
XDOM = [0.25, 0.745]                              # ancho común de las tres gráficas
PLOT = {1: (276, 424), 2: (584, 804), 3: (964, 1114)}   # alto de cada gráfica en px (arriba, abajo)
HEAD = {1: 158, 2: 466, 3: 846}                    # arriba de cada encabezado de panel
FOOT = "Fuente: Profeco, Quién es Quién en los Precios, agosto de 2026. Cálculos propios."
FIRMA = "Ernesto Roldán | Business Intelligence · Pricing · Análisis económico"


def mxn(v, dec=2):
    return f"&#36;{v:,.{dec}f}"                      # «&#36;» evita que Plotly lea dos «$» como fórmula


def sgn(v, dec=1, pct=True):
    s = f"{abs(v):.{dec}f}" + ("%" if pct else "")
    return ("+" if v > 0 else "−") + s


def dom(i):
    top, bot = PLOT[i]
    return [1 - bot / H, 1 - top / H]


def ann(fig, x_px, y_px, text, size, color=TXT, bold=False, xanchor="left", yanchor="top", align="left", **kw):
    fig.add_annotation(xref="paper", yref="paper", x=x_px / W, y=1 - y_px / H, xanchor=xanchor, yanchor=yanchor,
                       align=align, showarrow=False, text=f"<b>{text}</b>" if bold else text,
                       font=dict(family=FONT, size=size, color=color), **kw)


def encabezado(fig, i, titulo, l1, l2):
    ann(fig, 40, HEAD[i], titulo, 32, TXT, bold=True)
    ann(fig, 40, HEAD[i] + 45, l1, 24, TXT2)
    ann(fig, 40, HEAD[i] + 76, l2, 24, TXT2)


def hero(fig, i, grande, color, lineas):
    """Cifra grande a la derecha de la gráfica, centrada en su alto, con una línea de unidad por renglón."""
    total = 56 + 29 * len(lineas)
    top = (PLOT[i][0] + PLOT[i][1]) / 2 - total / 2
    ann(fig, 853, top, grande, 46, color, bold=True)
    ann(fig, 853, top + 58, "<br>".join(lineas), 22, TXT2)


def linea(fig, xref, i, x, color, dash, width=2):
    y0, y1 = dom(i)
    fig.add_shape(type="line", xref=xref, yref="paper", x0=x, x1=x, y0=y0, y1=y1, layer="above",
                  line=dict(color=color, width=width, dash=dash))


def eje(**kw):
    base = dict(gridcolor=C.GRID, zeroline=False, showline=True, linecolor=C.AXIS, tickfont=dict(size=22, color=TXT2))
    base.update(kw)
    return base


def hist_tienda(fig, eje_n, edges, valores, colores_por_centro, ymax_ticks):
    cnt = np.histogram(valores, bins=edges)[0] / len(valores) * 100
    mids = (edges[:-1] + edges[1:]) / 2
    fig.add_trace(go.Bar(x=mids, y=cnt, width=np.diff(edges), xaxis=f"x{eje_n}", yaxis=f"y{eje_n}", hoverinfo="skip",
                         marker=dict(color=[colores_por_centro(m) for m in mids], line=dict(color=BG, width=1))))
    top = cnt.max() * 1.32
    return top, list(range(0, int(top) + 1, 20))


def construir():
    fig = go.Figure()
    prima, mediana_env = RES["prima_lata"], RES["fam_empaque"]

    # --- panel 1: lata
    top1, ticks1 = hist_tienda(fig, "", np.arange(-10, 42.5, 2.5), PL.prima_pct.clip(-10, 39.99).to_numpy(),
                               lambda m: RED if m < 0 else GREEN, None)
    # --- panel 3: botella por envase (los envases con el mismo precio van en gris)
    neg, pos = ENV[ENV < 0], ENV[ENV > 0]
    n = len(ENV)
    e_neg, e_pos = np.arange(-25, 0.01, 2.5), np.arange(0, 22.6, 2.5)
    for valores, edges, col in [(neg, e_neg, RED), (pos, e_pos, GREEN)]:
        cnt = np.histogram(valores, bins=edges)[0] / n * 100
        fig.add_trace(go.Bar(x=(edges[:-1] + edges[1:]) / 2, y=cnt, width=2.5, xaxis="x3", yaxis="y3", hoverinfo="skip",
                             marker=dict(color=col, line=dict(color=BG, width=1))))
    fig.add_trace(go.Bar(x=[0], y=[PCT_IGUAL], width=1.0, xaxis="x3", yaxis="y3", hoverinfo="skip",
                         marker=dict(color=NEUTRAL, line=dict(color=BG, width=1))))
    cnt_max3 = max(np.histogram(neg, bins=e_neg)[0].max(), np.histogram(pos, bins=e_pos)[0].max()) / n * 100
    top3 = cnt_max3 * 1.32
    ticks3 = list(range(0, int(top3) + 1, 20))

    # --- panel 2: prima por litro por cadena, con IC90
    nombres = [g for g in CAD.grupo]
    for r in CAD.itertuples():
        col = GREEN if r.ic90_inf > 0 else (RED if r.ic90_sup < 0 else NEUTRAL)
        fig.add_trace(go.Scatter(x=[r.ic90_inf, r.ic90_sup], y=[r.grupo, r.grupo], mode="lines", xaxis="x2", yaxis="y2",
                                 line=dict(color=col, width=16), opacity=0.45, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=[r.brecha_pct], y=[r.grupo], mode="markers", xaxis="x2", yaxis="y2", hoverinfo="skip",
                                 marker=dict(symbol="diamond", size=24, color=col, line=dict(color=TXT, width=1.5))))
        txt_col = GREEN_T if r.ic90_inf > 0 else (RED_T if r.ic90_sup < 0 else TXT2)
        arrow = "▲ " if r.ic90_inf > 0 else ("▼ " if r.ic90_sup < 0 else "")
        fig.add_trace(go.Scatter(x=[max(r.ic90_sup, r.brecha_pct) + 0.9], y=[r.grupo], mode="text", xaxis="x2",
                                 yaxis="y2", hoverinfo="skip", cliponaxis=False, textposition="middle right",
                                 text=[f"<b>{arrow}{sgn(r.brecha_pct)}</b>"],
                                 textfont=dict(family=FONT, size=24, color=txt_col)))

    fig.update_layout(
        width=W, height=H, paper_bgcolor=BG, plot_bgcolor=BG, showlegend=False, margin=dict(l=0, r=0, t=0, b=0),
        font=dict(family=FONT, size=22, color=TXT2), bargap=0,
        xaxis=eje(domain=XDOM, anchor="y", range=[-10, 40], dtick=10, ticksuffix="%"),
        yaxis=eje(domain=dom(1), anchor="x", range=[0, top1], tickvals=ticks1, ticktext=[f"{t}%" for t in ticks1]),
        xaxis2=eje(domain=XDOM, anchor="y2", range=[-10, 24], dtick=10, ticksuffix="%"),
        yaxis2=eje(domain=dom(2), anchor="x2", type="category", categoryorder="array", categoryarray=nombres,
                   range=[len(nombres) - 0.5, -0.5], gridcolor="rgba(0,0,0,0)", tickfont=dict(size=24, color=TXT)),
        xaxis3=eje(domain=XDOM, anchor="y3", range=[-25, 22.5], dtick=10, ticksuffix="%"),
        yaxis3=eje(domain=dom(3), anchor="x3", range=[0, top3], tickvals=ticks3, ticktext=[f"{t}%" for t in ticks3]))

    # referencias: 0 = mismo precio que Pepsi; dorado = mediana
    linea(fig, "x", 1, 0, TXT2, "dot")
    linea(fig, "x", 1, prima, GOLD, "solid", 3)
    linea(fig, "x2", 2, 0, GOLD, "dash", 2)
    linea(fig, "x3", 3, 0, TXT2, "dot")
    linea(fig, "x3", 3, mediana_env, GOLD, "solid", 3)
    for xr, i, x, top in [("x", 1, prima, top1), ("x3", 3, mediana_env, top3)]:
        fig.add_annotation(xref=xr, yref="paper", x=x, y=dom(i)[1], xanchor="right", yanchor="top", xshift=-8, yshift=-4,
                           showarrow=False, text="mediana", font=dict(family=FONT, size=22, color=GOLD))

    # --- textos
    ann(fig, 40, 18, "Coca-Cola vs. Pepsi: el precio<br>cambia según la presentación", 40, TXT, bold=True)
    ann(fig, 40, 124, "Misma tienda · supermercados monitoreados por Profeco · 16–31 de agosto de 2026", 22, TXT2)

    encabezado(fig, 1, "1 · Latas de 355 ml", f"Coca-Cola frente a Pepsi en la misma tienda · {RES['pares_lata']:.0f} supermercados",
               "Barras: % de tiendas · línea punteada: mismo precio que Pepsi")
    hero(fig, 1, sgn(prima), GREEN_T, ["prima de precio", "(mediana)", f"{sgn(RES['pesos_lata'], 2, False).replace('+', '+&#36;')} típico"])
    encabezado(fig, 2, "2 · Botella familiar, por litro", f"Coca-Cola 2.75 L vs. Pepsi 3 L · {RES['pares_familiar']:.0f} supermercados",
               "Rango probable (IC90) por cadena · gris: cruza 0 · dorada: mismo precio")
    hero(fig, 2, sgn(RES["prima_familiar"]), GREEN_T, ["prima por litro", "(mediana)"])
    encabezado(fig, 3, "3 · Botella familiar, por envase",
               f"Tamaños distintos: Coca-Cola 2.75 L ({mxn(RES['fam_coca'])}) vs. Pepsi 3 L ({mxn(RES['fam_pepsi'])})",
               f"Coca-Cola más barata en {PCT_MAS_BARATA:.0f}% de las tiendas · igual en {PCT_IGUAL:.0f}% · más cara en {PCT_MAS_CARA:.0f}%")
    hero(fig, 3, sgn(mediana_env), RED_T, ["por botella", "(mediana)"])

    # --- conclusión, fuente y firma
    fig.add_shape(type="rect", xref="paper", yref="paper", x0=40 / W, x1=1040 / W, y0=1 - 1236 / H, y1=1 - 1156 / H,
                  fillcolor=PANEL, line=dict(color=GOLD, width=2))
    ann(fig, W / 2, 1196, "El resultado cambia según la presentación<br>y la unidad de comparación", 28, TXT, bold=True,
        xanchor="center", yanchor="middle", align="center")
    ann(fig, 40, 1264, FOOT, 20, MUTED, yanchor="middle")
    ann(fig, 40, 1296, FIRMA, 20, TXT2, yanchor="middle")
    return fig


if __name__ == "__main__":
    construir().write_image(SALIDA, width=W, height=H, scale=1)
    print(f"{SALIDA.name}: {W}×{H} px")
