# Materiales de publicación

| Archivo | Contenido |
|---|---|
| `infografia_coca_cola_pepsi.png` | Infografía de 1080 × 1350 px con tres gráficas del análisis |
| `generar_infografia.py` | Genera la infografía con Plotly y Kaleido, a partir de `data/processed/` |
| `post_linkedin.txt` | Texto de la publicación |
| `PROMPT_LINKEDIN.md` | Guía editorial reutilizable para futuras publicaciones |
| `coca_cola_pepsi_plotly.gif` | Animación de 15 s (1080 × 1080) con las cuatro gráficas del análisis |
| `coca_cola_pepsi_plotly.mp4` | La misma animación en video |
| `generar_gif.py` | Genera la animación y el video |

## Regenerar

```powershell
python -m pip install plotly kaleido pillow imageio imageio-ffmpeg
python linkedin/generar_infografia.py    # unos segundos
python linkedin/generar_gif.py           # unos 10 minutos: cada cuadro se exporta desde Plotly
```

Las cifras salen de `data/processed/` (`resultados.json`, `pares_lata.csv`, `pares_familiar.csv`, `prima_desglose.csv`,
`precio_por_litro_presentacion.csv`); los scripts no recalculan resultados.

## Modificar la animación

- Duración de cada escena: lista `ESCENAS`; animación de entrada: `ANIM`; fundido entre escenas: `FUNDIDO`.
- Cuadros por segundo: `FPS`. Tamaños de letra: `TITLE_PX`, `SUB_PX`, `AX_PX`, `LAB_PX`, `SMALL_PX`.
- Los textos de cada escena están dentro de su función `escena_*`.

Fuente: Profeco, Quién es Quién en los Precios, 16–31 de agosto de 2026. Cálculos propios.
