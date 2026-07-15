"""
Database initialization and core operations for the accounting app.
Uses SQLite with sqlite3 standard library.
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "contabilidad.db"


def get_connection():
    """Return a new database connection with row_factory set."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist and seed default accounts."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,            -- activo | pasivo | patrimonio | r_positivo | r_negativo
            subcategoria TEXT,             -- corriente | no_corriente | NULL
            descripcion TEXT,
            es_default INTEGER DEFAULT 0,
            activa INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS asientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER NOT NULL UNIQUE,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            creado_en TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS lineas_asiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asiento_id INTEGER NOT NULL REFERENCES asientos(id) ON DELETE CASCADE,
            cuenta_id INTEGER NOT NULL REFERENCES cuentas(id),
            debe REAL DEFAULT 0,
            haber REAL DEFAULT 0,
            descripcion TEXT
        );
    """)

    conn.commit()
    _seed_cuentas(conn)
    conn.close()


def _seed_cuentas(conn):
    """Insert default chart of accounts if table is empty."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cuentas WHERE es_default = 1")
    if cur.fetchone()[0] > 0:
        return

    cuentas_default = [
        # ACTIVOS CORRIENTES
        ("1.1.01", "Caja", "activo", "corriente", "Dinero en efectivo disponible"),
        ("1.1.02", "Banco", "activo", "corriente", "Depósitos bancarios a la vista"),
        ("1.1.03", "Clientes / Cuentas por Cobrar", "activo", "corriente", "Derechos de cobro por ventas"),
        ("1.1.04", "Documentos por Cobrar", "activo", "corriente", "Pagarés y letras a favor"),
        ("1.1.05", "Mercaderías / Inventario", "activo", "corriente", "Stock de bienes para la venta"),
        ("1.1.06", "Materias Primas", "activo", "corriente", "Insumos para producción"),
        ("1.1.07", "IVA Crédito Fiscal", "activo", "corriente", "IVA pagado en compras"),    
        ("1.1.08", "Inversiones Temporarias", "activo", "corriente", "Depósitos a plazo fijo corto"),
        # ACTIVOS NO CORRIENTES
        ("1.2.01", "Muebles y Útiles", "activo", "no_corriente", "Mobiliario de oficina"),
        ("1.2.02", "Equipos de Computación", "activo", "no_corriente", "Hardware y equipos tecnológicos"),
        ("1.2.03", "Maquinarias y Equipos", "activo", "no_corriente", "Equipos de producción"),
        ("1.2.04", "Rodados / Vehículos", "activo", "no_corriente", "Automóviles y camiones"),
        ("1.2.05", "Inmuebles / Terrenos", "activo", "no_corriente", "Propiedades y terrenos"),
        ("1.2.06", "Amort. Acum. Muebles y Útiles", "activo", "no_corriente", "Depreciación acumulada muebles"),
        ("1.2.07", "Amort. Acum. Equipos Computación", "activo", "no_corriente", "Depreciación acumulada equipos"),
        ("1.2.08", "Amort. Acum. Maquinarias", "activo", "no_corriente", "Depreciación acumulada maquinarias"),
        ("1.2.09", "Amort. Acum. Rodados", "activo", "no_corriente", "Depreciación acumulada vehículos"),
        ("1.2.10", "Inversiones Permanentes", "activo", "no_corriente", "Participaciones en otras empresas"),
        ("1.2.11", "Marcas y Patentes", "activo", "no_corriente", "Activos intangibles registrados"),
        # PASIVOS CORRIENTES
        ("2.1.01", "Proveedores / Cuentas por Pagar", "pasivo", "corriente", "Deudas con proveedores"),
        ("2.1.02", "Documentos por Pagar", "pasivo", "corriente", "Pagarés y letras emitidos"),
        ("2.1.03", "Sueldos y Jornales a Pagar", "pasivo", "corriente", "Remuneraciones devengadas"),
        ("2.1.04", "Cargas Sociales a Pagar", "pasivo", "corriente", "Contribuciones patronales pendientes"),
        ("2.1.05", "IVA Débito Fiscal", "pasivo", "corriente", "IVA recaudado en ventas"),
        ("2.1.06", "Impuestos a Pagar", "pasivo", "corriente", "Impuestos devengados pendientes"),
        ("2.1.07", "Anticipos de Clientes", "pasivo", "corriente", "Cobros recibidos por anticipado"),
        ("2.1.08", "Préstamos Bancarios CP", "pasivo", "corriente", "Deuda bancaria corto plazo"),
        ("2.1.09", "Dividendos a Pagar", "pasivo", "corriente", "Dividendos declarados pendientes"),
        ("2.1.10", "Arriendos a Pagar", "pasivo", "corriente", "Alquileres devengados pendientes"),
        # PASIVOS NO CORRIENTES
        ("2.2.01", "Préstamos Bancarios LP", "pasivo", "no_corriente", "Deuda bancaria largo plazo"),
        ("2.2.02", "Hipotecas a Pagar", "pasivo", "no_corriente", "Préstamos hipotecarios"),
        ("2.2.03", "Obligaciones Negociables", "pasivo", "no_corriente", "Deuda emitida al mercado"),
        ("2.2.04", "Previsión para Indemnizaciones", "pasivo", "no_corriente", "Provisión para despidos"),
        # PATRIMONIO NETO
        ("3.1.01", "Capital Social", "patrimonio", None, "Aporte de los accionistas / socios"),
        ("3.1.02", "Acciones en Circulación", "patrimonio", None, "Capital suscripto y pagado"),
        ("3.1.03", "Acciones a Emitir en Dividendos", "patrimonio", None, "Dividendos en acciones declarados"),
        ("3.2.01", "Reserva Legal", "patrimonio", None, "Reserva obligatoria por ley"),
        ("3.2.02", "Reserva Facultativa", "patrimonio", None, "Reserva por decisión societaria"),
        ("3.3.01", "Resultados No Asignados", "patrimonio", None, "Utilidades retenidas acumuladas"),
        ("3.3.02", "Resultado del Ejercicio", "patrimonio", None, "Ganancia o pérdida del período"),
        # INGRESOS / RESULTADOS POSITIVOS
        ("4.1.01", "Ventas", "r_positivo", None, "Ingresos por venta de bienes"),
        ("4.1.02", "Ventas de Servicios", "r_positivo", None, "Ingresos por prestación de servicios"),
        ("4.1.03", "Intereses Ganados", "r_positivo", None, "Rendimientos financieros obtenidos"),
        ("4.1.04", "Descuentos Obtenidos", "r_positivo", None, "Descuentos recibidos de proveedores"),
        ("4.1.05", "Alquileres Ganados", "r_positivo", None, "Ingresos por arrendamientos"),
        ("4.1.06", "Diferencia de Cambio Favorable", "r_positivo", None, "Ganancia por tipo de cambio"),
        ("4.1.07", "Otros Ingresos", "r_positivo", None, "Ingresos no operativos varios"),
        # EGRESOS / RESULTADOS NEGATIVOS
        ("5.1.01", "Costo de Mercaderías Vendidas", "r_negativo", None, "Costo de los bienes vendidos"),
        ("5.1.02", "Sueldos y Jornales", "r_negativo", None, "Remuneraciones del personal"),
        ("5.1.03", "Cargas Sociales", "r_negativo", None, "Contribuciones patronales"),
        ("5.1.04", "Alquileres Pagados", "r_negativo", None, "Gastos de arrendamiento"),
        ("5.1.05", "Servicios Públicos", "r_negativo", None, "Luz, gas, agua, internet"),
        ("5.1.06", "Gastos de Mantenimiento", "r_negativo", None, "Reparaciones y mantenimiento"),
        ("5.1.07", "Amortizaciones / Depreciaciones", "r_negativo", None, "Desgaste de bienes de uso"),
        ("5.1.08", "Intereses Perdidos", "r_negativo", None, "Gastos financieros por deudas"),
        ("5.1.09", "Descuentos Concedidos", "r_negativo", None, "Descuentos otorgados a clientes"),
        ("5.1.10", "Impuesto a las Ganancias", "r_negativo", None, "Cargo por impuesto a la renta"),
        ("5.1.11", "Gastos de Papelería y Útiles", "r_negativo", None, "Materiales de oficina consumidos"),
        ("5.1.12", "Publicidad y Propaganda", "r_negativo", None, "Gastos de marketing"),
        ("5.1.13", "Diferencia de Cambio Desfavorable", "r_negativo", None, "Pérdida por tipo de cambio"),
        ("5.1.14", "Devoluciones y Descuentos s/Ventas", "r_negativo", None, "Rebajas otorgadas sobre ventas"),
        ("5.1.15", "Otros Gastos", "r_negativo", None, "Gastos operativos varios"),
    ]

    cur.executemany(
        """INSERT OR IGNORE INTO cuentas
           (codigo, nombre, tipo, subcategoria, descripcion, es_default)
           VALUES (?, ?, ?, ?, ?, 1)""",
        cuentas_default,
    )
    conn.commit()


def reset_db():
    """Drop all data (but keep schema) and re-seed default accounts."""
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
        DELETE FROM lineas_asiento;
        DELETE FROM asientos;
        DELETE FROM cuentas;
        DELETE FROM sqlite_sequence WHERE name IN
            ('lineas_asiento','asientos','cuentas');
    """)
    conn.commit()
    _seed_cuentas(conn)
    conn.close()
