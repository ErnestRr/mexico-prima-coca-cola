"""Gráficas de la prima de Coca-Cola sobre Pepsi con la plantilla del núcleo (charts.py).

Convenciones: verde ▲ = Coca-Cola más cara que Pepsi en la misma tienda; rojo ▼ = más barata; gris = no distinta de
cero (el intervalo cruza 0); dorado = referencia (mediana, precio de Pepsi = 0).
"""
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator
from matplotlib.transforms import blended_transform_factory

import charts as C
from charts import n, b, g, r, minus, dpct, _box, _finish, _canvas, _frame, _save

SRC_P = C.SRC + ". Supermercados; mismas tiendas con las dos marcas."
COCA, PEPSI = C.TEXT2, "#5b8fd6"


def gold(t):
    return (t, True, C.GOLD)


def _col(lo, hi):
    return C.GREEN if lo > 0 else (C.RED if hi < 0 else C.NEUTRAL)


def _sgn(v, dec=1, solid=True):
    if not solid:
        return minus(f"{v:+.{dec}f}%"), C.TEXT2
    return minus(f"{'▲' if v > 0 else '▼'} {v:+.{dec}f}%"), (C.GREEN_T if v > 0 else C.RED_T)


def _hist(ax, v, med, size=7.0, step=2.5, lo=-10, hi=40):
    bins = np.arange(lo, hi + step, step)
    cnt, edges = np.histogram(np.clip(v, lo, hi - 1e-9), bins=bins)
    share = cnt / len(v) * 100
    for c_, e0, e1 in zip(share, edges[:-1], edges[1:]):
        col = C.GREEN if e0 >= 0 else C.RED
        ax.bar(e0, c_, width=e1 - e0, align="edge", color=col, edgecolor=C.FIG, lw=0.8, zorder=2, alpha=0.9)
    ax.axvline(med, color=C.GOLD, lw=2, zorder=4)
    ax.axvline(0, color=C.TEXT2, lw=1, ls=(0, (3, 3)), zorder=3)
    return share.max()


# --------------------------------------------------------------------------- 01 principal
def premium_main(pl, des, res, path, svg=True):
    v = res
    fig = _canvas(2100, 1320)
    ax = fig.add_axes([0.07, 0.15, 0.50, 0.50])
    top = _hist(ax, pl.prima_pct.to_numpy(), v["prima_lata"])
    ax.text(v["prima_lata"] + 0.6, top * 1.12, f"mediana ▲ +{v['prima_lata']:.1f}%\n(+${v['pesos_lata']:.2f} por lata)",
            ha="left", va="top", fontsize=7.8, color=C.GOLD, fontweight="bold", parse_math=False)
    ax.text(0.4, top * 1.12, "Coca-Cola\nmás barata ◀", ha="right", va="top", fontsize=6.8, color=C.RED_T, linespacing=1.15)
    ax.set(xlim=(-10, 40), ylim=(0, top * 1.22))
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.xaxis.set_major_formatter(lambda x, _: "Pepsi" if abs(x) < 1e-9 else minus(f"{x:+.0f}%"))
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    _frame(ax, grid="y", size=7.2)
    ax.set_xlabel("Prima de Coca-Cola sobre Pepsi en la misma tienda (lata 355 ml)", fontsize=7.6, labelpad=5)
    ax.set_ylabel("% de las tiendas", fontsize=7.6, labelpad=5)
    # desglose por cadena (formato)
    d = des[(des.comparacion == "lata") & (des.por == "formato")].sort_values("brecha_pct", ascending=False).reset_index(drop=True)
    k = len(d)
    ax2 = fig.add_axes([0.73, 0.15, 0.19, 0.50])
    for i, r_ in d.iterrows():
        col = _col(r_.ic90_inf, r_.ic90_sup)
        ax2.hlines(i, r_.ic90_inf, r_.ic90_sup, color=col, lw=8, alpha=0.45, zorder=2)
        ax2.scatter([r_.brecha_pct], [i], s=110, marker="D", color=col, edgecolor=C.TEXT, lw=0.8, zorder=3)
        ax2.text(-0.06, i - 0.12, r_.grupo, transform=ax2.get_yaxis_transform(), ha="right", va="center", fontsize=7.4,
                 fontweight="bold")
        ax2.text(-0.06, i + 0.24, f"{int(r_.n_pares)} tiendas", transform=ax2.get_yaxis_transform(), ha="right",
                 va="center", fontsize=6.0, color=C.TEXT2)
        t, tc = _sgn(r_.brecha_pct, solid=col != C.NEUTRAL)
        ax2.text(1.04, i, t, transform=ax2.get_yaxis_transform(), ha="left", va="center", fontsize=7.2, fontweight="bold",
                 color=tc)
    ax2.axvline(v["prima_lata"], color=C.GOLD, lw=1.2, ls=(0, (4, 3)), zorder=1)
    ax2.set(xlim=(10, 32), ylim=(k - 0.5, -0.5), yticks=[])
    ax2.xaxis.set_major_locator(MultipleLocator(5))
    ax2.xaxis.set_major_formatter(lambda x, _: f"+{x:.0f}%")
    _frame(ax2, grid="x", size=6.6)
    ax2.set_xlabel("Prima por cadena (IC 90%)", fontsize=7.2, labelpad=5)
    fig.text(0.59, 0.68, "Por cadena (formato)", fontsize=7.6, fontweight="bold", color=C.TEXT2)
    _box(fig, 0.03, 0.80, [[b("¿Cómo leer?  "), n("Barras: cuántas tiendas tienen cada prima (lata de Coca-Cola frente a lata de "
                                                 "Pepsi en la misma tienda). "), ("Línea dorada", True, C.GOLD), n(": mediana.")],
                           [n("A la derecha: prima típica por cadena con su rango probable (IC 90%). "), g("▲ verde"),
                            n(": Coca-Cola más cara.")]], "ul", size=7.4)
    _finish(fig, [[n("En la misma tienda, la lata de Coca-Cola cuesta "), g(f"▲ +{v['prima_lata']:.1f}%"),
                   n(f" más que la de Pepsi: ${v['lata_coca']:.0f} contra ${v['lata_pepsi']:.0f};")],
                  [n("Coca-Cola es más barata en solo "), r(f"▼ {v['inv_lata']:.0f}%"), n(f" de {v['pares_lata']:.0f} supermercados")]],
            f"Prima de Coca-Cola sobre Pepsi, lata 355 ml contra lata 355 ml en la misma tienda; {v['pares_lata']:.0f} supermercados "
            f"de {v['mun_lata']:.0f} municipios; IC90 por bootstrap de tiendas y municipios",
            [n(SRC_P)], size=13, foot=6.4, top=1 - 26 / 1320)
    return _save(fig, path, svg)


def premium_social(pl, res, fmt, path):
    v = res
    fig = C.social_canvas(fmt)
    W, H = C.SOCIAL[fmt]
    vertical = H > W
    top = (360 if vertical else 200) / H
    bot = (150 if vertical else 145) / H
    ax = fig.add_axes([0.1, bot, 0.84, 1 - top - bot])
    tp = _hist(ax, pl.prima_pct.to_numpy(), v["prima_lata"])
    ax.text(v["prima_lata"] - 0.7, tp * 1.02, f"mediana\n▲ +{v['prima_lata']:.1f}%", ha="right", va="top", fontsize=7.4,
            color=C.GOLD, fontweight="bold", path_effects=C.HALO)
    ax.set(xlim=(-10, 40), ylim=(0, tp * 1.15))
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.xaxis.set_major_formatter(lambda x, _: "Pepsi" if abs(x) < 1e-9 else minus(f"{x:+.0f}%"))
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    _frame(ax, grid="y", size=6.2)
    ax.set_xlabel("Prima de la lata de Coca-Cola sobre la de Pepsi en la misma tienda", fontsize=6.4)
    ax.set_ylabel("% de las tiendas", fontsize=6.4)
    if vertical:
        title = [[n("En la misma tienda, la lata de")], [n("Coca-Cola cuesta "), g(f"▲ +{v['prima_lata']:.1f}%")],
                 [n(f"más que la de Pepsi: ${v['lata_coca']:.0f} contra ${v['lata_pepsi']:.0f}")]]
        sub = f"{v['pares_lata']:.0f} supermercados con las dos latas; 16–31 ago 2026"
    else:
        title = [[n("En la misma tienda, la lata de Coca-Cola cuesta "), g(f"▲ +{v['prima_lata']:.1f}%")],
                 [n(f"más que la de Pepsi: ${v['lata_coca']:.0f} contra ${v['lata_pepsi']:.0f}")]]
        sub = f"Lata 355 ml contra lata 355 ml en {v['pares_lata']:.0f} supermercados; 16–31 ago 2026"
    C.finish_social(fig, title, sub, [n("Fuente: elaboración propia con datos de PROFECO, Quién es Quién en los Precios.")],
                    size=13 if vertical else 11, foot=5.4)
    fig.savefig(path, dpi=fig.dpi)
    return fig


# --------------------------------------------------------------------------- 02 por presentación
def _dot_rows(rows, path, title, sub, xlim, xlabel, box, h=1150, label_w=0.30, xfmt=None):
    k = len(rows)
    fig = _canvas(2000, h)
    top_px, bot_px = 430, 190
    rowh = (h - top_px - bot_px) / k
    ax = fig.add_axes([label_w, bot_px / h, 0.40, rowh * k / h])
    ax.patch.set_alpha(0)
    tr = blended_transform_factory(fig.transFigure, ax.transData)
    for i, rw in enumerate(rows):
        if i % 2 == 0:
            ax.add_patch(Rectangle((0.015, i - 0.5), 0.97, 1, transform=tr, color=C.ZEBRA, lw=0, zorder=0))
        col = _col(rw["lo"], rw["hi"])
        ax.hlines(i, rw["lo"], rw["hi"], color=col, lw=9, alpha=0.45, zorder=2)
        ax.scatter([rw["v"]], [i], s=150, marker="D", color=col, edgecolor=C.TEXT, lw=1, zorder=3)
        ax.text(label_w - 0.012, i - 0.14, rw["label"], transform=tr, ha="right", va="center", fontsize=8.4, fontweight="bold")
        ax.text(label_w - 0.012, i + 0.22, rw["sub"], transform=tr, ha="right", va="center", fontsize=6.4, color=C.TEXT2)
        t, tc = _sgn(rw["v"], solid=col != C.NEUTRAL)
        ax.text(0.73, i - 0.1, t, transform=tr, ha="left", va="center", fontsize=8.6, fontweight="bold", color=tc)
        ax.text(0.73, i + 0.24, rw["right"], transform=tr, ha="left", va="center", fontsize=6.6, color=C.TEXT2)
    ax.axvline(0, color=C.GOLD, lw=1.2, ls=(0, (4, 3)), zorder=1)
    ax.set(xlim=xlim, ylim=(k - 0.5, -0.5), yticks=[])
    ax.xaxis.set_major_locator(MultipleLocator(10 if xlim[1] - xlim[0] > 30 else 5))
    ax.xaxis.set_major_formatter(xfmt or (lambda x, _: "Pepsi" if abs(x) < 1e-9 else minus(f"{x:+.0f}%")))
    _frame(ax, grid="x", size=7.2)
    ax.set_xlabel(xlabel, fontsize=7.4, labelpad=5)
    _box(fig, 0.03, 1 - 205 / h, box, "ul", size=7.4)
    _finish(fig, title, sub, [n(SRC_P)], size=12.5, foot=6.4, top=1 - 26 / h)
    return _save(fig, path)


def by_presentation(tt, res, path):
    v = res
    rows = [dict(label="Lata 355 ml vs. lata 355 ml", sub=f"por lata · {v['pares_lata']:.0f} tiendas", v=v["prima_lata"],
                 lo=v["prima_lata_inf"], hi=v["prima_lata_sup"], right=f"+${v['pesos_lata']:.2f} por lata · IC90 "
                 f"{v['prima_lata_inf']:.1f} a {v['prima_lata_sup']:.1f}"),
            dict(label="Coca-Cola 2.75 L vs. Pepsi 3 L", sub=f"por litro · {v['pares_familiar']:.0f} tiendas",
                 v=v["prima_familiar"], lo=v["prima_familiar_inf"], hi=v["prima_familiar_sup"],
                 right=f"IC90 {v['prima_familiar_inf']:.1f} a {v['prima_familiar_sup']:.1f}"),
            dict(label="Coca-Cola 2.75 L vs. Pepsi 3 L", sub="por botella (lo que paga el cliente)", v=v["fam_empaque"],
                 lo=v["fam_empaque_inf"], hi=v["fam_empaque_sup"],
                 right=f"{C.money_tex(v['fam_coca'])} contra {C.money_tex(v['fam_pepsi'])} · "
                       + minus(f"IC90 {v['fam_empaque_inf']:.1f} a {v['fam_empaque_sup']:.1f}")),
            dict(label="Light 2 L vs. Light 2.5 L", sub=f"por litro · {v['pares_light']:.0f} tiendas (sensibilidad)",
                 v=v["prima_light"], lo=v["prima_light_inf"], hi=v["prima_light_sup"],
                 right=f"IC90 {v['prima_light_inf']:.1f} a {v['prima_light_sup']:.1f}")]
    title = [[n("La prima de Coca-Cola vive en la lata ("), g(f"▲ +{v['prima_lata']:.1f}%"), n("); en la botella familiar baja a "),
              g(f"▲ +{v['prima_familiar']:.1f}%"), n(" por litro")],
             [n("y, por botella, la Coca-Cola de 2.75 L sale "), r(minus(f"▼ {v['fam_empaque']:+.1f}%")), n(" frente a la Pepsi de 3 L")]]
    box = [[b("¿Cómo leer?  "), b("◆"), n(" prima típica de Coca-Cola sobre Pepsi en la misma tienda. Barra: rango probable (IC 90%).")],
           [g("▲ verde"), n(": Coca-Cola más cara; "), r("▼ rojo"), n(": más barata. "), ("Línea dorada", True, C.GOLD),
            n(": mismo precio que Pepsi.")]]
    return _dot_rows(rows, path, title, "Prima de Coca-Cola sobre Pepsi en la misma tienda por presentación; supermercados",
                     (-10, 45), "Coca-Cola frente a Pepsi en la misma tienda", box, h=1150)


def family_by_format(des, res, path):
    d = des[(des.comparacion == "familiar") & (des.por == "formato")].sort_values("brecha_pct", ascending=False)
    rows = [dict(label=r_.grupo, sub=f"{int(r_.n_pares)} tiendas · {int(r_.municipios)} municipios", v=r_.brecha_pct,
                 lo=r_.ic90_inf, hi=r_.ic90_sup,
                 right=minus(f"IC90 {r_.ic90_inf:.1f} a {r_.ic90_sup:.1f}") + f" · Coca-Cola más barata en {r_.pct_invertidos:.0f}%")
            for _, r_ in d.iterrows()]
    hi, lo = d.iloc[0], d.iloc[-1]
    solid_lo = (lo.ic90_inf > 0) or (lo.ic90_sup < 0)
    title = [[n("En la botella familiar la prima por litro es chica en todas las cadenas: de "),
              g(f"▲ +{hi.brecha_pct:.1f}%"), n(f" en {hi.grupo}")],
             [n("a "), (minus(f"{lo.brecha_pct:+.1f}%"), True, C.TEXT2 if not solid_lo else C.RED_T),
              n(f" en {lo.grupo}" + (", donde el rango probable cruza 0" if not solid_lo else ""))]]
    box = [[b("¿Cómo leer?  "), b("◆"), n(" prima típica por litro, Coca-Cola 2.75 L frente a Pepsi 3 L en la misma tienda; barra: IC 90%.")],
           [n("Gris: no distinta de 0. A la derecha, % de tiendas donde Coca-Cola sale más barata por litro.")]]
    return _dot_rows(rows, path, title, "Prima por litro de Coca-Cola 2.75 L sobre Pepsi 3 L por cadena (formato), 10 tiendas o más",
                     (-15, 25), "Coca-Cola frente a Pepsi por litro en la misma tienda", box, h=1250, label_w=0.24)


# --------------------------------------------------------------------------- 04 precio por litro
def liter_ladder(lad, res, path, min_tiendas=30):
    d = lad[lad.tiendas >= min_tiendas].copy()
    d["marca_c"] = np.where(d.marca == "Coca Cola", "Coca-Cola", "Pepsi")
    d = d.sort_values("por_litro", ascending=False).reset_index(drop=True)
    k = len(d)
    fig = _canvas(2000, 1150)
    ax = fig.add_axes([0.27, 0.15, 0.55, 0.52])
    ax.patch.set_alpha(0)
    for i, r_ in d.iterrows():
        col = COCA if r_.marca_c == "Coca-Cola" else PEPSI
        ax.barh(i, r_.por_litro, color=col, height=0.62, zorder=2)
        ax.text(r_.por_litro + 0.8, i, f"${r_.por_litro:.2f} por litro", ha="left", va="center", fontsize=7.6,
                fontweight="bold", color=col, parse_math=False)
        ax.text(-0.015, i - 0.12, f"{r_.marca_c} {r_.presentacion.split(' No Retornable')[0].replace('Lt.', 'L').replace('Ml.', 'ml')}",
                transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=8, fontweight="bold", color=col)
        ax.text(-0.015, i + 0.25, f"${r_.precio:.2f} el envase · {int(r_.tiendas)} tiendas", transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=6.3, color=C.TEXT2, parse_math=False)
    ax.set(xlim=(0, d.por_litro.max() * 1.25), ylim=(k - 0.5, -0.5), yticks=[])
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.xaxis.set_major_formatter(lambda x, _: f"${x:.0f}")
    _frame(ax, grid="x", size=7.2)
    ax.set_xlabel("Precio por litro (mediana de los supermercados que venden la presentación)", fontsize=7.4, labelpad=5)
    v = res
    _box(fig, 0.03, 0.80, [[b("¿Cómo leer?  "), n("Cada barra: lo que cuesta un litro de refresco en esa presentación. "),
                            ("Gris claro", True, COCA), n(": Coca-Cola; "), ("azul", True, PEPSI), n(": Pepsi. "
                            "Presentaciones en 30 tiendas o más.")]], "ul", size=7.4)
    _finish(fig, [[n("Un litro de Coca-Cola en lata cuesta "), b(f"${v['litro_coca_lata']:.2f}"), n(", "),
                   gold(f"{v['veces_lata_familiar']:.1f} veces"), n(f" lo que en la botella de 2.75 L (${v['litro_coca_275']:.2f}):")],
                  [n("la marca cobra su prima en el envase individual, donde el cliente compara menos")]],
            "Precio por litro de cada presentación regular de Coca-Cola y Pepsi; supermercados",
            [n(C.SRC + ". Supermercados.")], size=12.5, foot=6.4, top=1 - 26 / 1150)
    return _save(fig, path)
