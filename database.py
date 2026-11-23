"""Capa de persistencia SQLite para VSE ALIMENTA."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "vse_alimenta.db"
LIMA_TZ = ZoneInfo("America/Lima")


def now_local() -> datetime:
    """Hora local de Lima, guardada como fecha/hora sin zona para facilitar SQLite."""
    return datetime.now(LIMA_TZ).replace(tzinfo=None, second=0, microsecond=0)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_name TEXT NOT NULL,
                donor_phone TEXT DEFAULT '',
                food_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity_kg REAL NOT NULL CHECK(quantity_kg > 0),
                area TEXT NOT NULL,
                pickup_address TEXT NOT NULL,
                available_until TEXT NOT NULL,
                notes TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Disponible',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS needs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kitchen_name TEXT NOT NULL,
                contact_name TEXT NOT NULL,
                phone TEXT DEFAULT '',
                food_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity_kg REAL NOT NULL CHECK(quantity_kg > 0),
                area TEXT NOT NULL,
                address TEXT NOT NULL,
                needed_until TEXT NOT NULL,
                notes TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Activa',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donation_id INTEGER NOT NULL,
                need_id INTEGER NOT NULL,
                quantity_kg REAL NOT NULL CHECK(quantity_kg > 0),
                status TEXT NOT NULL DEFAULT 'Reservada',
                created_at TEXT NOT NULL,
                delivered_at TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                FOREIGN KEY(donation_id) REFERENCES donations(id),
                FOREIGN KEY(need_id) REFERENCES needs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);
            CREATE INDEX IF NOT EXISTS idx_needs_status ON needs(status);
            CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);
            """
        )
        donation_count = conn.execute("SELECT COUNT(*) FROM donations").fetchone()[0]
        need_count = conn.execute("SELECT COUNT(*) FROM needs").fetchone()[0]
        if donation_count == 0 and need_count == 0:
            _insert_demo_data(conn)


def _insert_demo_data(conn: sqlite3.Connection) -> None:
    now = now_local()
    donations = [
        (
            "Mercado Vecinal 1", "900111222", "Verduras mixtas", "Verduras", 15.0,
            "Sector 2", "Puesto de recepción (dirección de demostración)",
            (now + timedelta(hours=7)).isoformat(sep=" ", timespec="minutes"),
            "Ejemplo académico. Revisar estado y conservación antes de aceptar.", "Disponible", now.isoformat(sep=" ", timespec="minutes"),
        ),
        (
            "Bodega Solidaria", "900333444", "Arroz", "Granos y cereales", 20.0,
            "Sector 3", "Local de demostración, Villa El Salvador",
            (now + timedelta(hours=20)).isoformat(sep=" ", timespec="minutes"),
            "Paquetes cerrados de ejemplo.", "Disponible", now.isoformat(sep=" ", timespec="minutes"),
        ),
        (
            "Frutería del Barrio", "900555666", "Plátano", "Frutas", 10.0,
            "Sector 2", "Punto de recojo de demostración",
            (now + timedelta(hours=4)).isoformat(sep=" ", timespec="minutes"),
            "Ejemplo académico; revisar madurez y estado.", "Disponible", now.isoformat(sep=" ", timespec="minutes"),
        ),
    ]
    needs = [
        (
            "Comedor Esperanza", "Rosa Quispe", "901111222", "Verduras mixtas", "Verduras", 12.0,
            "Sector 2", "Ubicación de demostración - Villa El Salvador",
            (now + timedelta(hours=6)).isoformat(sep=" ", timespec="minutes"),
            "Necesidad de ejemplo para la demostración.", "Activa", now.isoformat(sep=" ", timespec="minutes"),
        ),
        (
            "Comedor Nueva Vida", "Luis Pérez", "901333444", "Arroz", "Granos y cereales", 15.0,
            "Sector 3", "Ubicación de demostración - Villa El Salvador",
            (now + timedelta(hours=18)).isoformat(sep=" ", timespec="minutes"),
            "Necesidad de ejemplo para la demostración.", "Activa", now.isoformat(sep=" ", timespec="minutes"),
        ),
        (
            "Comedor Luz", "Ana Rojas", "901555666", "Plátano", "Frutas", 8.0,
            "Sector 2", "Ubicación de demostración - Villa El Salvador",
            (now + timedelta(hours=3)).isoformat(sep=" ", timespec="minutes"),
            "Necesidad de ejemplo para la demostración.", "Activa", now.isoformat(sep=" ", timespec="minutes"),
        ),
    ]
    conn.executemany(
        """INSERT INTO donations
        (donor_name, donor_phone, food_name, category, quantity_kg, area, pickup_address,
         available_until, notes, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        donations,
    )
    conn.executemany(
        """INSERT INTO needs
        (kitchen_name, contact_name, phone, food_name, category, quantity_kg, area, address,
         needed_until, notes, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        needs,
    )


def reset_demo_data() -> None:
    """Borra los datos del prototipo y vuelve a cargar ejemplos ficticios."""
    with get_connection() as conn:
        conn.execute("DELETE FROM reservations")
        conn.execute("DELETE FROM donations")
        conn.execute("DELETE FROM needs")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('donations','needs','reservations')")
        _insert_demo_data(conn)


def add_donation(data: dict[str, Any]) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO donations
            (donor_name, donor_phone, food_name, category, quantity_kg, area, pickup_address,
             available_until, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Disponible', ?)""",
            (
                data["donor_name"].strip(), data.get("donor_phone", "").strip(),
                data["food_name"].strip(), data["category"], float(data["quantity_kg"]),
                data["area"].strip(), data["pickup_address"].strip(), data["available_until"],
                data.get("notes", "").strip(), now_local().isoformat(sep=" ", timespec="minutes"),
            ),
        )
        return int(cur.lastrowid)


def add_need(data: dict[str, Any]) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO needs
            (kitchen_name, contact_name, phone, food_name, category, quantity_kg, area, address,
             needed_until, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Activa', ?)""",
            (
                data["kitchen_name"].strip(), data["contact_name"].strip(), data.get("phone", "").strip(),
                data["food_name"].strip(), data["category"], float(data["quantity_kg"]),
                data["area"].strip(), data["address"].strip(), data["needed_until"],
                data.get("notes", "").strip(), now_local().isoformat(sep=" ", timespec="minutes"),
            ),
        )
        return int(cur.lastrowid)


def _remaining_quantity(conn: sqlite3.Connection, table: str, record_id: int, total: float) -> float:
    if table == "donations":
        field = "donation_id"
    elif table == "needs":
        field = "need_id"
    else:
        raise ValueError("Tabla no permitida")
    used = conn.execute(
        f"SELECT COALESCE(SUM(quantity_kg), 0) FROM reservations WHERE {field} = ? AND status IN ('Reservada','Entregada')",
        (record_id,),
    ).fetchone()[0]
    return max(0.0, round(float(total) - float(used), 2))


def list_donations() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM donations ORDER BY created_at DESC, id DESC").fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["remaining_kg"] = _remaining_quantity(conn, "donations", item["id"], item["quantity_kg"])
            result.append(item)
        return result


def list_needs() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM needs ORDER BY created_at DESC, id DESC").fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["remaining_kg"] = _remaining_quantity(conn, "needs", item["id"], item["quantity_kg"])
            result.append(item)
        return result


def create_reservation(donation_id: int, need_id: int, quantity_kg: float) -> int:
    """Reserva kilos disponibles de una donación para una necesidad."""
    qty = round(float(quantity_kg), 2)
    if qty <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        donation = conn.execute("SELECT * FROM donations WHERE id = ?", (donation_id,)).fetchone()
        need = conn.execute("SELECT * FROM needs WHERE id = ?", (need_id,)).fetchone()
        if donation is None or need is None:
            raise ValueError("No se encontró la donación o la necesidad seleccionada.")
        if donation["status"] != "Disponible" or need["status"] != "Activa":
            raise ValueError("La donación o la necesidad ya no están activas.")
        now = now_local()
        if datetime.fromisoformat(donation["available_until"]) < now:
            raise ValueError("El plazo de recojo de esta donación ya venció.")
        if datetime.fromisoformat(need["needed_until"]) < now:
            raise ValueError("El plazo de esta necesidad ya venció.")

        donation_left = _remaining_quantity(conn, "donations", donation_id, donation["quantity_kg"])
        need_left = _remaining_quantity(conn, "needs", need_id, need["quantity_kg"])
        if qty > donation_left + 0.0001:
            raise ValueError(f"Solo quedan {donation_left:.2f} kg disponibles de esta donación.")
        if qty > need_left + 0.0001:
            raise ValueError(f"El comedor todavía necesita {need_left:.2f} kg.")

        cur = conn.execute(
            """INSERT INTO reservations (donation_id, need_id, quantity_kg, status, created_at)
            VALUES (?, ?, ?, 'Reservada', ?)""",
            (donation_id, need_id, qty, now.isoformat(sep=" ", timespec="minutes")),
        )
        conn.commit()
        return int(cur.lastrowid)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_delivered(reservation_id: int) -> None:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE reservations SET status = 'Entregada', delivered_at = ? WHERE id = ? AND status = 'Reservada'",
            (now_local().isoformat(sep=" ", timespec="minutes"), reservation_id),
        )
        if cur.rowcount == 0:
            raise ValueError("No se pudo confirmar: la reserva no está pendiente.")


def cancel_reservation(reservation_id: int) -> None:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE reservations SET status = 'Cancelada' WHERE id = ? AND status = 'Reservada'",
            (reservation_id,),
        )
        if cur.rowcount == 0:
            raise ValueError("No se pudo cancelar: la reserva no está pendiente.")


def list_reservations(status: str | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT r.*, d.food_name, d.donor_name, d.area AS donor_area, d.pickup_address,
               n.kitchen_name, n.contact_name, n.area AS kitchen_area, n.address AS kitchen_address
        FROM reservations r
        JOIN donations d ON d.id = r.donation_id
        JOIN needs n ON n.id = r.need_id
    """
    params: tuple[Any, ...] = ()
    if status:
        query += " WHERE r.status = ?"
        params = (status,)
    query += " ORDER BY r.created_at DESC, r.id DESC"
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def dashboard_stats() -> dict[str, Any]:
    with get_connection() as conn:
        donated = conn.execute("SELECT COALESCE(SUM(quantity_kg), 0) FROM donations").fetchone()[0]
        available = 0.0
        donations = conn.execute("SELECT * FROM donations WHERE status = 'Disponible'").fetchall()
        for row in donations:
            if datetime.fromisoformat(row["available_until"]) >= now_local():
                available += _remaining_quantity(conn, "donations", row["id"], row["quantity_kg"])
        delivered = conn.execute("SELECT COALESCE(SUM(quantity_kg), 0) FROM reservations WHERE status = 'Entregada'").fetchone()[0]
        active_reservations = conn.execute("SELECT COUNT(*) FROM reservations WHERE status = 'Reservada'").fetchone()[0]
        delivered_kitchens = conn.execute(
            """SELECT COUNT(DISTINCT n.kitchen_name)
               FROM reservations r JOIN needs n ON n.id = r.need_id
               WHERE r.status = 'Entregada'"""
        ).fetchone()[0]
        active_needs = conn.execute("SELECT COUNT(*) FROM needs WHERE status = 'Activa'").fetchone()[0]
        return {
            "total_registered_kg": round(float(donated), 2),
            "available_kg": round(float(available), 2),
            "delivered_kg": round(float(delivered), 2),
            "active_reservations": int(active_reservations),
            "delivered_kitchens": int(delivered_kitchens),
            "active_needs": int(active_needs),
        }
