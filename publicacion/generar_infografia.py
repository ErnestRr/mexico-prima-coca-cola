"""Infografía ejecutiva de 1080×1350 px (4:5): tres indicadores, una comparación por cadena comercial y la conclusión.

Hecha con Plotly y Kaleido. Las cifras salen de ../data/processed/ y no se recalcula nada:
  resultados.json  -> prima_lata (+23.7%), prima_familiar (+4.9%, por litro) y fam_empaque (−3.8%, por envase familiar);
  prima_desglose.csv -> prima por cadena (formato) de la lata y de la botella familiar por litro, con su IC90.
Son diferencias medianas de precios observados en la misma tienda, no márgenes, y comparan presentaciones distintas:
lata de 355 ml, y Coca-Cola de 2.75 L frente a Pepsi de 3 L (por litro y por envase).
Colores: verde = Coca-Cola más cara, coral = más barata, gris = el rango probable (IC90) cruza 0 (diferencia no clara).
Las siluetas usan el color de cada marca en las gráficas del análisis (Coca-Cola gris claro, Pepsi azul); la altura de las
botellas es proporcional a su volumen.

Uso: python generar_infografia.py   (requiere plotly, kaleido y pandas)
"""
from pathlib import Path
import json
import sys

import pandas as pd
import plotly.graph_objects as go

AQUI = Path(__file__).resolve().parent
PROY = AQUI.parent
sys.path.insert(0, str(PROY / "src"))
import charts as C  # noqa: E402  (paleta del proyecto)

SALIDA = AQUI / "infografia_coca_cola_pepsi.png"
PROC = PROY / "data/processed"
RES = {k: v["cifra"] for k, v in json.loads((PROC / "resultados.json").read_text(encoding="utf-8")).items()}
DES = pd.read_csv(PROC / "prima_desglose.csv")


def por_cadena(comparacion):
    return DES[(DES.comparacion == comparacion) & (DES.por == "formato")].set_index("grupo")


LATA, LITRO = por_cadena("lata"), por_cadena("familiar")
# Se muestran las cuatro cadenas con más tiendas (lata + botella familiar); las seis están en el reporte interactivo.
TIENDAS = LATA.n_pares.add(LITRO.n_pares, fill_value=0)
MAS_TIENDAS = list(TIENDAS.sort_values(ascending=False).index[:4])
CADENAS = [c for c in LATA.sort_values("brecha_pct", ascending=False).index if c in MAS_TIENDAS]

# ----------------------------------------------------------------------------- diseño
W, H = 1080, 1350
FONT = "Segoe UI, Arial, sans-serif"
BG, CARD = C.FIG, C.BOX
TXT, TXT2, MUTED = C.TEXT, C.TEXT2, C.MUTED
POS, POS_T = C.GREEN, C.GREEN_T                    # prima positiva: Coca-Cola más cara
NEG = NEG_T = "#ff6b5f"                            # diferencia negativa (coral): Coca-Cola más barata
GRIS, GRIS_T = C.NEUTRAL, C.TEXT2                  # rango probable que cruza 0
COCA, PEPSI = C.TEXT2, "#5b8fd6"                   # colores de marca de las gráficas del análisis
MX = 40                                            # margen lateral


def pct(v, dec=1):
    return ("+" if v > 0 else "−") + f"{abs(v):.{dec}f}%"


def color_fila(fila):
    """Verde si el rango probable queda sobre 0, coral si queda bajo 0, gris si lo cruza."""
    if fila.ic90_inf > 0:
        return POS, POS_T
    if fila.ic90_sup < 0:
        return NEG, NEG_T
    return GRIS, GRIS_T


def ann(fig, x, y, text, size, color=TXT, bold=False, xanchor="left", yanchor="middle", align="left"):
    """Texto en coordenadas de píxel del lienzo (eje oculto x4/y4)."""
    fig.add_annotation(xref="x4", yref="y4", x=x, y=y, xanchor=xanchor, yanchor=yanchor, align=align, showarrow=False,
                       text=f"<b>{text}</b>" if bold else text, font=dict(family=FONT, size=size, color=color))


def rrect(x, y, w, h, r):
    return (f"M {x + r},{y} L {x + w - r},{y} Q {x + w},{y} {x + w},{y + r} L {x + w},{y + h - r} "
            f"Q {x + w},{y + h} {x + w - r},{y + h} L {x + r},{y + h} Q {x},{y + h} {x},{y + h - r} L {x},{y + r} Q {x},{y} {x + r},{y} Z")


def forma(fig, path, color, opacity=1.0):
    fig.add_shape(type="path", xref="x4", yref="y4", path=path, fillcolor=color, opacity=opacity, line=dict(width=0))


def lata(fig, cx, base, color):
    """Lata de 355 ml: cuerpo con hombros, aros superior e inferior y banda de etiqueta."""
    top = base - 84
    forma(fig, (f"M {cx - 22},{top + 11} Q {cx - 22},{top + 4} {cx - 16},{top + 4} L {cx + 16},{top + 4} "
                f"Q {cx + 22},{top + 4} {cx + 22},{top + 11} L {cx + 22},{base - 11} Q {cx + 22},{base - 4} {cx + 16},{base - 4} "
                f"L {cx - 16},{base - 4} Q {cx - 22},{base - 4} {cx - 22},{base - 11} Z"), color)
    forma(fig, rrect(cx - 17, top, 34, 6, 2), TXT, 0.6)
    forma(fig, rrect(cx - 17, base - 5, 34, 5, 2), TXT, 0.6)
    forma(fig, rrect(cx - 22, top + 30, 44, 26, 0), BG, 0.3)


def botella(fig, cx, base, alto, color):
    """Botella: la altura es proporcional al volumen (3 L = 128 px, 2.75 L = 117 px)."""
    top, w = base - alto, 52
    forma(fig, (f"M {cx - 8},{top + 11} L {cx - 8},{top + 0.19 * alto} Q {cx - w / 2},{top + 0.29 * alto} {cx - w / 2},{top + 0.40 * alto} "
                f"L {cx - w / 2},{base - 10} Q {cx - w / 2},{base} {cx - w / 2 + 10},{base} L {cx + w / 2 - 10},{base} "
                f"Q {cx + w / 2},{base} {cx + w / 2},{base - 10} L {cx + w / 2},{top + 0.40 * alto} "
                f"Q {cx + w / 2},{top + 0.29 * alto} {cx + 8},{top + 0.19 * alto} L {cx + 8},{top + 11} Z"), color)
    forma(fig, rrect(cx - 10, top, 20, 12, 3), TXT, 0.6)
    forma(fig, rrect(cx - w / 2, top + 0.56 * alto, w, 0.22 * alto, 0), BG, 0.3)


def tarjeta(fig, x0, top, valor, color, texto, color_t, figuras, etiquetas):
    forma(fig, rrect(x0, top, 320, 376, 14), CARD)
    forma(fig, rrect(x0, top, 320, 5, 2), color)                       # filo superior: signo de la diferencia
    base = top + 140
    for (cx, tipo, alto, col), (nombre, medida) in zip(figuras, etiquetas):
        (lata(fig, x0 + cx, base, col) if tipo == "lata" else botella(fig, x0 + cx, base, alto, col))
        ann(fig, x0 + cx, base + 24, nombre, 20, col, xanchor="center")
        ann(fig, x0 + cx, base + 48, medida, 20, TXT2, xanchor="center")
    ann(fig, x0 + 24, top + 244, valor, 60, color_t, bold=True)
    for i, linea in enumerate(texto):
        ann(fig, x0 + 24, top + 296 + 29 * i, linea, 24, TXT)


def columna_cadenas(fig, tabla, eje):
    """Barras por cadena de una comparación, con su valor; las dos columnas comparten escala."""
    cats = CADENAS
    colores = [color_fila(tabla.loc[c]) for c in cats]
    vals = [tabla.loc[c, "brecha_pct"] for c in cats]
    sufijo = "" if eje == 1 else str(eje)
    fig.add_trace(go.Bar(x=vals, y=cats, orientation="h", xaxis=f"x{sufijo}", yaxis=f"y{sufijo}", hoverinfo="skip", width=0.55,
                         marker=dict(color=[c[0] for c in colores])))
    fig.add_trace(go.Scatter(x=[max(v, 0) + 0.9 for v in vals], y=cats, mode="text", xaxis=f"x{sufijo}", yaxis=f"y{sufijo}",
                             hoverinfo="skip", cliponaxis=False, textposition="middle right",
                             text=[f"<b>{pct(v)}</b>" for v in vals],
                             textfont=dict(family=FONT, size=30, color=[c[1] for c in colores])))


def construir():
    lata_p, litro_p, envase_p = RES["prima_lata"], RES["prima_familiar"], RES["fam_empaque"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0], y=[0], xaxis="x4", yaxis="y4", mode="markers", opacity=0, hoverinfo="skip"))

    # --- encabezado: el título es lo más grande de la página
    ann(fig, MX, 30, f"Coca-Cola puede costar <span style='color:{POS_T}'>{lata_p:.1f}% más</span><br>que Pepsi, pero también puede<br>"
        f"ser <span style='color:{NEG_T}'>{abs(envase_p):.1f}% más barata.</span>", 48, TXT, bold=True, yanchor="top")
    ann(fig, MX, 222, "Comparación de precios en supermercados de México | Profeco, agosto 2026", 24, TXT2, yanchor="top")

    # --- tres indicadores
    top = 268
    pareja = lambda tipo, alto_c, alto_p: [(70, tipo, alto_c, COCA), (200, tipo, alto_p, PEPSI)]
    tarjeta(fig, MX, top, pct(lata_p), POS, ["Coca-Cola más cara", "por lata", "de 355 ml"], POS_T,
            pareja("lata", 0, 0), [("Coca-Cola", "355 ml"), ("Pepsi", "355 ml")])
    tarjeta(fig, MX + 340, top, pct(litro_p), POS, ["Coca-Cola más cara", "por litro en botella", "familiar"], POS_T,
            pareja("botella", 128 * 2.75 / 3, 128), [("Coca-Cola", "2.75 L"), ("Pepsi", "3 L")])
    tarjeta(fig, MX + 680, top, pct(envase_p), NEG, ["Coca-Cola más barata", "por envase", "familiar"], NEG_T,
            pareja("botella", 128 * 2.75 / 3, 128), [("Coca-Cola", "2.75 L"), ("Pepsi", "3 L")])

    # --- comparación por cadena comercial (dos columnas, misma escala)
    ytop, ybot = 742, 974
    x_izq, x_der = [0.30, 0.575], [0.665, 0.94]
    ann(fig, MX, 668, "Cadena por cadena, la prima cambia con la presentación", 26, TXT, bold=True)
    ann(fig, MX, 712, "Cadenas con más tiendas", 20, MUTED)
    ann(fig, (x_izq[0] + x_izq[1]) / 2 * W, 712, "Lata de 355 ml", 25, TXT, bold=True, xanchor="center")
    ann(fig, (x_der[0] + x_der[1]) / 2 * W, 712, "Botella familiar por litro", 25, TXT, bold=True, xanchor="center")
    columna_cadenas(fig, LATA, 1)
    columna_cadenas(fig, LITRO, 2)
    dom_y = [1 - ybot / H, 1 - ytop / H]
    eje_x = dict(range=[-8, 34], showgrid=False, zeroline=False, showline=False, fixedrange=True, ticks="",
                 tickvals=[0], ticktext=["= Pepsi"], tickfont=dict(family=FONT, size=22, color=MUTED))
    eje_y = dict(domain=dom_y, type="category", categoryorder="array", categoryarray=CADENAS, autorange="reversed",
                 showgrid=False, zeroline=False, showline=False, ticks="")
    fig.update_layout(
        width=W, height=H, paper_bgcolor=BG, plot_bgcolor="rgba(0,0,0,0)", showlegend=False, margin=dict(l=0, r=0, t=0, b=0),
        font=dict(family=FONT, size=22, color=TXT),
        xaxis=dict(domain=x_izq, anchor="y", **eje_x),
        yaxis=dict(anchor="x", tickfont=dict(family=FONT, size=26, color=TXT), **eje_y),
        xaxis2=dict(domain=x_der, anchor="y2", **eje_x),
        yaxis2=dict(anchor="x2", showticklabels=False, **eje_y),
        xaxis4=dict(domain=[0, 1], range=[0, W], visible=False, fixedrange=True),
        yaxis4=dict(domain=[0, 1], range=[H, 0], visible=False, fixedrange=True))
    for ref in ("x", "x2"):
        fig.add_shape(type="line", xref=ref, yref="paper", x0=0, x1=0, y0=dom_y[0], y1=dom_y[1], line=dict(color=TXT2, width=2))

    # --- cómo leerla
    ann(fig, MX, 1016,
        "Botella familiar: Coca-Cola de 2.75 L frente a Pepsi de 3 L.<br>"
        "Diferencias medianas de precios observados en la misma tienda; no son márgenes.<br>"
        f"<span style='color:{POS_T}'>Verde</span>: más cara · <span style='color:{NEG_T}'>coral</span>: más barata. "
        "Son diferencias de precio, no ganancias.<br>"
        "<span style='color:#9aa3b2'>Gris</span>: el intervalo de incertidumbre cruza cero; no implica precios iguales.",
        22, TXT2, yanchor="top")

    # --- conclusión
    fig.add_shape(type="line", xref="x4", yref="y4", x0=MX, x1=W - MX, y0=1142, y1=1142, line=dict(color=C.GOLD, width=2))
    ann(fig, MX, 1156, "Comparar precios sin considerar presentaciones y unidades<br>"
        "de medida puede llevar a decisiones equivocadas de pricing.", 28, TXT, bold=True, yanchor="top")

    # --- pie
    ann(fig, MX, 1258, "Fuente: Profeco, Quién es Quién en los Precios, 16–31 de agosto de 2026.", 20, MUTED)
    ann(fig, MX, 1288, "Ernesto Roldán | Business Intelligence · Pricing · Rentabilidad", 20, TXT2)
    ann(fig, MX, 1318, "Análisis completo: github.com/ErnestRr/mexico-prima-coca-cola", 20, MUTED)
    return fig


if __name__ == "__main__":
    construir().write_image(SALIDA, width=W, height=H, scale=1)
    print(f"{SALIDA.name}: {W}×{H} px")
