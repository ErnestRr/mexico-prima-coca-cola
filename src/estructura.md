```
mexico-prima-coca-cola/
├── notebooks/        00 datos y equivalencias · 01 prima en la misma tienda · 02 cadena, formato y región
│                     03 dónde se reduce · 04 poder de precio · 05 visualizaciones
├── config.yaml       objetivo, preguntas y textos del README y del reporte
├── src/              entorno.py, prima.py (pares y prima), graficas.py, reporte.py
├── data/processed/   pares por tienda, prima por presentación y cadena, precio por litro (CSV) y resultados.json
├── data/metadata/    parametros.json, manifiesto_insumos.json
├── outputs/charts/   gráficas PNG (la principal también en SVG)
├── outputs/social/   versiones de 1280×720 y 1080×1350
├── docs/index.html   reporte interactivo autocontenido (GitHub Pages)
├── publicacion/      infografía, animación y texto de la publicación (scripts incluidos)
├── tests/            validar_publicacion.py: cifras, enlaces, archivos y datos sensibles
├── build_notebooks.py
└── verify_project.py
```

```powershell
python -m pip install -r requirements.txt
python build_notebooks.py
$env:OMP_NUM_THREADS = 1; $env:OPENBLAS_NUM_THREADS = 1; $env:MKL_NUM_THREADS = 1
foreach ($n in Get-ChildItem notebooks/0*.ipynb) {
  python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 $n.FullName
}
python verify_project.py
python tests/validar_publicacion.py
```

`verify_project.py` recalcula las cifras clave solo con pandas y numpy a partir de los precios originales y comprueba que
coinciden con este README. `tests/validar_publicacion.py` revisa que el HTML, la infografía y el texto de la publicación
usen esas mismas cifras.

Materiales de `publicacion/` (opcionales, requieren Kaleido): `python publicacion/generar_infografia.py` y `python publicacion/generar_gif.py` (la animación tarda unos 10 minutos).
