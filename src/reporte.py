"""Reporte HTML de la prima de Coca-Cola sobre Pepsi, con la plantilla del núcleo (reporte_base) y los textos de
config.yaml (plantillas.render)."""
import re

import numpy as np

import charts as C
import plantillas as PL
import reporte_base as RB


def _html(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


def build(pl, des, tt, res, cfg, gallery, path):
    import plotly.graph_objects as go

    v = res
    fig = go.Figure(go.Histogram(x=pl.prima_pct, xbins=dict(start=-10, end=40, size=2.5), histnorm="percent",
                                 marker=dict(color=C.GREEN, line=dict(color=C.FIG, width=1)),
                                 hovertemplate="Prima %{x}<br>%{y:.1f}% de las tiendas<extra></extra>"))
    fig.add_vline(v["prima_lata"], line=dict(color=C.GOLD, width=2),
                  annotation=dict(text=f"mediana +{v['prima_lata']:.1f}%", font=dict(color=C.GOLD)))
    fig.add_vline(0, line=dict(color=C.TEXT2, width=1, dash="dot"))
    fig.update_layout(**RB.layout(height=480, margin=dict(l=70, r=30, t=100, b=60), showlegend=False,
                                  title=RB.title("Prima de la lata de Coca-Cola sobre la de Pepsi, tienda por tienda",
                                                 f"{v['pares_lata']:.0f} supermercados con las dos latas de 355 ml")),
                      xaxis=RB.axis(title="Coca-Cola frente a Pepsi en la misma tienda", ticksuffix="%", range=[-10, 40]),
                      yaxis=RB.axis(title="% de las tiendas", ticksuffix="%"))

    def rows_for(comp):
        d = des[(des.comparacion == comp) & (des.por == "formato")].sort_values("brecha_pct", ascending=False)
        out = []
        for _, r_ in d.iterrows():
            solid = (r_.ic90_inf > 0) or (r_.ic90_sup < 0)
            cell = RB.pct(r_.brecha_pct) if solid else f"{r_.brecha_pct:+.1f}%".replace("-", "−")
            out.append([f"<b>{r_.grupo}</b>", f"#{cell}", f"#{r_.ic90_inf:.1f} a {r_.ic90_sup:.1f}".replace("-", "−"),
                        f"#{r_.pct_invertidos:.0f}%", f"#{int(r_.n_pares)}"])
        return out

    head = ["Cadena (formato)", "Prima", "IC90", "Coca-Cola más barata", "Tiendas"]
    pres = [["Lata 355 ml vs. lata 355 ml (por lata)", f"#{RB.pct(v['prima_lata'])}", f"#+${v['pesos_lata']:.2f}",
             f"#{v['pares_lata']:.0f}"],
            ["Coca-Cola 2.75 L vs. Pepsi 3 L (por litro)", f"#{RB.pct(v['prima_familiar'])}", "#—", f"#{v['pares_familiar']:.0f}"],
            ["Coca-Cola 2.75 L vs. Pepsi 3 L (por botella)", f"#{RB.pct(v['fam_empaque'])}",
             f"#−${abs(v['pesos_familiar']):.2f}", f"#{v['pares_familiar']:.0f}"],
            ["Light 2 L vs. Light 2.5 L (por litro, sensibilidad)", f"#{RB.pct(v['prima_light'])}", "#—", f"#{v['pares_light']:.0f}"]]
    rep = cfg["reporte"]
    R = lambda t: _html(PL.render(t, v))
    ap = cfg["readme"]["hallazgos_apoyo"]
    html = RB.page(
        titulo=cfg["titulo"], descripcion=PL.render(rep["descripcion"], v), objetivo=R(cfg["objetivo"]), h1=R(rep["h1"]),
        intro=R(rep["intro"]), stats=[(R(s["valor"]), s.get("clase", ""), R(s["texto"])) for s in rep["stats"]],
        secciones=[
            ("La prima en la <b>lata</b>", R(cfg["readme"]["hallazgo_principal"]), f"<div class='card'>{RB.fig_div(fig, 'lata')}</div>"),
            ("Por <b>presentación</b>", R(ap[0]), RB.table(["Comparación", "Prima", "Diferencia típica en pesos", "Tiendas"], pres)),
            ("Lata por <b>cadena</b>", R(ap[1]), RB.table(head, rows_for("lata"))),
            ("Botella familiar por <b>cadena</b>", R(ap[2]), RB.table(head, rows_for("familiar"))),
            ("Lo que no resultó sólido", R(cfg["readme"]["no_solido"]), ""),
        ],
        acciones=[(aud, " ".join(R(a) for a in acc)) for aud, acc in cfg["readme"]["acciones"].items()],
        galeria=gallery, metodo=[R(m) for m in rep["metodo"]])
    return RB.write(html, path)
