"""Secuencia animada (15 s, 1080×1080) con las cuatro gráficas del análisis Coca-Cola vs. Pepsi, en Plotly.

Fuentes de cada escena (solo lectura de ../data/processed/ y ../src/):
1. Prima en lata: la figura Plotly del reporte (src/reporte.py, histograma tienda por tienda), con sus mismos
   cortes (−10 a 40%, cada 2.5 puntos), línea de mediana y línea de cero.
2. Prima por presentación: src/graficas.py · by_presentation (filas, rombo = prima, barra = IC90, cero = Pepsi).
3. Botella familiar por cadena: src/graficas.py · family_by_format (mismas filas, IC90 y colores por signo).
4. Precio por litro: src/graficas.py · liter_ladder (presentaciones en 30 tiendas o más, colores de marca).
Las escenas 2 a 4 están hechas en matplotlib en el proyecto; aquí se trazan en Plotly con los mismos datos, filas,
intervalos, referencias y paleta, para poder animar sus elementos. No se recalcula ningún resultado.

Uso: python generar_gif.py   (requiere plotly, kaleido, pillow, imageio, imageio-ffmpeg)
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image
import io

AQUI = Path(__file__).resolve().parent
PROY = AQUI.parent
sys.path.insert(0, str(PROY / "src"))
import charts as C  # noqa: E402  (paleta del proyecto)

PROC = PROY / "data/processed"
RES = json.loads((PROC / "resultados.json").read_text(encoding="utf-8"))
V = {}
for k, x in RES.items():
    V[k] = x["cifra"]
    if x.get("intervalo"):
        V[k + "_inf"], V[k + "_sup"] = x["intervalo"]
PL = pd.read_csv(PROC / "pares_lata.csv")
DES = pd.read_csv(PROC / "prima_desglose.csv")
LAD = pd.read_csv(PROC / "precio_por_litro_presentacion.csv")

# ----------------------------------------------------------------------------- estilo (el del proyecto)
W = H = 1080
FPS = 12
COCA, PEPSI = C.TEXT2, "#5b8fd6"                  # colores de marca de src/graficas.py
FONT = "Segoe UI, Arial, sans-serif"
TITLE_PX, SUB_PX, AX_PX, LAB_PX, SMALL_PX = 36, 22, 22, 24, 18
FUENTE = "Fuente: Profeco, Quién es Quién en los Precios, 16–31 ago 2026 · Cálculos propios · Ernesto Roldán · Python + Plotly"


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def sign_col(lo, hi):
    return C.GREEN if lo > 0 else (C.RED if hi < 0 else C.NEUTRAL)


def sign_txt(v, lo, hi, dec=1):
    if lo > 0:
        return f"▲ +{v:.{dec}f}%", C.GREEN_T
    if hi < 0:
        return f"▼ −{abs(v):.{dec}f}%", C.RED_T
    return f"{v:+.{dec}f}%".replace("-", "−"), C.TEXT2


def layout(fig, title, sub, l=90, r=40, t=175, b=160):
    fig.update_layout(
        width=W, height=H, paper_bgcolor=C.FIG, plot_bgcolor=C.FIG, showlegend=False,
        font=dict(family=FONT, size=AX_PX, color=C.TEXT2), margin=dict(l=l, r=r, t=t, b=b),
        title=dict(text=f"<b>{title}</b><br><span style='font-size:{SUB_PX}px;color:{C.TEXT2}'>{sub}</span>",
                   x=0.04, xanchor="left", y=0.955, yanchor="top", font=dict(size=TITLE_PX, color=C.TEXT, family=FONT)))
    fig.add_annotation(text=FUENTE, xref="paper", yref="paper", x=0, y=0, xanchor="left", yanchor="top",
                       xshift=-(l - 40), yshift=-(b - 45), showarrow=False, font=dict(size=SMALL_PX, color=C.MUTED))
    return fig


def axis(**kw):
    base = dict(gridcolor=C.GRID, zeroline=False, linecolor=C.AXIS, tickfont=dict(size=AX_PX, color=C.TEXT2),
                title_font=dict(size=AX_PX, color=C.TEXT2))
    base.update(kw)
    return base


# ----------------------------------------------------------------------------- 1. prima en lata (figura del reporte)
EDGES = np.arange(-10, 40 + 2.5, 2.5)
HIST = np.histogram(PL.prima_pct.clip(-10, 39.99), bins=EDGES)[0] / len(PL) * 100


def escena_lata(p):
    q = ease(p / 0.7)
    mids = (EDGES[:-1] + EDGES[1:]) / 2
    fig = go.Figure(go.Bar(x=mids, y=HIST * q, width=2.5, marker=dict(color=C.GREEN, line=dict(color=C.FIG, width=1))))
    fig.add_vline(0, line=dict(color=C.TEXT2, width=1.5, dash="dot"))
    a = ease((p - 0.6) / 0.4)
    if a > 0:
        fig.add_vline(V["prima_lata"], line=dict(color=C.GOLD, width=3))
        fig.add_annotation(x=V["prima_lata"], y=HIST.max() * 1.12, text=f"<b>mediana +{V['prima_lata']:.1f}%</b><br>"
                           f"+${V['pesos_lata']:.2f} por lata", showarrow=False, xanchor="left", xshift=10, align="left",
                           font=dict(size=LAB_PX + 4, color=C.GOLD), opacity=a)
    layout(fig, f"Coca-Cola cuesta {V['prima_lata']:.1f}% más que Pepsi en lata",
           f"Prima tienda por tienda · latas de 355 ml · {V['pares_lata']:.0f} supermercados con las dos")
    fig.update_layout(bargap=0,
                      xaxis=axis(title="Coca-Cola frente a Pepsi en la misma tienda", ticksuffix="%", range=[-10, 40], dtick=10),
                      yaxis=axis(title="% de las tiendas", ticksuffix="%", range=[0, HIST.max() * 1.3]))
    return fig


# ----------------------------------------------------------------------------- filas con rombo e IC90 (escenas 2 y 3)
def filas(rows, p, title, sub, xr, xlabel, l=360, colx=None):
    k = len(rows)
    ys = list(range(k))
    fig = go.Figure()
    fig.add_vline(0, line=dict(color=C.GOLD, width=2, dash="dash"))
    colx = colx if colx is not None else xr[1] - (xr[1] - xr[0]) * 0.02
    for i, rw in enumerate(rows):
        q = ease((p - i * 0.12) / 0.55)
        col = sign_col(rw["lo"], rw["hi"])
        if q <= 0:
            continue
        lo, hi, vv = rw["lo"] * q, rw["hi"] * q, rw["v"] * q
        fig.add_trace(go.Scatter(x=[lo, hi], y=[i, i], mode="lines", line=dict(color=col, width=14), opacity=0.45))
        fig.add_trace(go.Scatter(x=[vv], y=[i], mode="markers", marker=dict(symbol="diamond", size=24, color=col,
                                                                              line=dict(color=C.TEXT, width=1.5))))
        t, tc = sign_txt(rw["v"], rw["lo"], rw["hi"])
        fig.add_annotation(x=colx, y=i, xref="x", yref="y", text=f"<b>{t}</b>", showarrow=False, xanchor="right",
                           yshift=10, font=dict(size=LAB_PX + 4, color=tc), opacity=ease((q - 0.6) / 0.4))
        fig.add_annotation(x=colx, y=i, xref="x", yref="y", text=rw["right"], showarrow=False, xanchor="right",
                           yshift=-20, font=dict(size=SMALL_PX, color=C.TEXT2), opacity=ease((q - 0.6) / 0.4))
    ticks = [f"<b>{rw['label']}</b><br><span style='font-size:{SMALL_PX}px;color:{C.TEXT2}'>{rw['sub']}</span>" for rw in rows]
    layout(fig, title, sub, l=l)
    fig.update_layout(xaxis=axis(range=xr, ticksuffix="%", title=xlabel, dtick=10 if xr[1] - xr[0] > 30 else 5),
                      yaxis=axis(range=[k - 0.5, -0.6], tickvals=ys, ticktext=ticks, gridcolor="rgba(0,0,0,0)",
                                 tickfont=dict(size=LAB_PX, color=C.TEXT)))
    for i in range(0, k, 2):
        fig.add_hrect(y0=i - 0.5, y1=i + 0.5, fillcolor=C.ZEBRA, line_width=0, layer="below")
    return fig


def escena_presentacion(p):
    rows = [dict(label="Lata 355 ml vs. lata 355 ml", sub=f"por lata · {V['pares_lata']:.0f} tiendas", v=V["prima_lata"],
                 lo=V["prima_lata_inf"], hi=V["prima_lata_sup"],
                 right=f"IC90 {V['prima_lata_inf']:.1f} a {V['prima_lata_sup']:.1f}"),
            dict(label="Coca-Cola 2.75 L vs. Pepsi 3 L", sub=f"por litro · {V['pares_familiar']:.0f} tiendas",
                 v=V["prima_familiar"], lo=V["prima_familiar_inf"], hi=V["prima_familiar_sup"],
                 right=f"IC90 {V['prima_familiar_inf']:.1f} a {V['prima_familiar_sup']:.1f}"),
            dict(label="Coca-Cola 2.75 L vs. Pepsi 3 L", sub="por botella (lo que paga el cliente)", v=V["fam_empaque"],
                 lo=V["fam_empaque_inf"], hi=V["fam_empaque_sup"],
                 right=f"${V['fam_coca']:.2f} vs. ${V['fam_pepsi']:.2f}".replace("$", "&#36;"))]
    return filas(rows, p, "La prima cambia según la presentación",
                 "Prima de Coca-Cola sobre Pepsi en la misma tienda · línea dorada: mismo precio que Pepsi",
                 [-10, 45], "Coca-Cola frente a Pepsi en la misma tienda")


def escena_cadenas(p):
    d = DES[(DES.comparacion == "familiar") & (DES.por == "formato")].sort_values("brecha_pct", ascending=False)
    rows = [dict(label=r.grupo, sub=f"{int(r.n_pares)} tiendas · {int(r.municipios)} municipios", v=r.brecha_pct,
                 lo=r.ic90_inf, hi=r.ic90_sup, right=f"IC90 {r.ic90_inf:.1f} a {r.ic90_sup:.1f}".replace("-", "−"))
            for r in d.itertuples()]
    return filas(rows, p, "Por litro, la prima de la botella<br>cambia de una cadena a otra",
                 "Coca-Cola 2.75 L vs. Pepsi 3 L por litro · gris: el rango cruza 0",
                 [-15, 25], "Coca-Cola frente a Pepsi por litro en la misma tienda", l=300, colx=24.5)


# ----------------------------------------------------------------------------- 4. precio por litro
def escena_litro(p):
    d = LAD[LAD.tiendas >= 30].copy()
    d["marca_c"] = np.where(d.marca == "Coca Cola", "Coca-Cola", "Pepsi")
    d = d.sort_values("por_litro", ascending=False).reset_index(drop=True)
    names = [f"{r.marca_c} {r.presentacion.split(' No Retornable')[0].replace('Lt.', 'L').replace('Ml.', 'ml')}" for r in d.itertuples()]
    q = ease(p / 0.7)
    cols = [COCA if m == "Coca-Cola" else PEPSI for m in d.marca_c]
    fig = go.Figure(go.Bar(x=d.por_litro * q, y=names, orientation="h", marker_color=cols,
                           text=[f"<b>${v:.2f}</b>".replace("$", "&#36;") for v in d.por_litro], textposition="outside",
                           textfont=dict(size=LAB_PX, color=cols), cliponaxis=False))
    a = ease((p - 0.6) / 0.4)
    i_lata, i_275 = names.index("Coca-Cola Lata 355 ml"), next(i for i, n in enumerate(names) if "2.75" in n)
    fig.add_annotation(x=d.por_litro[i_275] + 9, y=names[i_275], ax=56, ay=i_275 - 0.45,
                       axref="x", ayref="y", text=f"<b>{V['veces_lata_familiar']:.1f} veces</b> más por litro<br>en lata que en 2.75 L",
                       showarrow=True, arrowhead=2, arrowwidth=2.5, arrowcolor=C.GOLD, font=dict(size=LAB_PX, color=C.GOLD),
                       bgcolor=C.FIG, opacity=a)
    layout(fig, "La presentación modifica considerablemente<br>la comparación de precios",
           "Precio por litro de cada presentación (mediana en supermercados) · 30 tiendas o más", l=330, r=70)
    fig.update_layout(xaxis=axis(range=[0, d.por_litro.max() * 1.18], tickprefix="$", dtick=10, title="Precio por litro"),
                      yaxis=axis(autorange="reversed", tickfont=dict(size=LAB_PX, color=C.TEXT), gridcolor="rgba(0,0,0,0)"),
                      bargap=0.3)
    fig.update_yaxes(ticktext=[f"<span style='color:{c}'><b>{n}</b></span>" for n, c in zip(names, cols)], tickvals=names)
    return fig


# ----------------------------------------------------------------------------- render y ensamblado
ESCENAS = [(escena_lata, 4.0), (escena_presentacion, 4.0), (escena_cadenas, 4.0), (escena_litro, 3.0)]
ANIM, FUNDIDO = 1.5, 0.35


def png(fig):
    return Image.open(io.BytesIO(pio.to_image(fig, format="png", width=W, height=H, scale=1))).convert("RGB")


def cuadros():
    out = []
    finales = []
    for k, (fn, dur) in enumerate(ESCENAS):
        n = int(round(dur * FPS))
        cache = {}
        nxt = png(ESCENAS[k + 1][0](0.0)) if k < len(ESCENAS) - 1 else None
        for i in range(n):
            t = i / FPS
            key = round(min(t / ANIM, 1.0), 3)
            if key not in cache:
                cache[key] = png(fn(key))
            img = cache[key]
            if nxt is not None and t > dur - FUNDIDO:
                img = Image.blend(img, nxt, (t - (dur - FUNDIDO)) / FUNDIDO)
            out.append(img)
        finales.append(cache[1.0])
    return out, finales


def guardar(frames, finales):
    import imageio.v2 as imageio
    for f in AQUI.glob("coca_cola_vs_pepsi*"):
        f.unlink()
    for f in AQUI.glob("escena_*.png"):
        f.unlink()
    mp4 = AQUI / "coca_cola_pepsi_plotly.mp4"
    with imageio.get_writer(mp4, fps=FPS, codec="libx264", quality=8, pixelformat="yuv420p", macro_block_size=8) as w:
        for f in frames:
            w.append_data(np.asarray(f))
    uniq, dur = [], []
    for f in frames:
        if uniq and np.array_equal(np.asarray(uniq[-1]), np.asarray(f)):
            dur[-1] += 1000 / FPS
        else:
            uniq.append(f)
            dur.append(1000 / FPS)
    pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in uniq]
    gif = AQUI / "coca_cola_pepsi_plotly.gif"
    pal[0].save(gif, save_all=True, append_images=pal[1:], duration=[int(round(d)) for d in dur], loop=0, optimize=True)
    for k, f in enumerate(finales, 1):
        f.save(AQUI / f"escena_{k}.png")
    return gif, mp4, len(uniq), sum(dur) / 1000


if __name__ == "__main__":
    frames, finales = cuadros()
    gif, mp4, n, seg = guardar(frames, finales)
    print(f"{gif.name}: {n} cuadros únicos, {seg:.1f} s, {gif.stat().st_size / 1e6:.2f} MB")
    print(f"{mp4.name}: {len(frames)} cuadros a {FPS} fps, {mp4.stat().st_size / 1e6:.2f} MB")
