# ContaSim — Simulador Contable Educativo

Aplicación web interactiva para simular el ciclo contable completo de una organización. Desarrollada con Python y Streamlit, orientada a estudiantes universitarios de contabilidad y administración.

---

## ¿Qué hace?

ContaSim implementa el sistema de **partida doble** completo, desde el registro de asientos hasta la generación automática de los cuatro estados financieros principales.

- **Plan de Cuentas** — 65 cuentas predeterminadas, posibilidad de agregar y eliminar cuentas propias
- **Libro Diario** — Carga de asientos con validación de partida doble (Debe = Haber), sugerencias de contrapartida por tipo de cuenta, edición y eliminación de asientos
- **Libro Mayor** — Generado automáticamente, con saldo acumulado y clasificación deudor/acreedor
- **Estados Financieros** — Balance General, Estado de Resultados, Estado de Evolución del Patrimonio Neto y Estado de Flujo de Efectivo, todos descargables en Excel
- **Dashboard** — Indicadores de liquidez, liquidez ácida, solvencia, endeudamiento, ROA y margen neto con semáforo visual

---

## Stack

- **Python 3.10+**
- **Streamlit** — interfaz web
- **SQLite** — base de datos local (sin configuración adicional)
- **Pandas** — cálculo de estados financieros
- **openpyxl** — exportación a Excel

---

## Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/contasim.git
cd contasim

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Correr la app
streamlit run app.py
```

La base de datos SQLite (`contabilidad.db`) se crea automáticamente en el primer arranque con el plan de cuentas predeterminado.

---

## Publicar en Streamlit Cloud

1. Subir este repositorio a GitHub (puede ser público o privado)
2. Ir a [share.streamlit.io](https://share.streamlit.io) e iniciar sesión con GitHub
3. Seleccionar el repositorio y configurar:
   - **Main file path:** `app.py`
   - **Python version:** 3.10 o superior
4. Hacer clic en **Deploy**

> La base de datos se crea en cada sesión nueva. Para uso en producción con datos persistentes, se recomienda migrar a una base de datos externa (PostgreSQL, Supabase, etc.).

---

## Estructura del proyecto

```
contasim/
├── app.py                    # Entry point y página de inicio
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml           # Tema visual
├── utils/
│   ├── database.py           # Inicialización SQLite y cuentas predeterminadas
│   ├── contabilidad.py       # Lógica contable, estados financieros, ratios
│   └── styles.py             # CSS, helpers de formato y UI
└── pages/
    ├── plan_cuentas.py
    ├── libro_diario.py
    ├── libro_mayor.py
    ├── estados_financieros.py
    └── dashboard.py
```

---

## Lógica contable implementada

### Tipos de cuentas y saldo normal

| Tipo | Saldo normal | Aumenta con | Disminuye con |
|---|---|---|---|
| Activo | Deudor | Debe | Haber |
| Pasivo | Acreedor | Haber | Debe |
| Patrimonio Neto | Acreedor | Haber | Debe |
| Resultado Positivo (R+) | Acreedor | Haber | Debe |
| Resultado Negativo (R−) | Deudor | Debe | Haber |

### Validaciones aplicadas

- Todo asiento debe cumplir **Debe = Haber** antes de guardarse
- Las cuentas predeterminadas no pueden eliminarse si tienen movimientos
- El Balance General verifica que **Activo = Pasivo + Patrimonio Neto**

### Estados financieros

- **Balance General** — saldos de activos, pasivos y patrimonio al cierre del período
- **Estado de Resultados** — ingresos menos egresos del período
- **Evolución del Patrimonio Neto** — saldos actuales por componente del patrimonio
- **Flujo de Efectivo** — método directo, clasificado en actividades operativas, de inversión y de financiación

### Indicadores del dashboard

| Indicador | Fórmula | Referencia |
|---|---|---|
| Liquidez corriente | Activo corriente / Pasivo corriente | > 1.5 |
| Liquidez ácida | (Activo corriente − Inventarios) / Pasivo corriente | > 0.8 |
| Solvencia total | Activo total / Pasivo total | > 1 |
| Endeudamiento | Pasivo total / Patrimonio neto | < 1 |
| ROA | Resultado neto / Activo total × 100 | > 5% |
| Margen neto | Resultado neto / Ingresos × 100 | > 10% |

---

## Consideraciones de uso

Esta aplicación es un **complemento educativo**. No reemplaza software contable profesional ni debe utilizarse para declaraciones impositivas o informes legales. Los estados financieros generados tienen fines pedagógicos y no están preparados bajo ninguna norma contable profesional específica (NIC/NIIF, RT, etc.).

---

## Contribuciones

Las contribuciones son bienvenidas. Para cambios importantes, abrí primero un issue describiendo qué querés modificar.

1. Fork del repositorio
2. Crear una rama: `git checkout -b feature/nombre-de-la-feature`
3. Commit con mensaje claro: `git commit -m "feat: descripción"`
4. Push y Pull Request

---

## Licencia

MIT — libre para uso educativo y personal.
