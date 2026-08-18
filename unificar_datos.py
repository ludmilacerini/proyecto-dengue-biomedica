import pandas as pd

print("🔍 Unificando la serie epidemiológica completa (2019 - 2026)...")

# 1. Cargar las 3 fuentes de datos
df_reales = pd.read_csv("datos/dataset_provincial_escalado.csv")
df_pred_pasadas = pd.read_csv("datos/predicciones.csv")

# Si el archivo de 2026 está en Descargas:
df_pred_2026 = pd.read_csv(r"C:\Users\ludmi\Downloads\predicciones_futuras.csv")

# ------------------------------------------------------------------
# A. Extraer Histórico 2019-2023 (Casos Reales)
# ------------------------------------------------------------------
df_19_23 = df_reales[df_reales["anio"] < 2024][["provincia", "anio", "semana", "casos_dengue"]].copy()
df_19_23.rename(columns={"semana": "semana_epi", "casos_dengue": "casos_real"}, inplace=True)
df_19_23["pred"] = None
df_19_23["horizonte"] = "t+2"

# ------------------------------------------------------------------
# B. Extraer Validación 2024-2025 (Casos Reales + Predicciones)
# ------------------------------------------------------------------
df_24_25 = df_pred_pasadas[df_pred_pasadas["anio"].isin([2024, 2025])][
    ["provincia", "anio", "semana_epi", "horizonte", "casos_real", "pred"]
].copy()

# ------------------------------------------------------------------
# C. Extraer Proyección 2026 (Predicciones Futuras)
# ------------------------------------------------------------------
df_26 = df_pred_2026.rename(
    columns={
        "anio_predicho": "anio",
        "semana_predicha": "semana_epi",
        "casos_predichos": "pred"
    }
)[["provincia", "anio", "semana_epi", "horizonte", "pred"]].copy()
df_26["casos_real"] = None

# ------------------------------------------------------------------
# D. Concatenar y Ordenar Dataset Final
# ------------------------------------------------------------------
df_final = pd.concat([df_19_23, df_24_25, df_26], ignore_index=True)

# Limpieza de tipos de datos
df_final["anio"] = df_final["anio"].astype(int)
df_final["semana_epi"] = df_final["semana_epi"].astype(int)
df_final.sort_values(by=["provincia", "anio", "semana_epi"], inplace=True)

# ------------------------------------------------------------------
# E. Guardar en datos/predicciones.csv
# ------------------------------------------------------------------
df_final.to_csv("datos/predicciones.csv", index=False)

print("✅ ¡Éxito total! Archivo datos/predicciones.csv actualizado con datos 2019-2026.")