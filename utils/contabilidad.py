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
    total_patrimonio = df[df["tipo"] == "patrimonio"]["saldo"].sum()
    resultado = (
        df[df["tipo"] == "r_positivo"]["saldo"].sum()
        - df[df["tipo"] == "r_negativo"]["saldo"].sum()
    )

    total_patrimonio += resultado

    return {
        "activo_corriente": rows("activo", "corriente"),
        "activo_no_corriente": rows("activo", "no_corriente"),
        "pasivo_corriente": rows("pasivo", "corriente"),
        "pasivo_no_corriente": rows("pasivo", "no_corriente"),
        "patrimonio": rows("patrimonio"),
        "resultado_detalle": resultado,
        "total_activo": total_activo,
        "total_pasivo": total_pasivo,
        "total_patrimonio": total_patrimonio,
        "total_pasivo_patrimonio": total_pasivo + total_patrimonio,
    }


def get_estado_resultados() -> dict:
    """Estado de Resultados (PyG)."""
    df = _saldos_df()
    if df.empty:
        return {"ingresos": [], "egresos": [], "total_ingresos": 0,
                "total_egresos": 0, "resultado_neto": 0}

    ingresos = df[df["tipo"] == "r_positivo"][["codigo", "nombre", "saldo"]].to_dict("records")
    egresos = df[df["tipo"] == "r_negativo"][["codigo", "nombre", "saldo"]].to_dict("records")

    total_i = sum(r["saldo"] for r in ingresos)
    total_e = sum(r["saldo"] for r in egresos)
    resultado = total_i - total_e

    return {
        "ingresos": ingresos,
        "egresos": egresos,
        "total_ingresos": total_i,
        "total_egresos": total_e,
        "resultado_neto": resultado,
    }


def get_estado_evolucion_patrimonio() -> dict:
    """Estado de Evolución del Patrimonio Neto."""
    df = _saldos_df()
    if df.empty:
        return {"cuentas": [], "total": 0}

    pn = df[df["tipo"] == "patrimonio"][["codigo", "nombre", "saldo"]].to_dict("records")
    total = sum(r["saldo"] for r in pn)
    return {"cuentas": pn, "total": total}


def get_flujo_efectivo() -> dict:
    """
    Simplified direct-method cash flow statement.
    Classifies by account type and name heuristics.
    """
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT c.nombre, c.tipo, c.subcategoria,
               l.debe, l.haber
        FROM lineas_asiento l
        JOIN cuentas c ON c.id = l.cuenta_id
        """,
        conn,
    )
    conn.close()

    if df.empty:
        return {
            "operativas": [], 
            "inversion": [], 
            "financiacion": [],
            "total_op": 0.0, 
            "total_inv": 0.0, 
            "total_fin": 0.0,
            "variacion_efectivo": 0.0,
            "saldo_efectivo_cierre": 0.0,  
        }

    # Effective cash accounts
    efectivo_nombres = {"caja", "banco", "caja chica"}

    operativas, inversion, financiacion = [], [], []

    conn2 = get_connection()
    asientos = get_all_asientos()
    conn2.close()

    for a in asientos:
        for l in a["lineas"]:
            nombre_lower = (l["nombre"] or "").lower()
            tipo = l["tipo"]
            sub = l.get("subcategoria") or ""
            neto = l["debe"] - l["haber"]  # positive = cash in, negative = cash out

            if any(e in nombre_lower for e in efectivo_nombres):
                # This line IS the cash movement — skip, we track the other side
                continue

            if tipo in ("r_positivo", "r_negativo"):
                operativas.append({"cuenta": l["nombre"], "monto": -neto})
            elif tipo == "activo" and sub == "no_corriente":
                inversion.append({"cuenta": l["nombre"], "monto": -neto})
            elif tipo == "pasivo" and sub == "no_corriente":
                financiacion.append({"cuenta": l["nombre"], "monto": -neto})
            elif tipo == "patrimonio":
                financiacion.append({"cuenta": l["nombre"], "monto": -neto})

    total_op = sum(x["monto"] for x in operativas)
    total_inv = sum(x["monto"] for x in inversion)
    total_fin = sum(x["monto"] for x in financiacion)

    # Saldo efectivo from ledger
    saldos = get_saldos_por_cuenta()
    saldo_efectivo = sum(
        d["saldo"]
        for d in saldos.values()
        if any(e in d["nombre"].lower() for e in efectivo_nombres)
    )

    return {
        "operativas": operativas,
        "inversion": inversion,
        "financiacion": financiacion,
        "total_op": total_op,
        "total_inv": total_inv,
        "total_fin": total_fin,
        "variacion_efectivo": total_op + total_inv + total_fin,
        "saldo_efectivo_cierre": saldo_efectivo,
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

    patrimonio = total("patrimonio")
    ingresos = total("r_positivo")
    egresos = total("r_negativo")
    resultado = ingresos - egresos

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
        rows_er.append({"Sección": "INGRESOS", "Cuenta": "", "Monto": ""})
        for r in er["ingresos"]:
            rows_er.append({"Sección": "", "Cuenta": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_er.append({"Sección": "Total Ingresos", "Cuenta": "", "Monto": er["total_ingresos"]})
        rows_er.append({"Sección": "EGRESOS", "Cuenta": "", "Monto": ""})
        for r in er["egresos"]:
            rows_er.append({"Sección": "", "Cuenta": f"{r['codigo']} - {r['nombre']}", "Monto": r["saldo"]})
        rows_er.append({"Sección": "Total Egresos", "Cuenta": "", "Monto": er["total_egresos"]})
        rows_er.append({"Sección": "RESULTADO NETO", "Cuenta": "", "Monto": er["resultado_neto"]})
        pd.DataFrame(rows_er).to_excel(writer, sheet_name="Estado de Resultados", index=False)

        # Evolución Patrimonio
        pd.DataFrame(ep["cuentas"]).rename(
            columns={"codigo": "Código", "nombre": "Cuenta", "saldo": "Saldo"}
        ).to_excel(writer, sheet_name="Evolución Patrimonio", index=False)

        # Flujo de Efectivo
        rows_fe = []
        rows_fe.append({"Actividad": "ACTIVIDADES OPERATIVAS", "Cuenta": "", "Monto": ""})
        for r in fe["operativas"]:
            rows_fe.append({"Actividad": "", "Cuenta": r["cuenta"], "Monto": r["monto"]})
        rows_fe.append({"Actividad": "Total Operativas", "Cuenta": "", "Monto": fe["total_op"]})
        rows_fe.append({"Actividad": "ACTIVIDADES DE INVERSIÓN", "Cuenta": "", "Monto": ""})
        for r in fe["inversion"]:
            rows_fe.append({"Actividad": "", "Cuenta": r["cuenta"], "Monto": r["monto"]})
        rows_fe.append({"Actividad": "Total Inversión", "Cuenta": "", "Monto": fe["total_inv"]})
        rows_fe.append({"Actividad": "ACTIVIDADES DE FINANCIACIÓN", "Cuenta": "", "Monto": ""})
        for r in fe["financiacion"]:
            rows_fe.append({"Actividad": "", "Cuenta": r["cuenta"], "Monto": r["monto"]})
        rows_fe.append({"Actividad": "Total Financiación", "Cuenta": "", "Monto": fe["total_fin"]})
        rows_fe.append({"Actividad": "VARIACIÓN NETA DE EFECTIVO", "Cuenta": "", "Monto": fe["variacion_efectivo"]})
        pd.DataFrame(rows_fe).to_excel(writer, sheet_name="Flujo de Efectivo", index=False)
