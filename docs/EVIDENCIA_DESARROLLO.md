# Evidencia de desarrollo

Registro de cómo se construyó este análisis: de dónde salen los datos, qué herramientas intervinieron, cómo se validaron
las cifras y qué no puede documentarse. Solo se afirma lo que puede comprobarse con archivos del proyecto.

## 1. Origen de los datos

| Concepto | Valor |
|---|---|
| Fuente oficial | PROFECO, programa Quién es Quién en los Precios (https://qqp.profeco.gob.mx/) |
| Archivo original | `08-2026_Q2.csv` |
| Periodo | 16 al 31 de agosto de 2026 |
| Registros | 657,602 (todo el archivo) |
| SHA-256 del original | `cfde30f577cc580d93f3f260a104f85491e42f3d3dae395520e50e33706a7ea3` |
| Modificado | No. El CSV se leyó una vez, se guardó en Parquet sin quitar filas y se conserva el extracto en `data/processed/profeco_extracto.parquet` |

Las huellas del original y del Parquet están en `data/metadata/manifiesto_insumos.json`. La propiedad de las marcas
(The Coca-Cola Company y PepsiCo, Inc.) se tomó del Form 10-K 2025 de cada empresa; los enlaces están en el README.

## 2. Herramientas y bibliotecas

Versiones instaladas en el entorno del proyecto al preparar esta publicación (29 de octubre de 2026, Windows 11):

| Uso | Herramienta |
|---|---|
| Lenguaje | Python 3.13.7 |
| Datos | pandas 3.0.6, NumPy 2.5.4, PyArrow 26.0.0, PyYAML 6.0.3 |
| Notebooks | Jupyter 1.1.1, nbformat 5.11.1, nbclient 0.11.0 |
| Gráficas del análisis | matplotlib 3.11.2 |
| Reporte interactivo, infografía y animación | Plotly 7.1.0, Kaleido 1.5.0 |
| Animación | Pillow 13.0.0, imageio 2.38.1, imageio-ffmpeg 0.6.0 (FFmpeg) |

## 3. Participación de herramientas de IA

**Herramienta:** Claude Code (Anthropic), asistente de programación usado dentro de VS Code.

**Lo que está documentado**

| Trabajo | Evidencia |
|---|---|
| Desarrollo del análisis (notebooks, módulos, gráficas, reporte HTML, `verify_project.py`) | La especificación `_specs/08.md` y el plan metodológico están redactados como instrucciones para un asistente de programación; el plan lleva la nota «aprobado el 21 de octubre de 2026». Los notebooks se ejecutaron ese día (archivos con fecha 21-oct-2026, 23:19 a 23:31). Ambos documentos están en el espacio de trabajo del autor, no en este repositorio |
| Materiales de publicación: animación (`linkedin/generar_gif.py`), infografía (`linkedin/generar_infografia.py`), ampliación del README, `tests/validar_publicacion.py`, este documento y la guía editorial | Código y archivos presentes en `linkedin/`, `tests/` y `docs/`; generados en sesiones de Claude Code entre el 25 y el 29 de octubre de 2026 |

**Lo que no está documentado**

- Este repositorio no conserva el registro de las sesiones del 21 de octubre. No se sabe qué propuso la herramienta y qué
  decidió el autor en cada paso del análisis, y aquí no se atribuye ninguna decisión concreta a una u otro.
- No hay constancia escrita de una revisión línea por línea del código por parte del autor.

**Lo que corresponde al autor**

- La pregunta, la elección de los datos y la aprobación del plan metodológico (documentada en el propio plan).
- El texto de la publicación (`linkedin/post_linkedin.txt`) y los lineamientos editoriales: los dio el autor.
- La decisión de publicar.

## 4. Decisiones metodológicas documentadas

Están en el plan metodológico, en `data/metadata/parametros.json` y en los notebooks:

- **Misma tienda:** cada precio de Coca-Cola se compara con el de Pepsi en el mismo establecimiento; el precio de la tienda es
  la mediana de sus observaciones de la quincena.
- **Canal:** supermercados y tiendas de autoservicio.
- **Presentaciones:** lata de 355 ml contra lata de 355 ml; Coca-Cola 2.75 L contra Pepsi 3 L. Como los tamaños difieren
  (razón 0.92), se reporta por litro y por botella. No hay Pepsi de 600 ml, así que esa presentación no se compara.
- **Prima:** mediana de log(precio Coca-Cola / precio Pepsi) en %, y mediana de la diferencia en pesos.
- **Incertidumbre:** IC90 por bootstrap de tiendas y municipios, 500 réplicas, semilla 2026; grupos con 10 tiendas o más.
- **Lectura:** precio relativo observado; no se estima disposición a pagar, margen ni causalidad.

## 5. Validación

| Procedimiento | Qué comprueba |
|---|---|
| `verify_project.py` | Recalcula las cifras clave solo con pandas y NumPy desde los precios originales, sin usar `src/`, y comprueba que coinciden con `resultados.json` y con el README |
| `tests/validar_publicacion.py` | Que el post, el HTML, el README y la infografía usen las mismas cifras; que los enlaces y archivos existan; que no haya credenciales, correos ni rutas locales |
| Ejecución de notebooks | Los seis notebooks se ejecutan en orden sin errores |
| Revisión de la infografía (29-oct-2026) | Se verificó que el 79% corresponde al precio por botella (la Coca-Cola de 2.75 L cuesta menos que la Pepsi de 3 L en 114 de 144 tiendas; 3.5% iguales; 17.4% más cara) y no al precio por litro. Revisión visual de cada panel en tamaño de celular |

## 6. Limitaciones

- Solo supermercados monitoreados por PROFECO, durante una quincena; no es una muestra representativa de todo el mercado.
- Los precios son de anaquel: no hay ventas, volumen ni margen.
- Muchas tiendas cobran exactamente lo mismo, por lo que algunos rangos probables tocan la estimación en un extremo.
- El resultado describe precios relativos; no explica por qué las cadenas los fijan así.

## 7. Reproducción

```powershell
python -m pip install -r requirements.txt
python build_notebooks.py
foreach ($n in Get-ChildItem notebooks/0*.ipynb) {
  python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 $n.FullName
}
python verify_project.py
python tests/validar_publicacion.py
python linkedin/generar_infografia.py
```

Este documento lo redactó el asistente el 29 de octubre de 2026 a partir de los archivos del proyecto.
