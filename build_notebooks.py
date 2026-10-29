"""Genera los notebooks del proyecto. Después ejecutarlos en orden 00→05 (ver README)."""
from pathlib import Path
import nbformat as nbf
import yaml

root = Path(__file__).resolve().parent
CFG = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8")) or {}
OBJ = CFG.get("objetivo", "")
KERNEL = {"display_name": "Python (mexico-costo-canasta)", "language": "python", "name": "python3"}
SETUP = """import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
from pathlib import Path
import sys, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
import entorno
entorno.setup()
import profeco, tablas, pares, estadistica as E, charts as C
import prima as P
PROC, META, CHARTS, SOCIAL = entorno.PROC, entorno.META, entorno.CHARTS, entorno.SOCIAL
CFG = entorno.config()
reg = entorno.registrar
pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 70)
pts, st, cat = P.load()
REPS = 500
"""
TOT = '["n_pares", "claves", "tiendas", "municipios", "brecha_pct", "ic90_inf", "ic90_sup", "brecha_pesos", "pct_invertidos", "pct_iguales"]'


def write(name, cells):
    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    nb.metadata.kernelspec = KERNEL
    (root / "notebooks").mkdir(exist_ok=True)
    nbf.write(nb, root / "notebooks" / name)


def head(num, title, question, why):
    return ("md", f"# {num} · {title}\n\n**Objetivo:** {OBJ}\n\n**Pregunta:** {question}\n\n{why}")


# --------------------------------------------------------------------------- 00
write("00_datos_y_cobertura.ipynb", [
    head("00", "Datos, presentaciones y equivalencias", CFG.get("pregunta", ""),
         """Este notebook responde: ¿qué presentaciones de Coca-Cola y Pepsi hay, en cuántas tiendas, cuáles son
equivalentes y cómo se comparan? Cierra con la tabla de decisiones metodológicas (plan aprobado en
`_specs/plan_metodologico_6_12.md`).

**Prima** = cuánto más cuesta Coca-Cola que Pepsi en la misma tienda, en % y en pesos. Se habla de precio relativo
sostenido, no de «valor de marca» en sentido contable."""),
    ("code", SETUP + """raw = entorno.load_raw()
manifest = entorno.write_manifest(raw)
x = cat[cat.familia.isin(["Coca Cola", "Pepsi"])].copy()
cov = pts.merge(st[["establecimiento_id", "giro"]], on="establecimiento_id")
cov = cov[cov.sku_id.isin(x.sku_id)].groupby(["sku_id", "giro"]).establecimiento_id.nunique().unstack(fill_value=0)
tab = x.set_index("sku_id")[["marca", "presentacion", "cantidad_base", "empresa_propietaria"]].join(cov).fillna(0)
display(tab.sort_values(["marca", "cantidad_base"]))"""),
    ("md", """## 1. ¿Qué presentaciones equivalen?

La ficha citaba Coca-Cola 600 ml en 342 tiendas y Pepsi en 306. En el archivo **no hay Pepsi de 600 ml**: Pepsi
regular solo viene en lata de 355 ml, botella de 2.5 L y de 3 L.

**Decisiones:**
1. **Comparación principal: lata 355 ml contra lata 355 ml.** Mismo tamaño y mismo envase; el precio por empaque es
   también el precio por litro. Es el par limpio.
2. **Botella familiar: Coca-Cola 2.75 L contra Pepsi 3 L, por litro.** Son las presentaciones grandes que más tiendas
   tienen (162 y 254 en supermercados). Por litro, porque los tamaños difieren (razón 0.92); el precio por litro favorece
   un poco al envase más grande, así que también se muestra por empaque.
3. **Sensibilidad: Coca-Cola Light 2 L contra Pepsi Light 2.5 L,** por litro (pocas tiendas con las dos).

**Alternativas descartadas:**
- Coca-Cola 600 ml contra cualquier Pepsi: no hay presentación equivalente.
- Coca-Cola 2.75 L contra Pepsi 2.5 L: Pepsi 2.5 L está en solo 10 supermercados.
- Promedio nacional de cada marca: mezcla tiendas y ciudades.

**Misma tienda** (`pares.marcas`): controla ciudad, cadena y día de levantamiento; es lo que el cliente ve frente al
refrigerador. Precio de tienda = mediana de la quincena."""),
    ("code", """print("Empresa propietaria verificada (sku_catalogo):")
display(cat[cat.familia.isin(["Coca Cola", "Pepsi"])].drop_duplicates("familia")[["familia", "empresa_propietaria",
        "fuente_propietaria", "url_fuente_propietaria"]])"""),
    ("md", """## 2. Canal

**Decisión:** supermercados y autoservicio, donde están casi todos los pares. Farmacias y tiendas de conveniencia se
muestran como contexto: tienen muy pocas tiendas con las dos marcas."""),
    ("code", """cob = []
for k, c in P.COMPARA.items():
    for canal in [P.CANAL, "Farmacias", "Tienda de Conveniencia"]:
        p = P.pairs(pts, st, cat, k, canal=canal)
        cob.append({"comparación": c["nombre"], "canal": canal, "tiendas con las dos": len(p),
                    "municipios": p.municipio_id.nunique() if len(p) else 0})
cob = pd.DataFrame(cob)
display(cob)"""),
    ("md", """## 3. Calidad

- Posibles errores y extremos (`estadistica.flag_prices` sobre el precio de tienda): se marcan y la prima principal se
  repite sin ellos.
- Promociones de un día: el precio de tienda es la mediana de la quincena, que las atenúa; sensibilidad solo con tiendas
  donde el precio no cambió en la quincena."""),
    ("code", """sm = pts.merge(st[st.giro == P.CANAL][["establecimiento_id"]], on="establecimiento_id")
f = E.flag_prices(sm, sku="sku_id")
ids = [c[s] for c in P.COMPARA.values() for s in ("coca", "pepsi")]
q = f[f.sku_id.isin(ids)].groupby("sku_id")[["posible_error", "extremo"]].mean().mul(100)
q["cambia_en_quincena_%"] = sm[sm.sku_id.isin(ids)].groupby("sku_id").precios_distintos.apply(lambda s: (s > 1).mean() * 100)
display(q.join(cat.set_index("sku_id")[["marca", "presentacion"]]).round(1))"""),
    ("code", """cob.to_csv(PROC / "cobertura_comparaciones.csv", index=False, encoding="utf-8-sig")
params = {"semilla": P.SEMILLA, "bootstrap_replicas": REPS, "canal": P.CANAL, "min_pares": P.MIN_PARES,
          "comparaciones": P.COMPARA}
_ = (META / "parametros.json").write_text(json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")
F = "00_datos_y_cobertura"
for k in P.COMPARA:
    r_ = cob[(cob.comparación == P.COMPARA[k]["nombre"]) & (cob.canal == P.CANAL)].iloc[0]
    reg(f"cob_{k}", r_["tiendas con las dos"], fuente=F); reg(f"cob_{k}_mun", r_.municipios, fuente=F)
reg("tiendas_coca600", tab.loc[338, P.CANAL], fuente=F)
reg("tiendas_coca_lata", tab.loc[2588, P.CANAL], fuente=F); reg("tiendas_pepsi_lata", tab.loc[1149, P.CANAL], fuente=F)"""),
    ("md", "## 4. Decisiones metodológicas"),
    ("code", """display(Markdown(f'''
| # | Decisión | Propuesta | Por qué | Alternativas descartadas |
|---|---|---|---|---|
| 1 | Par principal | lata 355 ml vs. lata 355 ml, precio por empaque | mismo tamaño y envase: el par limpio | Coca-Cola 600 ml (no hay Pepsi de 600 ml) |
| 2 | Botella familiar | Coca-Cola 2.75 L vs. Pepsi 3 L por litro; también por empaque | son las grandes con más tiendas; tamaño distinto (0.92) | Pepsi 2.5 L (10 tiendas) |
| 3 | Sensibilidad | Coca-Cola Light 2 L vs. Pepsi Light 2.5 L por litro | variante sin azúcar | — |
| 4 | Comparación | misma tienda (`pares.marcas`); precio de tienda = mediana de la quincena | controla ciudad, cadena y día | promedio nacional de cada marca |
| 5 | Prima | mediana de log(Coca-Cola / Pepsi) en % y mediana de la diferencia en pesos; % invertidos | robusta a extremos; casi no hay empates | promedio simple |
| 6 | Incertidumbre | IC90 por bootstrap de dos vías (tiendas y municipios), 500 réplicas, semilla 2026 | las tiendas de una ciudad no son independientes | IC por par |
| 7 | Desglose | cadena, formato, grupo y región con 10 pares o más | ¿dónde se reduce o se invierte? | — |
| 8 | Calidad | extremos y promociones marcados; prima repetida sin ellos | no borrar en silencio | borrar extremos |
| — | Alcance | precio relativo sostenido, no valor contable de la marca | solo hay precios al consumidor | inferir margen o ventas |
'''))"""),
    ("code", """l_ = cob[(cob.comparación == P.COMPARA["lata"]["nombre"]) & (cob.canal == P.CANAL)].iloc[0]
f_ = cob[(cob.comparación == P.COMPARA["familiar"]["nombre"]) & (cob.canal == P.CANAL)].iloc[0]
display(Markdown(
    f"**Conclusión.** No hay Pepsi de 600 ml en el archivo; el par limpio es la lata de 355 ml, que las dos marcas tienen en "
    f"**{l_['tiendas con las dos']} supermercados** de {l_.municipios} municipios. La botella familiar (2.75 L contra 3 L) se compara por "
    f"litro en {f_['tiendas con las dos']} supermercados."))"""),
])

# --------------------------------------------------------------------------- 01
write("01_prima_misma_tienda.ipynb", [
    head("01", "¿Cuánto más cuesta Coca-Cola que Pepsi en la misma tienda?",
         "En presentación equivalente y en la misma tienda, ¿cuánto sobreprecio sostiene Coca-Cola?",
         """Importa porque es la medida más directa del poder de precio de una marca: el mismo cliente, frente al mismo
refrigerador, ve las dos marcas con precios distintos. IC90 = rango probable (bootstrap de tiendas y ciudades)."""),
    ("code", SETUP + f"""res_ = {{}}
for k in P.COMPARA:
    p = P.pairs(pts, st, cat, k)
    tot, _ = P.summary(p, por=(), reps=REPS)
    res_[k] = tot
    p.to_csv(PROC / f"pares_{{k}}.csv", index=False, encoding="utf-8-sig")
tt = pd.DataFrame(res_).T
display(tt[{TOT}].round(2))
for k, t in res_.items():
    assert t["ic90_inf"] <= t["brecha_pct"] <= t["ic90_sup"], k"""),
    ("md", """## 1. Lata: precio en pesos

La prima en pesos es la mediana de la diferencia por tienda; también los precios típicos de cada marca."""),
    ("code", """pl = pd.read_csv(PROC / "pares_lata.csv")
print(f"Precio típico: Coca-Cola ${pl.pesos_b.median():.2f} · Pepsi ${pl.pesos_a.median():.2f} · diferencia típica ${np.median(pl.prima_pesos):.2f}")
display(pl.prima_pct.describe(percentiles=[.1, .25, .5, .75, .9]).round(1).to_frame("prima % por tienda"))"""),
    ("md", """## 2. Botella familiar: por litro y por empaque

Por litro Coca-Cola sale algo más cara, pero su botella es más chica (2.75 L contra 3 L): por empaque el cliente paga
menos por la Coca-Cola."""),
    ("code", """pf = P.pairs(pts, st, cat, "familiar", por="empaque")
tf, _ = P.summary(pf, por=(), reps=REPS)
print(f"Por empaque: Coca-Cola 2.75 L ${pf.pesos_b.median():.2f} · Pepsi 3 L ${pf.pesos_a.median():.2f} · "
      f"prima por empaque {tf['brecha_pct']:+.1f}% (IC90 {tf['ic90_inf']:+.1f} a {tf['ic90_sup']:+.1f})")
inv = (pf.precio_b < pf.precio_a).mean() * 100
print(f"Tiendas donde la botella de Coca-Cola cuesta menos que la de Pepsi: {inv:.0f}%")"""),
    ("md", """## 3. Sensibilidad (lata)

- sin posibles errores ni extremos;
- solo tiendas donde ninguno de los dos precios cambió en la quincena;
- todos los giros (incluye farmacias y conveniencia)."""),
    ("code", """sm = pts.merge(st[st.giro == P.CANAL][["establecimiento_id"]], on="establecimiento_id")
fl = E.flag_prices(sm, sku="sku_id")
clean = sm[~fl.extremo.to_numpy()]
stable = sm[sm.precios_distintos == 1]
var = {"Principal": P.pairs(pts, st, cat, "lata"), "Sin posibles errores ni extremos": P.pairs(clean, st, cat, "lata"),
       "Precio sin cambios en la quincena": P.pairs(stable, st, cat, "lata"), "Todos los giros": P.pairs(pts, st, cat, "lata", canal=None)}
sens = pd.DataFrame({k: P.summary(v, por=(), reps=200)[0] for k, v in var.items()}).T
display(sens[["n_pares", "brecha_pct", "ic90_inf", "ic90_sup", "brecha_pesos", "pct_invertidos"]].round(1))"""),
    ("code", """tt.to_csv(PROC / "prima_por_comparacion.csv", encoding="utf-8-sig")
sens.to_csv(PROC / "sensibilidad_lata.csv", encoding="utf-8-sig")
F = "01_prima_misma_tienda"
for k, t in res_.items():
    reg(f"prima_{k}", t["brecha_pct"], [t["ic90_inf"], t["ic90_sup"]], n=t["n_pares"], fuente=F)
    reg(f"pesos_{k}", t["brecha_pesos"], n=t["n_pares"], fuente=F)
    reg(f"inv_{k}", t["pct_invertidos"], n=t["n_pares"], fuente=F)
    reg(f"pares_{k}", t["n_pares"], fuente=F); reg(f"mun_{k}", t["municipios"], fuente=F)
reg("lata_coca", pl.pesos_b.median(), fuente=F); reg("lata_pepsi", pl.pesos_a.median(), fuente=F)
reg("lata_p10", pl.prima_pct.quantile(.1), fuente=F); reg("lata_p90", pl.prima_pct.quantile(.9), fuente=F)
reg("fam_coca", pf.pesos_b.median(), fuente=F); reg("fam_pepsi", pf.pesos_a.median(), fuente=F)
reg("fam_empaque", tf["brecha_pct"], [tf["ic90_inf"], tf["ic90_sup"]], n=tf["n_pares"], fuente=F)
reg("fam_coca_mas_barata", inv, fuente=F, nota="% de tiendas donde la botella de Coca-Cola 2.75 L cuesta menos que la Pepsi 3 L")
reg("sens_lata_min", sens.brecha_pct.min(), fuente=F); reg("sens_lata_max", sens.brecha_pct.max(), fuente=F)
t = res_["lata"]
display(Markdown(
    f"**Conclusión.** En la misma tienda, la lata de Coca-Cola cuesta **{t['brecha_pct']:.1f}% más** que la de Pepsi (IC90 "
    f"{t['ic90_inf']:.1f}–{t['ic90_sup']:.1f}%; ${pl.pesos_b.median():.2f} contra ${pl.pesos_a.median():.2f}) y solo en {t['pct_invertidos']:.0f}% de "
    f"{t['n_pares']} tiendas es más barata. En la botella familiar la prima por litro baja a {res_['familiar']['brecha_pct']:.1f}% y por empaque "
    f"la Coca-Cola de 2.75 L cuesta menos que la Pepsi de 3 L en {inv:.0f}% de las tiendas."))"""),
])

# --------------------------------------------------------------------------- 02
write("02_cadena_formato_region.ipynb", [
    head("02", "¿Cambia la prima por cadena, formato o región?",
         "¿En qué cadenas, formatos y regiones sostiene Coca-Cola más sobreprecio sobre Pepsi?",
         """Importa porque el precio de anaquel lo fija la cadena: si la prima cambia mucho entre cadenas, la marca negocia
distinto con cada una (o cada cadena usa a una de las dos marcas como gancho). Grupos con 10 pares o más."""),
    ("code", SETUP + """out = {}
for k in ["lata", "familiar"]:
    p = pd.read_csv(PROC / f"pares_{k}.csv")
    _, des = P.summary(p, reps=REPS)
    des["comparacion"] = k
    out[k] = des
    print(P.COMPARA[k]["nombre"])
    display(des[["por", "grupo", "n_pares", "municipios", "brecha_pct", "ic90_inf", "ic90_sup", "brecha_pesos",
                 "pct_invertidos", "solido"]].round(1))"""),
    ("md", """**Lectura.** En la lata todas las cadenas y regiones sostienen una prima clara. En la botella familiar el
desglose separa: en algunas cadenas Coca-Cola sale más barata por litro."""),
    ("code", """des = pd.concat(out.values())
des.to_csv(PROC / "prima_desglose.csv", index=False, encoding="utf-8-sig")
F = "02_cadena_formato_region"
lf = out["lata"][out["lata"].por == "formato"].set_index("grupo")
ff = out["familiar"][out["familiar"].por == "formato"].set_index("grupo")
lr = out["lata"][out["lata"].por == "region"].set_index("grupo")
reg("lata_formato_max", lf.brecha_pct.max(), fuente=F, nota=lf.brecha_pct.idxmax())
reg("lata_formato_min", lf.brecha_pct.min(), fuente=F, nota=lf.brecha_pct.idxmin())
reg("lata_formatos", len(lf), fuente=F); reg("lata_formatos_solidos", int(lf.solido.sum()), fuente=F)
reg("lata_region_min", lr.brecha_pct.min(), fuente=F, nota=lr.brecha_pct.idxmin()); reg("lata_region_max", lr.brecha_pct.max(), fuente=F, nota=lr.brecha_pct.idxmax())
for f_, k_ in {"Walmart": "walmart", "Bodega Aurrerá": "bodega", "Hipermercado Soriana": "soriana", "Chedraui": "chedraui"}.items():
    if f_ in lf.index:
        reg(f"lata_{k_}", lf.loc[f_, "brecha_pct"], [lf.loc[f_, "ic90_inf"], lf.loc[f_, "ic90_sup"]], n=lf.loc[f_, "n_pares"], fuente=F)
    if f_ in ff.index:
        reg(f"fam_{k_}", ff.loc[f_, "brecha_pct"], [ff.loc[f_, "ic90_inf"], ff.loc[f_, "ic90_sup"]], n=ff.loc[f_, "n_pares"], fuente=F)
reg("fam_formatos_neg", int((ff.brecha_pct < 0).sum()), n=len(ff), fuente=F)
display(Markdown(
    f"**Conclusión.** En la lata, la prima va de {lf.brecha_pct.min():.1f}% en {lf.brecha_pct.idxmin()} a {lf.brecha_pct.max():.1f}% en "
    f"{lf.brecha_pct.idxmax()}, con rango probable arriba de 0 en {int(lf.solido.sum())} de {len(lf)} formatos. En la botella familiar, "
    f"{int((ff.brecha_pct < 0).sum())} de {len(ff)} formatos tienen la Coca-Cola más barata por litro que la Pepsi."))"""),
])

# --------------------------------------------------------------------------- 03
write("03_donde_se_reduce.ipynb", [
    head("03", "¿Dónde se reduce o se invierte la prima?",
         "¿En qué tiendas Coca-Cola queda cerca del precio de Pepsi o por debajo?",
         """Importa porque ahí está la oportunidad de la marca retadora (o el riesgo de margen de la líder).

- **Invertida:** Coca-Cola más barata que Pepsi en esa tienda.
- **Reducida:** prima menor a la mitad de la mediana nacional."""),
    ("code", SETUP + """rows = []
for k in ["lata", "familiar"]:
    p = P.store_flags(pd.read_csv(PROC / f"pares_{k}.csv"))
    p.to_csv(PROC / f"pares_{k}_clase.csv", index=False, encoding="utf-8-sig")
    c = p.clase.value_counts(normalize=True).mul(100).reindex(["normal", "reducida", "igual", "invertida"]).fillna(0)
    rows.append(c.rename(P.COMPARA[k]["nombre"]))
cls = pd.DataFrame(rows)
display(cls.round(1))"""),
    ("md", "## 1. ¿En qué formatos se concentra?"),
    ("code", """pf = pd.read_csv(PROC / "pares_familiar_clase.csv")
by = pf.groupby("formato").agg(tiendas=("clase", "size"), invertida=("clase", lambda s: (s == "invertida").mean() * 100),
                               reducida=("clase", lambda s: (s == "reducida").mean() * 100)).query("tiendas >= 10")
display(by.sort_values("invertida", ascending=False).round(0))
pl = pd.read_csv(PROC / "pares_lata_clase.csv")
display(pl[pl.clase != "normal"][["cadena_comercial", "municipio_id", "pesos_a", "pesos_b", "prima_pct", "clase"]].sort_values("prima_pct").head(12).round(1))"""),
    ("md", """## 2. ¿Una tienda con prima baja en lata también la tiene en la botella?

Si fuera así, la tienda (o la cadena) estaría usando a Coca-Cola como gancho en general. Correlación de rangos entre la
prima de lata y la de botella en las tiendas que tienen las dos comparaciones."""),
    ("code", """m = pl[["establecimiento_id", "prima_pct", "formato"]].merge(pf[["establecimiento_id", "prima_pct"]], on="establecimiento_id",
                                                             suffixes=("_lata", "_familiar"))
rho = m[["prima_pct_lata", "prima_pct_familiar"]].corr(method="spearman").iloc[0, 1]
print(f"Tiendas con las dos comparaciones: {len(m)} · Spearman: {rho:+.2f}")"""),
    ("code", """cls.to_csv(PROC / "clases_prima.csv", encoding="utf-8-sig")
by.to_csv(PROC / "familiar_invertida_por_formato.csv", encoding="utf-8-sig")
F = "03_donde_se_reduce"
cl, cf = cls.iloc[0], cls.iloc[1]
reg("lata_invertida", cl.invertida, fuente=F); reg("lata_reducida", cl.reducida, fuente=F); reg("lata_igual", cl.igual, fuente=F)
reg("fam_invertida", cf.invertida, fuente=F); reg("fam_reducida", cf.reducida, fuente=F)
reg("fam_inv_max", by.invertida.max(), fuente=F, nota=by.invertida.idxmax())
reg("rho_lata_familiar", rho, n=len(m), fuente=F)
display(Markdown(
    f"**Conclusión.** En la lata la prima casi nunca se invierte ({cl.invertida:.0f}% de las tiendas) y se reduce a menos de la mitad en "
    f"{cl.reducida:.0f}%. En la botella familiar Coca-Cola sale más barata por litro en {cf.invertida:.0f}% de las tiendas, sobre todo en "
    f"{by.invertida.idxmax()} ({by.invertida.max():.0f}%). Las dos primas casi no se relacionan en la misma tienda (Spearman {rho:+.2f}): "
    "cada presentación tiene su propia política."))"""),
])

# --------------------------------------------------------------------------- 04
write("04_poder_de_precio.ipynb", [
    head("04", "¿Qué dice sobre el poder de precio de una marca líder?",
         "¿Dónde cobra la marca líder su prima y qué puede aprender una marca retadora?",
         """Importa porque la prima no es igual en todas las presentaciones: dónde la cobra la líder y dónde la cede dice
cómo administra su poder de precio. Precio por litro de cada presentación regular (mediana de los supermercados)."""),
    ("code", SETUP + """lad = P.ladder(pts, st, cat)
display(lad.round(2))"""),
    ("md", """**Lectura.** Las presentaciones individuales (lata, 600 ml) cuestan por litro dos a cuatro veces más que la
botella familiar. Ahí, donde el cliente compra por impulso y compara poco, Coca-Cola cobra su prima completa; en la
botella familiar, donde el cliente compara precio por empaque, la prima casi desaparece."""),
    ("code", """tt = pd.read_csv(PROC / "prima_por_comparacion.csv", index_col=0)
lad.to_csv(PROC / "precio_por_litro_presentacion.csv", index=False, encoding="utf-8-sig")
F = "04_poder_de_precio"
g = lad.set_index(["marca", "cantidad_base"])
reg("litro_coca_lata", g.loc[("Coca Cola", 0.355), "por_litro"], fuente=F)
reg("litro_coca_600", g.loc[("Coca Cola", 0.6), "por_litro"], fuente=F)
reg("litro_coca_275", g.loc[("Coca Cola", 2.75), "por_litro"], fuente=F)
reg("litro_pepsi_lata", g.loc[("Pepsi", 0.355), "por_litro"], fuente=F)
reg("litro_pepsi_3", g.loc[("Pepsi", 3.0), "por_litro"], fuente=F)
reg("precio_coca_600", g.loc[("Coca Cola", 0.6), "precio"], fuente=F)
reg("veces_lata_familiar", g.loc[("Coca Cola", 0.355), "por_litro"] / g.loc[("Coca Cola", 2.75), "por_litro"], fuente=F)
display(Markdown(
    f"**Conclusión.** Coca-Cola cobra su prima en el formato individual (lata: {tt.loc['lata', 'brecha_pct']:+.0f}%) y la cede en el "
    f"familiar ({tt.loc['familiar', 'brecha_pct']:+.0f}% por litro, y una botella más chica que cuesta menos por empaque). Un litro en lata "
    f"de Coca-Cola cuesta {g.loc[('Coca Cola', 0.355), 'por_litro'] / g.loc[('Coca Cola', 2.75), 'por_litro']:.1f} veces lo que un litro en la "
    "botella de 2.75 L."))"""),
])

# --------------------------------------------------------------------------- 05
write("05_visualizaciones.ipynb", [
    head("05", "Visualizaciones, reporte e implicaciones", "¿Cómo se comunica el hallazgo y qué hace cada audiencia?",
         """Convenciones: **verde ▲** = Coca-Cola más cara que Pepsi en la misma tienda; **rojo ▼** = más barata;
gris = no distinta de cero; dorado = referencia (mediana o precio de Pepsi)."""),
    ("code", SETUP + """import graficas as G, reporte, plantillas, re
res = entorno.cifras()
pl = pd.read_csv(PROC / "pares_lata.csv")
pf = pd.read_csv(PROC / "pares_familiar.csv")
des = pd.read_csv(PROC / "prima_desglose.csv")
tt = pd.read_csv(PROC / "prima_por_comparacion.csv", index_col=0)
lad = pd.read_csv(PROC / "precio_por_litro_presentacion.csv")"""),
    ("md", "## Gráfica principal: prima de la lata en la misma tienda"),
    ("code", """G.premium_main(pl, des, res, CHARTS / "01_prima_lata.png", svg=True); plt.show()"""),
    ("md", "### Versiones para publicar (1280×720 y 1080×1350)"),
    ("code", """G.premium_social(pl, res, "horizontal", SOCIAL / "01_prima_lata_1280x720.png"); plt.show()
G.premium_social(pl, res, "vertical", SOCIAL / "01_prima_lata_1080x1350.png"); plt.show()"""),
    ("md", "## Complementarias"),
    ("code", """G.by_presentation(tt, res, CHARTS / "02_prima_por_presentacion.png"); plt.show()"""),
    ("code", """G.family_by_format(des, res, CHARTS / "03_familiar_por_formato.png"); plt.show()"""),
    ("code", """G.liter_ladder(lad, res, CHARTS / "04_precio_por_litro.png"); plt.show()"""),
    ("md", "## Reporte HTML y README"),
    ("code", """GALERIA = [(g_["titulo"], g_["pie"], CHARTS / g_["archivo"]) for g_ in CFG["graficas"]]
out = reporte.build(pl, des, tt, res, CFG, GALERIA, ROOT / "docs/index.html")
print(out.relative_to(ROOT), f"{out.stat().st_size / 1e6:.1f} MB")
estructura = (ROOT / "src/estructura.md").read_text(encoding="utf-8")
(ROOT / "README.md").write_text(plantillas.readme(CFG, res, estructura), encoding="utf-8")
txt = (ROOT / "README.md").read_text(encoding="utf-8")
assert not re.search(r"\\{[a-z][a-z0-9_]*(:[^}]*)?\\}", txt), re.findall(r"\\{[a-z][a-z0-9_]*(?::[^}]*)?\\}", txt)[:5]
print("README actualizado")"""),
    ("md", "## Qué hacer con esto"),
    ("code", """for aud, acc in CFG["readme"]["acciones"].items():
    display(Markdown(f"**{aud}**\\n\\n" + "\\n".join(f"- {plantillas.render(a, res)}" for a in acc)))"""),
])

print("Notebooks generados.")
