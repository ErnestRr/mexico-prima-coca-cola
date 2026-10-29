"""Verificación independiente: recalcula las cifras clave solo con pandas y numpy a partir de los precios originales
(extracto publicado o Parquet del núcleo), sin usar los módulos de src/, y comprueba que coinciden con el README y con
data/processed/resultados.json."""
from pathlib import Path
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROC = ROOT / "data/processed"
README = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
RES = json.loads((PROC / "resultados.json").read_text(encoding="utf-8"))
src = PROC / "profeco_extracto.parquet"
if not src.exists():
    src = ROOT.parent / "_profeco_core/data/profeco_2026_08_q2.parquet"
df = pd.read_parquet(src, columns=["precio_num", "giro", "sku_id", "establecimiento_id"])
df = df[(df.precio_num > 0) & (df.giro.astype(str) == "Supermercado / Tienda de Autoservicio")]
# Precio de tienda = mediana de la quincena
tienda = df.groupby(["establecimiento_id", "sku_id"]).precio_num.median().unstack("sku_id")
LITROS = {2588: 0.355, 1149: 0.355, 3210: 2.75, 344: 3.0}


def prima(coca, pepsi, por_litro):
    x = tienda[[coca, pepsi]].dropna()
    a, b = x[pepsi], x[coca]
    if por_litro:
        a, b = a / LITROS[pepsi], b / LITROS[coca]
    return (np.exp(np.median(np.log(b / a))) - 1) * 100, x, (b < a).mean() * 100


lata, xl, inv_l = prima(2588, 1149, False)
fam, xf, _ = prima(3210, 344, True)
pesos = np.median(xl[2588] - xl[1149])
fam_barata = (xf[3210] < xf[344]).mean() * 100
checks = {
    "prima lata": (lata, "prima_lata", f"cuesta {lata:.1f}% más que la de Pepsi"),
    "pesos por lata": (pesos, "pesos_lata", f"diferencia típica de ${pesos:.2f} por lata"),
    "tiendas con las dos latas": (len(xl), "pares_lata", f"de los {len(xl)} supermercados"),
    "invertidas lata": (inv_l, "inv_lata", f"más barata que Pepsi en solo {inv_l:.0f}%"),
    "prima familiar por litro": (fam, "prima_familiar", f"{fam:.1f}% por litro"),
    "botella Coca-Cola más barata": (fam_barata, "fam_coca_mas_barata", f"más barata en {fam_barata:.0f}% de las tiendas"),
}
for name, (val, key, txt) in checks.items():
    assert abs(val - RES[key]["cifra"]) < 1e-6, f"{name}: {val} vs resultados.json {RES[key]['cifra']}"
    assert txt in README, f"{name}: «{txt}» no aparece en el README"
    print(f"OK  {name:30s} {txt}")

for nb_path in sorted((ROOT / "notebooks").glob("0*.ipynb")):
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is not None, f"{nb_path.name} sin ejecutar"
            assert not any(o["output_type"] == "error" for o in cell["outputs"]), nb_path.name
for f in ["outputs/charts/01_prima_lata.png", "outputs/charts/01_prima_lata.svg", "outputs/social/01_prima_lata_1280x720.png",
          "outputs/social/01_prima_lata_1080x1350.png", "outputs/charts/02_prima_por_presentacion.png",
          "outputs/charts/03_familiar_por_formato.png", "outputs/charts/04_precio_por_litro.png", "docs/index.html",
          "data/metadata/manifiesto_insumos.json"]:
    assert (ROOT / f).exists(), f"Falta {f}"
assert "elaboración propia con datos de PROFECO" in README
assert "URL oficial" in README
print("Verificación correcta: las cifras clave del README se reproducen de forma independiente "
      "y los notebooks 00–05 se ejecutaron sin errores.")
