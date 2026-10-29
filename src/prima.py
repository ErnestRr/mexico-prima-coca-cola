"""Prima de Coca-Cola sobre Pepsi en la misma tienda (motor pares.marcas).

Convención del motor: a = Pepsi, b = Coca-Cola. Prima = mediana de log(precio Coca-Cola / precio Pepsi) en %;
positiva = Coca-Cola más cara. Invertido = Coca-Cola más barata que Pepsi en esa tienda.
IC90 por bootstrap de dos vías (tiendas-producto y municipios), semilla 2026 (pares.resumir).
"""
import numpy as np
import pandas as pd

import entorno
import estadistica as E
import pares

CANAL = "Supermercado / Tienda de Autoservicio"
SEMILLA = 2026
MIN_PARES = 10          # pares para dar cifra de una cadena, formato o región
# Comparaciones (sku_id de PROFECO). Ver notebook 00 para la equivalencia de cada una.
COMPARA = {
    "lata": {"nombre": "Lata 355 ml vs. lata 355 ml", "coca": 2588, "pepsi": 1149, "por": "empaque",
             "nota": "mismo tamaño: precio por empaque (igual a precio por litro)"},
    "familiar": {"nombre": "Coca-Cola 2.75 L vs. Pepsi 3 L", "coca": 3210, "pepsi": 344, "por": "unidad",
                 "nota": "tamaños distintos (razón 0.92): precio por litro; se muestra también por empaque"},
    "light": {"nombre": "Coca-Cola Light 2 L vs. Pepsi Light 2.5 L", "coca": 2589, "pepsi": 1150, "por": "unidad",
              "nota": "sensibilidad: variantes sin azúcar, por litro"},
}


def load():
    st = entorno.tabla("tiendas")
    pts = entorno.tabla("precio_tienda_sku", columns=["establecimiento_id", "sku_id", "precio", "observaciones",
                                                      "precios_distintos"])
    cat = entorno.tabla("sku_catalogo")
    return pts, st, cat


def pairs(pts, st, cat, key, canal=CANAL, por=None):
    c = COMPARA[key]
    s = st[st.giro == canal] if canal else st
    ks = {c["coca"], c["pepsi"]}
    pts = pts[pts.establecimiento_id.isin(s.establecimiento_id)]   # el motor conserva tiendas fuera de `s` con cadena vacía
    p = pares.marcas(pts, s, cat, "Pepsi", "Coca Cola", ["producto"], por=por or c["por"],
                     filtro=lambda x: x.sku_id.isin(ks))
    p["prima_pct"] = (p.precio_b / p.precio_a - 1) * 100
    p["prima_pesos"] = p.pesos_b - p.pesos_a
    return p


def summary(p, por=("cadena_comercial", "formato", "grupo", "region"), reps=500):
    tot, des = pares.resumir(p, esperado="b>a", por=por, reps=reps, seed=SEMILLA, min_pares=MIN_PARES)
    if not des.empty:
        des["solido"] = (des.ic90_inf > 0) | (des.ic90_sup < 0)
    return tot, des


def store_flags(p):
    """Tiendas donde la prima se reduce (menos de la mitad de la mediana) o se invierte (Coca-Cola más barata)."""
    med = np.median(np.log(p.precio_b / p.precio_a))
    lr = np.log(p.precio_b / p.precio_a)
    out = p.copy()
    out["clase"] = np.select([lr < -1e-9, np.abs(lr) < 1e-9, lr < med / 2], ["invertida", "igual", "reducida"], "normal")
    return out


def ladder(pts, st, cat, canal=CANAL):
    """Precio por litro de cada presentación de Coca-Cola y Pepsi (regular): mediana de las tiendas del canal."""
    s = st[st.giro == canal]
    x = pts.merge(s[["establecimiento_id"]], on="establecimiento_id").merge(cat, on="sku_id")
    x = x[x.marca.isin(["Coca Cola", "Pepsi"])]
    x["por_litro"] = x.precio / x.cantidad_base
    return x.groupby(["marca", "presentacion", "cantidad_base"]).agg(
        tiendas=("establecimiento_id", "nunique"), precio=("precio", "median"),
        por_litro=("por_litro", "median")).reset_index().sort_values(["marca", "cantidad_base"])
