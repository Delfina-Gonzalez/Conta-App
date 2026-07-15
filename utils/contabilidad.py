"""
Core accounting logic: journal entries, ledger, financial statements.
All calculations follow double-entry bookkeeping principles.
"""

from __future__ import annotations
from typing import Optional
import pandas as pd
from utils.database import get_connection


# ─────────────────────────────────────────
# ACCOUNT HELPERS
# ─────────────────────────────────────────

TIPO_LABELS = {
    "activo": "Activo",
    "pasivo": "Pasivo",
    "patrimonio": "Patrimonio Neto",
    "r_positivo": "Resultado Positivo (Ingreso)",
    "r_negativo": "Resultado Negativo (Egreso)",
}

SUBCATEGORIA_LABELS = {
    "corriente": "Corriente",
    "no_corriente": "No Corriente",
    None: "—",
}

# Natural balance side per account type (DEBE increases / HABER increases)
# activo      → DEBE increases (deudor)
# pasivo      → HABER increases (acreedor)
# patrimonio  → HABER increases (acreedor)
# r_positivo  → HABER increases (acreedor)
# r_negativo  → DEBE increases (deudor)
SALDO_NORMAL = {
    "activo": "deudor",
    "pasivo": "acreedor",
    "patrimonio": "acreedor",
    "r_positivo": "acreedor",
    "r_negativo": "deudor",
}

# Suggested counterparts per account type with explanation
CONTRAPARTIDAS_SUGERIDAS = {
    "activo": [
        ("pasivo", "Se adquiere un activo financiado por un pasivo (ej: compra a crédito)"),
        ("patrimonio", "Se adquiere un activo mediante aporte de capital"),
        ("activo", "Se transforma un activo en otro (ej: cobro de clientes → caja)"),
        ("r_positivo", "El activo aumenta por un ingreso devengado"),
    ],
    "pasivo": [
        ("activo", "Se cancela un pasivo entregando activos (ej: pago en efectivo)"),
        ("pasivo", "Se reclasifica o refinancia una deuda"),
    ],
    "patrimonio": [
        ("activo", "El aporte de capital ingresa como activo (ej: dinero)"),
        ("r_positivo", "Se incorpora resultado positivo al patrimonio"),
        ("r_negativo", "Se registra pérdida que reduce el patrimonio"),
    ],
    "r_positivo": [
        ("activo", "El ingreso genera un activo (ej: caja, clientes)"),
        ("pasivo", "El ingreso viene acompañado de un impuesto (IVA Débito)"),
    ],
    "r_negativo": [
        ("activo", "El gasto reduce un activo (ej: efectivo, mercaderías)"),
        ("pasivo", "El gasto genera una deuda (ej: sueldos a pagar)"),
    ],
}

# ─────────────────────────────────────────
# CLASIFICACIÓN DE CUENTAS DE RESULTADO
# (para armar el Estado de Resultados por función, según la teoría contable)
# ─────────────────────────────────────────

# Categoría por código de cuenta predeterminada.
CATEGORIA_RESULTADO_POR_CODIGO = {
    "4.1.01": "ingreso_venta",
    "4.1.02": "ingreso_venta",
    "4.1.03": "financiero",
    "4.1.04": "otro_ingreso",
    "4.1.05": "otro_ingreso",
    "4.1.06": "financiero",
    "4.1.07": "otro_ingreso",
    "5.1.01": "costo_venta",
    "5.1.02": "gasto_operativo",
    "5.1.03": "gasto_operativo",
    "5.1.04": "gasto_operativo",
    "5.1.05": "gasto_operativo",
    "5.1.06": "gasto_operativo",
    "5.1.07": "gasto_operativo",
    "5.1.08": "financiero",
    "5.1.09": "gasto_operativo",
    "5.1.10": "impuesto",
    "5.1.11": "gasto_operativo",
    "5.1.12": "gasto_operativo",
    "5.1.13": "financiero",
    "5.1.14": "gasto_operativo",
    "5.1.15": "gasto_operativo",
}


def _categoria_resultado(codigo: str, nombre: str, tipo: str) -> str:
    """
    Devuelve la categoría funcional de una cuenta de resultado:
    ingreso_venta | costo_venta | otro_ingreso | gasto_operativo | financiero | impuesto
    Usa el código para las cuentas predeterminadas; para cuentas nuevas
    (agregadas por el usuario) infiere la categoría por palabras clave del nombre.
    """
    if codigo in CATEGORIA_RESULTADO_POR_CODIGO:
        return CATEGORIA_RESULTADO_POR_CODIGO[codigo]

    n = (nombre or "").lower()
    if "impuesto" in n and "ganancia" in n:
        return "impuesto"
    if "interes" in n or "interés" in n or "cambio" in n:
        return "financiero"
    if tipo == "r_positivo":
        return "ingreso_venta" if "venta" in n else "otro_ingreso"
    else:  # r_negativo
        if "costo" in n and "vent" in n:
            return "costo_venta"
        return "gasto_operativo"


def get_all_cuentas() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM cuentas WHERE activa = 1 ORDER BY codigo",
        conn,
    )
    conn.close()
    return df


def get_cuenta_by_id(cuenta_id: int) -> Optional[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cuentas WHERE id = ?", (cuenta_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_cuenta(codigo, nombre, tipo, subcategoria, descripcion=""):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO cuentas (codigo,nombre,tipo,subcategoria,descripcion) VALUES (?,?,?,?,?)",
            (codigo.strip(), nombre.strip(), tipo, subcategoria or None, descripcion.strip()),
        )
        conn.commit()
        return True, "Cuenta creada exitosamente."
    except Exception as e:
        return False, f"Error al crear cuenta: {e}"
    finally:
        conn.close()


def delete_cuenta(cuenta_id: int):
    conn = get_connection()
    cur = conn.cursor()
    # Check if account is used in any journal entry
    cur.execute(
        "SELECT COUNT(*) FROM lineas_asiento WHERE cuenta_id = ?", (cuenta_id,)
    )
    if cur.fetchone()[0] > 0:
        conn.close()
        return False, "No se puede eliminar: la cuenta tiene movimientos registrados."
    try:
        cur.execute("DELETE FROM cuentas WHERE id = ? AND es_default = 0", (cuenta_id,))
        if cur.rowcount == 0:
            conn.close()
            return False, "Las cuentas predeterminadas no pueden eliminarse."
        conn.commit()
        return True, "Cuenta eliminada."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def toggle_cuenta(cuenta_id: int, activa: bool):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE cuentas SET activa = ? WHERE id = ?", (1 if activa else 0, cuenta_id))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# JOURNAL (LIBRO DIARIO)
# ─────────────────────────────────────────

def get_next_asiento_number() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(numero), 0) + 1 FROM asientos")
    n = cur.fetchone()[0]
    conn.close()
    return n


def get_all_asientos() -> list[dict]:
    """Return all journal entries with their lines."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, a.numero, a.fecha, a.descripcion, a.creado_en,
               l.id as linea_id, l.cuenta_id, c.codigo, c.nombre, c.tipo,
               l.debe, l.haber, l.descripcion as linea_desc
        FROM asientos a
        LEFT JOIN lineas_asiento l ON l.asiento_id = a.id
        LEFT JOIN cuentas c ON c.id = l.cuenta_id
        ORDER BY a.numero, l.id
    """)
    rows = cur.fetchall()
    conn.close()

    asientos = {}
    for r in rows:
        aid = r["id"]
        if aid not in asientos:
            asientos[aid] = {
                "id": aid,
                "numero": r["numero"],
                "fecha": r["fecha"],
                "descripcion": r["descripcion"],
                "creado_en": r["creado_en"],
                "lineas": [],
            }
        if r["linea_id"]:
            asientos[aid]["lineas"].append({
                "linea_id": r["linea_id"],
                "cuenta_id": r["cuenta_id"],
                "codigo": r["codigo"],
                "nombre": r["nombre"],
                "tipo": r["tipo"],
                "debe": r["debe"] or 0,
                "haber": r["haber"] or 0,
                "descripcion": r["linea_desc"],
            })
    return list(asientos.values())


def save_asiento(fecha: str, descripcion: str, lineas: list[dict]):
    """
    lineas: list of {cuenta_id, debe, haber, descripcion}
    Returns (ok, message, asiento_id)
    """
    if not lineas:
        return False, "El asiento no tiene líneas.", None

    total_debe = sum(l.get("debe", 0) or 0 for l in lineas)
    total_haber = sum(l.get("haber", 0) or 0 for l in lineas)

    if round(total_debe, 2) != round(total_haber, 2):
        return (
            False,
            f"Asiento desbalanceado: DEBE={total_debe:.2f} ≠ HABER={total_haber:.2f}. "
            "La partida doble requiere que DEBE = HABER.",
            None,
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        numero = get_next_asiento_number()
        cur.execute(
            "INSERT INTO asientos (numero, fecha, descripcion) VALUES (?,?,?)",
            (numero, fecha, descripcion.strip()),
        )
        asiento_id = cur.lastrowid
        for l in lineas:
            cur.execute(
                """INSERT INTO lineas_asiento (asiento_id, cuenta_id, debe, haber, descripcion)
                   VALUES (?,?,?,?,?)""",
                (
                    asiento_id,
                    l["cuenta_id"],
                    float(l.get("debe") or 0),
                    float(l.get("haber") or 0),
                    l.get("descripcion", ""),
                ),
            )
        conn.commit()
        return True, f"Asiento N° {numero} registrado correctamente.", asiento_id
    except Exception as e:
        conn.rollback()
        return False, f"Error al guardar asiento: {e}", None
    finally:
        conn.close()


def delete_asiento(asiento_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM asientos WHERE id = ?", (asiento_id,))
        conn.commit()
        return True, "Asiento eliminado."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def update_asiento(asiento_id: int, fecha: str, descripcion: str, lineas: list[dict]):
    """Replace an existing journal entry's lines."""
    total_debe = sum(l.get("debe", 0) or 0 for l in lineas)
    total_haber = sum(l.get("haber", 0) or 0 for l in lineas)
    if round(total_debe, 2) != round(total_haber, 2):
        return False, f"Asiento desbalanceado: DEBE={total_debe:.2f} ≠ HABER={total_haber:.2f}."

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE asientos SET fecha=?, descripcion=? WHERE id=?",
            (fecha, descripcion.strip(), asiento_id),
        )
        cur.execute("DELETE FROM lineas_asiento WHERE asiento_id=?", (asiento_id,))
        for l in lineas:
            cur.execute(
                """INSERT INTO lineas_asiento (asiento_id, cuenta_id, debe, haber, descripcion)
                   VALUES (?,?,?,?,?)""",
                (
                    asiento_id,
                    l["cuenta_id"],
                    float(l.get("debe") or 0),
                    float(l.get("haber") or 0),
                    l.get("descripcion", ""),
                ),
            )
        conn.commit()
        return True, "Asiento actualizado correctamente."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


# ─────────────────────────────────────────
# LEDGER (LIBRO MAYOR)
# ─────────────────────────────────────────

def get_libro_mayor() -> dict[str, dict]:
    """
    Returns a dict keyed by cuenta_id with ledger movements and running balance.
    """
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT c.id as cuenta_id, c.codigo, c.nombre, c.tipo, c.subcategoria,
               a.numero as asiento_num, a.fecha, a.descripcion as asiento_desc,
               l.debe, l.haber
        FROM lineas_asiento l
        JOIN cuentas c ON c.id = l.cuenta_id
        JOIN asientos a ON a.id = l.asiento_id
        ORDER BY c.codigo, a.fecha, a.numero
        """,
        conn,
    )
    conn.close()

    resultado = {}
    for _, row in df.iterrows():
        cid = row["cuenta_id"]
        if cid not in resultado:
            resultado[cid] = {
                "cuenta_id": cid,
                "codigo": row["codigo"],
                "nombre": row["nombre"],
                "tipo": row["tipo"],
                "subcategoria": row["subcategoria"],
                "movimientos": [],
                "total_debe": 0,
                "total_haber": 0,
            }
        resultado[cid]["movimientos"].append({
            "asiento_num": row["asiento_num"],
            "fecha": row["fecha"],
            "descripcion": row["asiento_desc"],
            "debe": row["debe"] or 0,
            "haber": row["haber"] or 0,
        })
        resultado[cid]["total_debe"] += row["debe"] or 0
        resultado[cid]["total_haber"] += row["haber"] or 0

    # Compute saldo
    for cid, data in resultado.items():
        td, th = data["total_debe"], data["total_haber"]
        natural = SALDO_NORMAL.get(data["tipo"], "deudor")
        if natural == "deudor":
            data["saldo"] = td - th
            data["tipo_saldo"] = "Deudor" if td >= th else "Acreedor"
        else:
            data["saldo"] = th - td
            data["tipo_saldo"] = "Acreedor" if th >= td else "Deudor"
        data["saldo_abs"] = abs(data["saldo"])

    return resultado


def get_saldos_por_cuenta() -> dict[int, dict]:
    """Lightweight saldo summary for use in financial statements."""
    mayor = get_libro_mayor()
    return {
        cid: {
            "codigo": d["codigo"],
            "nombre": d["nombre"],
            "tipo": d["tipo"],
            "subcategoria": d["subcategoria"],
            "saldo": d["saldo"],
            "saldo_abs": d["saldo_abs"],
            "tipo_saldo": d["tipo_saldo"],
        }
        for cid, d in mayor.items()
    }


# ─────────────────────────────────────────
# FINANCIAL STATEMENTS
# ─────────────────────────────────────────

def _saldos_df() -> pd.DataFrame:
    saldos = get_saldos_por_cuenta()
    if not saldos:
        return pd.DataFrame()
    return pd.DataFrame(list(saldos.values()))


def get_balance_general() -> dict:
    """Estado de Situación Patrimonial."""
    df = _saldos_df()
    if df.empty:
        return {"activo_corriente": [], "activo_no_corriente": [],
                "pasivo_corriente": [], "pasivo_no_corriente": [],
                "patrimonio": [], "total_activo": 0, "total_pasivo": 0,
                "total_patrimonio": 0}

    def rows(tipo, sub=None):
        mask = df["tipo"] == tipo
        if sub:
            mask &= df["subcategoria"] == sub
        return df[mask][["codigo", "nombre", "saldo"]].to_dict("records")

    total_activo = df[df["tipo"] == "activo"]["saldo"].sum()
    total_pasivo = df[df["tipo"] == "pasivo"]["saldo"].sum()
    total_patrimonio_cuentas = df[df["tipo"] == "patrimonio"]["saldo"].sum()
    resultado = (
        df[df["tipo"] == "r_positivo"]["saldo"].sum()
        - df[df["tipo"] == "r_negativo"]["saldo"].sum()
    )

    # Build the patrimonio rows and append the period result as its own line,
    # so the accounts shown under "Patrimonio Neto" actually sum to the subtotal.
    patrimonio_rows = rows("patrimonio")
    if resultado != 0:
        patrimonio_rows.append({
            "codigo": "",
            "nombre": "Resultado del Ejercicio (Ganancia)" if resultado >= 0
                      else "Resultado del Ejercicio (Pérdida)",
            "saldo": resultado,
        })

    total_patrimonio = total_patrimonio_cuentas + resultado

    return {
        "activo_corriente": rows("activo", "corriente"),
        "activo_no_corriente": rows("activo", "no_corriente"),
        "pasivo_corriente": rows("pasivo", "corriente"),
        "pasivo_no_corriente": rows("pasivo", "no_corriente"),
        "patrimonio": patrimonio_rows,
        "resultado_detalle": resultado,
        "total_activo": total_activo,
        "total_pasivo": total_pasivo,
        "total_patrimonio": total_patrimonio,
        "total_pasivo_patrimonio": total_pasivo + total_patrimonio,
    }


def get_estado_resultados() -> dict:
    """
    Estado de Resultados (PyG) por función, siguiendo el esquema teórico:

    Ingresos por ventas
    (-) Costo de ventas
    = Resultado Bruto
    (+) Otros ingresos operativos
    (-) Gastos operativos
    = Resultado Operativo
    (+/-) Resultado financiero (intereses, diferencia de cambio)
    = Resultado antes de impuestos
    (-) Impuesto a las ganancias
    = Resultado Neto del ejercicio
    """
    vacio = {
        "ingresos_venta": [], "total_ingresos_venta": 0.0,
        "costos_venta": [], "total_costo_venta": 0.0,
        "resultado_bruto": 0.0,
        "otros_ingresos": [], "total_otros_ingresos": 0.0,
        "gastos_operativos": [], "total_gastos_operativos": 0.0,
        "resultado_operativo": 0.0,
        "ingresos_financieros": [], "total_ingresos_financieros": 0.0,
        "egresos_financieros": [], "total_egresos_financieros": 0.0,
        "resultado_financiero": 0.0,
        "resultado_antes_impuestos": 0.0,
        "impuesto_ganancias": [], "total_impuesto_ganancias": 0.0,
        "resultado_neto": 0.0,
        # legacy keys kept for backward-compatibility (e.g. dashboard/exports)
        "ingresos": [], "egresos": [], "total_ingresos": 0.0, "total_egresos": 0.0,
    }

    df = _saldos_df()
    if df.empty:
        return vacio

    resultado_df = df[df["tipo"].isin(["r_positivo", "r_negativo"])].copy()
    if resultado_df.empty:
        return vacio

    resultado_df["categoria"] = resultado_df.apply(
        lambda r: _categoria_resultado(r["codigo"], r["nombre"], r["tipo"]), axis=1
    )

    def grupo(cat):
        return resultado_df[resultado_df["categoria"] == cat][
            ["codigo", "nombre", "saldo"]
        ].to_dict("records")

    ingresos_venta = grupo("ingreso_venta")
    costos_venta = grupo("costo_venta")
    otros_ingresos = grupo("otro_ingreso")
    gastos_operativos = grupo("gasto_operativo")
    financiero_pos = resultado_df[
        (resultado_df["categoria"] == "financiero") & (resultado_df["tipo"] == "r_positivo")
    ][["codigo", "nombre", "saldo"]].to_dict("records")
    financiero_neg = resultado_df[
        (resultado_df["categoria"] == "financiero") & (resultado_df["tipo"] == "r_negativo")
    ][["codigo", "nombre", "saldo"]].to_dict("records")
    impuesto = grupo("impuesto")

    total_ingresos_venta = sum(r["saldo"] for r in ingresos_venta)
    total_costo_venta = sum(r["saldo"] for r in costos_venta)
    resultado_bruto = total_ingresos_venta - total_costo_venta

    total_otros_ingresos = sum(r["saldo"] for r in otros_ingresos)
    total_gastos_operativos = sum(r["saldo"] for r in gastos_operativos)
    resultado_operativo = resultado_bruto + total_otros_ingresos - total_gastos_operativos

    total_ing_fin = sum(r["saldo"] for r in financiero_pos)
    total_egr_fin = sum(r["saldo"] for r in financiero_neg)
    resultado_financiero = total_ing_fin - total_egr_fin

    resultado_antes_impuestos = resultado_operativo + resultado_financiero
    total_impuesto = sum(r["saldo"] for r in impuesto)
    resultado_neto = resultado_antes_impuestos - total_impuesto

    # legacy aggregate view (used by dashboard ratios / other pages if needed)
    total_i = df[df["tipo"] == "r_positivo"]["saldo"].sum()
    total_e = df[df["tipo"] == "r_negativo"]["saldo"].sum()

    return {
        "ingresos_venta": ingresos_venta,
        "total_ingresos_venta": total_ingresos_venta,
        "costos_venta": costos_venta,
        "total_costo_venta": total_costo_venta,
        "resultado_bruto": resultado_bruto,
        "otros_ingresos": otros_ingresos,
        "total_otros_ingresos": total_otros_ingresos,
        "gastos_operativos": gastos_operativos,
        "total_gastos_operativos": total_gastos_operativos,
        "resultado_operativo": resultado_operativo,
        "ingresos_financieros": financiero_pos,
        "total_ingresos_financieros": total_ing_fin,
        "egresos_financieros": financiero_neg,
        "total_egresos_financieros": total_egr_fin,
        "resultado_financiero": resultado_financiero,
        "resultado_antes_impuestos": resultado_antes_impuestos,
        "impuesto_ganancias": impuesto,
        "total_impuesto_ganancias": total_impuesto,
        "resultado_neto": resultado_neto,
        # legacy
        "ingresos": df[df["tipo"] == "r_positivo"][["codigo", "nombre", "saldo"]].to_dict("records"),
        "egresos": df[df["tipo"] == "r_negativo"][["codigo", "nombre", "saldo"]].to_dict("records"),
        "total_ingresos": total_i,
        "total_egresos": total_e,
    }


def get_estado_evolucion_patrimonio() -> dict:
    """
    Estado de Evolución del Patrimonio Neto.

    Agrupa las cuentas de patrimonio en sus componentes clásicos (Capital,
    Reservas, Resultados No Asignados) e incorpora el Resultado del Ejercicio
    calculado a partir de las cuentas de resultado (r_positivo / r_negativo),
    de forma que el total coincida exactamente con el Patrimonio Neto que
    figura en el Estado de Situación Patrimonial.
    """
    df = _saldos_df()
    if df.empty:
        return {
            "cuentas": [], "total": 0,
            "capital": [], "total_capital": 0,
            "reservas": [], "total_reservas": 0,
            "resultados_acumulados": [], "total_resultados_acumulados": 0,
            "resultado_ejercicio": 0,
        }

    pn_df = df[df["tipo"] == "patrimonio"].copy()
    pn = pn_df[["codigo", "nombre", "saldo"]].to_dict("records")

    def es_capital(codigo):
        return codigo.startswith("3.1")

    def es_reserva(codigo):
        return codigo.startswith("3.2")

    def es_resultado_acumulado(codigo):
        return codigo.startswith("3.3")

    capital = [r for r in pn if es_capital(r["codigo"])]
    reservas = [r for r in pn if es_reserva(r["codigo"])]
    resultados_acumulados = [r for r in pn if es_resultado_acumulado(r["codigo"])]
    otros = [
        r for r in pn
        if not es_capital(r["codigo"]) and not es_reserva(r["codigo"])
        and not es_resultado_acumulado(r["codigo"])
    ]

    resultado_ejercicio = (
        df[df["tipo"] == "r_positivo"]["saldo"].sum()
        - df[df["tipo"] == "r_negativo"]["saldo"].sum()
    )

    total_capital = sum(r["saldo"] for r in capital)
    total_reservas = sum(r["saldo"] for r in reservas)
    total_resultados_acumulados = sum(r["saldo"] for r in resultados_acumulados) + sum(
        r["saldo"] for r in otros
    )
    total = total_capital + total_reservas + total_resultados_acumulados + resultado_ejercicio

    return {
        "cuentas": pn,
        "total": total,
        "capital": capital,
        "total_capital": total_capital,
        "reservas": reservas,
        "total_reservas": total_reservas,
        "resultados_acumulados": resultados_acumulados + otros,
        "total_resultados_acumulados": total_resultados_acumulados,
        "resultado_ejercicio": resultado_ejercicio,
    }


def get_flujo_efectivo() -> dict:
    """
    Estado de Flujo de Efectivo por el método indirecto:

    Actividades Operativas
      Resultado neto del ejercicio
      (+) Ajustes por partidas sin movimiento de efectivo (amortizaciones)
      (+/-) Cambios en el capital de trabajo (activo/pasivo corriente, sin efectivo)
      = Flujo neto operativo

    Actividades de Inversión
      Variación de activos no corrientes "reales" (bienes de uso, inversiones)
      = Flujo neto de inversión

    Actividades de Financiación
      Variación de pasivos no corrientes (préstamos LP) y aportes de capital
      = Flujo neto de financiación

    Como el sistema no maneja saldos de apertura de un período anterior
    (arranca desde cero), la "variación" de cada cuenta coincide con su
    saldo actual, lo que permite reconstruir el flujo de fondos completo.
    """
    vacio = {
        "resultado_neto": 0.0,
        "ajustes": [], "total_ajustes": 0.0,
        "capital_trabajo": [], "total_capital_trabajo": 0.0,
        "total_op": 0.0,
        "inversion": [], "total_inv": 0.0,
        "financiacion": [], "total_fin": 0.0,
        "variacion_efectivo": 0.0,
        "efectivo_inicial": 0.0,
        "saldo_efectivo_cierre": 0.0,
        "diferencia_conciliacion": 0.0,
        # legacy keys
        "operativas": [], "total_operativas": 0.0,
    }

    saldos = get_saldos_por_cuenta()
    if not saldos:
        return vacio

    efectivo_nombres = {"caja", "banco", "caja chica"}
    amort_keywords = ("amort", "deprec")
    provision_keywords = ("previs", "provisi")

    er = get_estado_resultados()
    resultado_neto = er["resultado_neto"]

    # ── Ajustes por partidas sin movimiento de efectivo ─────────────────────
    ajustes = []
    for r in er["gastos_operativos"]:
        n = r["nombre"].lower()
        if any(k in n for k in amort_keywords) or any(k in n for k in provision_keywords):
            ajustes.append({"cuenta": r["nombre"], "monto": r["saldo"]})
    total_ajustes = sum(a["monto"] for a in ajustes)

    # ── Cambios en el capital de trabajo (activo/pasivo corriente, sin efectivo) ──
    capital_trabajo = []
    for d in saldos.values():
        nombre_lower = d["nombre"].lower()
        if any(e in nombre_lower for e in efectivo_nombres):
            continue
        if d["tipo"] == "activo" and d["subcategoria"] == "corriente":
            if abs(d["saldo"]) > 0.005:
                capital_trabajo.append({"cuenta": d["nombre"], "monto": -d["saldo"]})
        elif d["tipo"] == "pasivo" and d["subcategoria"] == "corriente":
            if abs(d["saldo"]) > 0.005:
                capital_trabajo.append({"cuenta": d["nombre"], "monto": d["saldo"]})
    total_capital_trabajo = sum(c["monto"] for c in capital_trabajo)

    total_op = resultado_neto + total_ajustes + total_capital_trabajo

    # ── Actividades de inversión: activo no corriente "real" ────────────────
    inversion = []
    for d in saldos.values():
        if d["tipo"] == "activo" and d["subcategoria"] == "no_corriente":
            nombre_lower = d["nombre"].lower()
            if any(k in nombre_lower for k in amort_keywords):
                continue  # ya reflejado como ajuste no-monetario arriba
            if abs(d["saldo"]) > 0.005:
                inversion.append({"cuenta": d["nombre"], "monto": -d["saldo"]})
    total_inv = sum(x["monto"] for x in inversion)

    # ── Actividades de financiación: pasivo no corriente + aportes de capital ──
    financiacion = []
    for d in saldos.values():
        if d["tipo"] == "pasivo" and d["subcategoria"] == "no_corriente":
            if abs(d["saldo"]) > 0.005:
                financiacion.append({"cuenta": d["nombre"], "monto": d["saldo"]})
        elif d["tipo"] == "patrimonio" and d["codigo"].startswith("3.1"):
            if abs(d["saldo"]) > 0.005:
                financiacion.append({"cuenta": d["nombre"], "monto": d["saldo"]})
    total_fin = sum(x["monto"] for x in financiacion)

    variacion_efectivo = total_op + total_inv + total_fin

    saldo_efectivo = sum(
        d["saldo"]
        for d in saldos.values()
        if any(e in d["nombre"].lower() for e in efectivo_nombres)
    )

    return {
        "resultado_neto": resultado_neto,
        "ajustes": ajustes,
        "total_ajustes": total_ajustes,
        "capital_trabajo": capital_trabajo,
        "total_capital_trabajo": total_capital_trabajo,
        "total_op": total_op,
        "inversion": inversion,
        "total_inv": total_inv,
        "financiacion": financiacion,
        "total_fin": total_fin,
        "variacion_efectivo": variacion_efectivo,
        "efectivo_inicial": 0.0,
        "saldo_efectivo_cierre": saldo_efectivo,
        "diferencia_conciliacion": saldo_efectivo - variacion_efectivo,
        # legacy keys (kept in case something else references them)
        "operativas": capital_trabajo,
        "total_operativas": total_op,
    }


# ─────────────────────────────────────────
# FINANCIAL RATIOS
# ─────────────────────────────────────────

def get_indicadores() -> dict:
    df = _saldos_df()
    if df.empty:
        return {}

    def total(tipo, sub=None):
        mask = df["tipo"] == tipo
        if sub:
            mask &= df["subcategoria"] == sub
        return df[mask]["saldo"].sum()

    activo_c = total("activo", "corriente")
    activo_nc = total("activo", "no_corriente")
    activo_total = activo_c + activo_nc

    pasivo_c = total("pasivo", "corriente")
    pasivo_nc = total("pasivo", "no_corriente")
    pasivo_total = pasivo_c + pasivo_nc

    ingresos = total("r_positivo")
    egresos = total("r_negativo")
    resultado = ingresos - egresos
    patrimonio = total("patrimonio") + resultado

    # Inventario estimate (mercaderías)
    inventario = df[
        (df["tipo"] == "activo") &
        (df["nombre"].str.lower().str.contains("merced|inventario|stock", na=False))
    ]["saldo"].sum()

    return {
        "activo_corriente": activo_c,
        "activo_no_corriente": activo_nc,
        "activo_total": activo_total,
        "pasivo_corriente": pasivo_c,
        "pasivo_no_corriente": pasivo_nc,
        "pasivo_total": pasivo_total,
        "patrimonio": patrimonio,
        "ingresos": ingresos,
        "egresos": egresos,
        "resultado": resultado,
        # Ratios
        "liquidez_corriente": activo_c / pasivo_c if pasivo_c else None,
        "liquidez_acida": (activo_c - inventario) / pasivo_c if pasivo_c else None,
        "solvencia": activo_total / pasivo_total if pasivo_total else None,
        "endeudamiento": pasivo_total / patrimonio if patrimonio else None,
        "rentabilidad": resultado / activo_total * 100 if activo_total else None,
        "margen_neto": resultado / ingresos * 100 if ingresos else None,
    }


# ─────────────────────────────────────────
# EXPORT TO EXCEL
# ─────────────────────────────────────────

def export_estados_excel(buffer):
    """Write all financial statements to an Excel workbook."""
    bg = get_balance_general()
    er = get_estado_resultados()
    ep = get_estado_evolucion_patrimonio()
    fe = get_flujo_efectivo()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Balance General
        rows_bg = []
        rows_bg.append({"Sección": "ACTIVO CORRIENTE", "Cuenta": "", "Monto": ""})
        for r in bg["activo_corriente"]:
            rows_bg.append({"Sección": "", "Cuenta": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_bg.append({"Sección": "ACTIVO NO CORRIENTE", "Cuenta": "", "Monto": ""})
        for r in bg["activo_no_corriente"]:
            rows_bg.append({"Sección": "", "Cuenta": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_bg.append({"Sección": "TOTAL ACTIVO", "Cuenta": "", "Monto": bg["total_activo"]})
        rows_bg.append({"Sección": "", "Cuenta": "", "Monto": ""})
        rows_bg.append({"Sección": "PASIVO CORRIENTE", "Cuenta": "", "Monto": ""})
        for r in bg["pasivo_corriente"]:
            rows_bg.append({"Sección": "", "Cuenta": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_bg.append({"Sección": "PASIVO NO CORRIENTE", "Cuenta": "", "Monto": ""})
        for r in bg["pasivo_no_corriente"]:
            rows_bg.append({"Sección": "", "Cuenta": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_bg.append({"Sección": "TOTAL PASIVO", "Cuenta": "", "Monto": bg["total_pasivo"]})
        rows_bg.append({"Sección": "PATRIMONIO NETO", "Cuenta": "", "Monto": ""})
        for r in bg["patrimonio"]:
            rows_bg.append({"Sección": "", "Cuenta": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_bg.append({"Sección": "TOTAL PATRIMONIO NETO", "Cuenta": "", "Monto": bg["total_patrimonio"]})
        pd.DataFrame(rows_bg).to_excel(writer, sheet_name="Balance General", index=False)

        # Estado de Resultados
        rows_er = []
        rows_er.append({"Concepto": "INGRESOS POR VENTAS", "Monto": ""})
        for r in er["ingresos_venta"]:
            rows_er.append({"Concepto": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_er.append({"Concepto": "(-) Costo de Ventas", "Monto": ""})
        for r in er["costos_venta"]:
            rows_er.append({"Concepto": f"{r['codigo']} - {r['nombre']}", "Monto": -r["saldo"]})
        rows_er.append({"Concepto": "RESULTADO BRUTO", "Monto": er["resultado_bruto"]})
        rows_er.append({"Concepto": "(+) Otros Ingresos Operativos", "Monto": ""})
        for r in er["otros_ingresos"]:
            rows_er.append({"Concepto": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_er.append({"Concepto": "(-) Gastos Operativos", "Monto": ""})
        for r in er["gastos_operativos"]:
            rows_er.append({"Concepto": f"{r['codigo']} - {r['nombre']}", "Monto": -r["saldo"]})
        rows_er.append({"Concepto": "RESULTADO OPERATIVO", "Monto": er["resultado_operativo"]})
        rows_er.append({"Concepto": "(+) Ingresos Financieros", "Monto": ""})
        for r in er["ingresos_financieros"]:
            rows_er.append({"Concepto": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_er.append({"Concepto": "(-) Egresos Financieros", "Monto": ""})
        for r in er["egresos_financieros"]:
            rows_er.append({"Concepto": f"{r['codigo']} - {r['nombre']}", "Monto": -r["saldo"]})
        rows_er.append({"Concepto": "RESULTADO ANTES DE IMPUESTOS", "Monto": er["resultado_antes_impuestos"]})
        rows_er.append({"Concepto": "(-) Impuesto a las Ganancias", "Monto": -er["total_impuesto_ganancias"]})
        rows_er.append({"Concepto": "RESULTADO NETO DEL EJERCICIO", "Monto": er["resultado_neto"]})
        pd.DataFrame(rows_er).to_excel(writer, sheet_name="Estado de Resultados", index=False)

        # Evolución Patrimonio
        rows_ep = []
        rows_ep.append({"Componente": "CAPITAL", "Monto": ""})
        for r in ep["capital"]:
            rows_ep.append({"Componente": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_ep.append({"Componente": "RESERVAS", "Monto": ""})
        for r in ep["reservas"]:
            rows_ep.append({"Componente": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_ep.append({"Componente": "RESULTADOS ACUMULADOS", "Monto": ""})
        for r in ep["resultados_acumulados"]:
            rows_ep.append({"Componente": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_ep.append({"Componente": "Resultado del Ejercicio", "Monto": ep["resultado_ejercicio"]})
        rows_ep.append({"Componente": "PATRIMONIO NETO TOTAL", "Monto": ep["total"]})
        pd.DataFrame(rows_ep).to_excel(writer, sheet_name="Evolución Patrimonio", index=False)

        # Flujo de Efectivo
        rows_fe = []
        rows_fe.append({"Actividad": "ACTIVIDADES OPERATIVAS", "Monto": ""})
        rows_fe.append({"Actividad": "Resultado neto del ejercicio", "Monto": fe["resultado_neto"]})
        rows_fe.append({"Actividad": "Ajustes sin movimiento de efectivo", "Monto": ""})
        for r in fe["ajustes"]:
            rows_fe.append({"Actividad": r["cuenta"], "Monto": r["monto"]})
        rows_fe.append({"Actividad": "Cambios en el capital de trabajo", "Monto": ""})
        for r in fe["capital_trabajo"]:
            rows_fe.append({"Actividad": r["cuenta"], "Monto": r["monto"]})
        rows_fe.append({"Actividad": "Flujo neto operativo", "Monto": fe["total_op"]})
        rows_fe.append({"Actividad": "ACTIVIDADES DE INVERSIÓN", "Monto": ""})
        for r in fe["inversion"]:
            rows_fe.append({"Actividad": r["cuenta"], "Monto": r["monto"]})
        rows_fe.append({"Actividad": "Flujo neto de inversión", "Monto": fe["total_inv"]})
        rows_fe.append({"Actividad": "ACTIVIDADES DE FINANCIACIÓN", "Monto": ""})
        for r in fe["financiacion"]:
            rows_fe.append({"Actividad": r["cuenta"], "Monto": r["monto"]})
        rows_fe.append({"Actividad": "Flujo neto de financiación", "Monto": fe["total_fin"]})
        rows_fe.append({"Actividad": "AUMENTO NETO DE EFECTIVO", "Monto": fe["variacion_efectivo"]})
        rows_fe.append({"Actividad": "Efectivo al inicio del período", "Monto": fe["efectivo_inicial"]})
        rows_fe.append({"Actividad": "EFECTIVO AL FINAL DEL PERÍODO", "Monto": fe["saldo_efectivo_cierre"]})
        pd.DataFrame(rows_fe).to_excel(writer, sheet_name="Flujo de Efectivo", index=False)
