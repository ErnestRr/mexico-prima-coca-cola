"""Validación de la publicación: cifras, enlaces, archivos y datos sensibles. Solo usa la biblioteca estándar.

Comprueba que el texto de la publicación, el reporte HTML, el README y la infografía digan lo mismo que
data/processed/resultados.json, que los enlaces y archivos existan, y que no haya credenciales, correos ni rutas locales.
Uso: python tests/validar_publicacion.py   (sale con código 1 si algo falla)
"""
from pathlib import Path
import importlib.util
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = "https://ernestrr.github.io/mexico-prima-coca-cola/"
fallas = []


def check(nombre, ok, detalle=""):
    print(("OK    " if ok else "FALLA ") + nombre + (f" — {detalle}" if detalle and not ok else ""))
    if not ok:
        fallas.append(nombre)


def leer(ruta):
    return (ROOT / ruta).read_text(encoding="utf-8")


R = {k: v["cifra"] for k, v in json.loads(leer("data/processed/resultados.json")).items()}

# ----------------------------------------------------------------------------- 1. cifras del análisis
esperadas = {"prima_lata": (23.7, 0.05), "pesos_lata": (4.5, 0.005), "prima_familiar": (4.9, 0.05),
             "fam_empaque": (-3.8, 0.05), "fam_coca_mas_barata": (79, 0.5), "pares_lata": (184, 0), "pares_familiar": (144, 0)}
for k, (v, tol) in esperadas.items():
    check(f"cifra {k} = {v}", abs(R[k] - v) <= tol, f"resultados.json tiene {R[k]}")

# ----------------------------------------------------------------------------- 2. publicación
post = leer("publicacion/texto_publicacion.txt")
check("post: redondeo del gancho (24%) coincide con la prima", round(R["prima_lata"]) == 24)
for t in ["24%", "23.7%", "4.9%", "79%", PAGES, "16–31 de agosto de 2026"]:
    check(f"post contiene «{t}»", t in post)

# ----------------------------------------------------------------------------- 3. HTML y README
html = leer("docs/index.html")
readme = leer("README.md")
for t in ["23.7%", "4.9%", "79%", "184", "144", "3.8%"]:
    check(f"HTML contiene «{t}»", t in html)
    check(f"README contiene «{t}»", t in readme)
for t in [PAGES, "publicacion/infografia_coca_cola_pepsi.png", "Tecnologías utilizadas",
          "Definiciones y criterios de comparabilidad", "Datos y cobertura"]:
    check(f"README contiene «{t}»", t in readme)
rotos = [m for m in re.findall(r"\]\(([^)\s]+)\)", readme) if not m.startswith(("http", "#")) and not (ROOT / m).exists()]
check("README: enlaces relativos existentes", not rotos, str(rotos))

# ----------------------------------------------------------------------------- 4. archivos
png = ROOT / "publicacion/infografia_coca_cola_pepsi.png"
dim = struct.unpack(">II", png.read_bytes()[16:24]) if png.exists() else None
check("infografía de 1080 × 1350 px", dim == (1080, 1350), str(dim))
gif, mp4 = ROOT / "publicacion/coca_cola_pepsi_plotly.gif", ROOT / "publicacion/coca_cola_pepsi_plotly.mp4"
check("animación GIF < 5 MB", gif.exists() and gif.stat().st_size < 5e6)
check("animación MP4 presente", mp4.exists())
for f in ["requirements.txt", "verify_project.py",
          "data/metadata/manifiesto_insumos.json"]:
    check(f"existe {f}", (ROOT / f).exists())
grandes = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p.stat().st_size > 100e6]
check("ningún archivo de 100 MB o más", not grandes, str(grandes))

# ----------------------------------------------------------------------------- 5. dependencias
modulo = {"pyyaml": "yaml", "pillow": "PIL", "imageio-ffmpeg": "imageio_ffmpeg", "adjusttext": "adjustText"}
faltan = []
for linea in leer("requirements.txt").split():
    nombre = re.split(r"[<>=]", linea)[0].lower()
    if importlib.util.find_spec(modulo.get(nombre, nombre.replace("-", "_"))) is None:
        faltan.append(nombre)
check("dependencias de requirements.txt instaladas", not faltan, str(faltan))

# ----------------------------------------------------------------------------- 6. datos sensibles
binarios = {".parquet", ".png", ".gif", ".mp4", ".svg", ".pyc"}
# Formatos conocidos de credenciales (se buscan en todos los archivos de texto)...
tokens = re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----")
# ...y asignaciones genéricas (clave = "valor"), salvo en el HTML, donde el código minificado de Plotly dice «font token: »
asignacion = re.compile(r"(?i:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"][^'\"]{6,}")
correo = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}")
local = re.compile(r"C:\\{1,2}Users|C:/Users|THINK" + "PAD|/home/[a-z]")
hallazgos = []
for p in ROOT.rglob("*"):
    if not p.is_file() or ".git" in p.parts or "__pycache__" in p.parts or p.suffix in binarios or p == Path(__file__).resolve():
        continue
    txt = p.read_text(encoding="utf-8", errors="ignore")
    rel = str(p.relative_to(ROOT))
    reglas = (("credencial", tokens), ("ruta local", local))
    if p.suffix != ".html":
        reglas += (("credencial", asignacion), ("correo", correo))
    for etiqueta, rx in reglas:
        if rx.search(txt):
            hallazgos.append(f"{etiqueta}: {rel}")
check("sin credenciales, correos ni rutas locales", not hallazgos, "; ".join(hallazgos))

print()
if fallas:
    print(f"{len(fallas)} validaciones fallaron.")
    sys.exit(1)
print("Validación correcta: la publicación usa las mismas cifras del análisis y no contiene datos sensibles.")
