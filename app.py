"""VSE ALIMENTA - prototipo web adaptable a móviles para HackODS UA 2026."""
from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from database import (
    add_donation,
    add_need,
    cancel_reservation,
    create_reservation,
    dashboard_stats,
    init_db,
    list_donations,
    list_needs,
    list_reservations,
    mark_delivered,
    now_local,
    reset_demo_data,
)
from matching import build_matches


CATEGORIES = [
    "Granos y cereales",
    "Verduras",
    "Frutas",
    "Proteínas",
    "Lácteos",
    "Enlatados y conservas",
    "Otros",
]
PAGES = [
    "Panel principal",
    "Registrar donación",
    "Registrar necesidad",
    "Emparejar y reservar",
    "Entregas",
    "Registros",
]

st.set_page_config(
    page_title="VSE ALIMENTA | HackODS UA 2026",
    page_icon="🥕",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { --brand: #177b58; --brand-dark: #105a42; --soft: #eaf5ef; }
      .stApp { background: #f7faf8; }
      [data-testid="stHeader"] { background: rgba(247,250,248,.92); }
      .block-container { max-width: 1180px; padding-top: 1.35rem; padding-bottom: 2.4rem; }
      [data-testid="stSidebar"] { background: #eff6f1; }
      .brand-title { color: #145c43; font-size: 1.52rem; font-weight: 800; letter-spacing: -.03em; }
      .brand-subtitle { color: #557367; font-size: .82rem; margin-top: -.3rem; }
      .hero { background: linear-gradient(115deg,#155d44 0%,#21865f 100%); color: white; padding: 1.35rem 1.5rem; border-radius: 18px; margin-bottom: 1rem; }
      .hero h1 { color: white; margin: 0 0 .35rem 0; font-size: clamp(1.5rem,3vw,2.15rem); }
      .hero p { color: #e5f5ec; margin: 0; font-size: .98rem; }
      .section-note { color: #587267; font-size: .9rem; }
      div[data-testid="stMetric"] { background: white; border: 1px solid #e0ebe4; padding: .85rem .9rem; border-radius: 14px; }
      div[data-testid="stMetricLabel"] { color: #547064; }
      div[data-testid="stMetricValue"] { color: #145c43; }
      .small-muted { color: #64796f; font-size: .82rem; }
      .stButton > button[kind="primary"] { background: #177b58; border-color: #177b58; }
      .stButton > button { border-radius: 10px; }
      .stForm { background: #fff; border: 1px solid #e1ebe4; border-radius: 14px; padding: 1rem; }
      [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }
      footer { visibility: hidden; }
      @media (max-width: 640px) {
        .block-container { padding: .75rem .8rem 2rem .8rem; }
        .hero { padding: 1rem; border-radius: 14px; }
        .brand-title { font-size: 1.3rem; }
        [data-testid="stMetric"] { padding: .65rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()


def set_flash(message: str, kind: str = "success") -> None:
    st.session_state["flash_message"] = message
    st.session_state["flash_kind"] = kind
    st.rerun()


def show_flash() -> None:
    message = st.session_state.pop("flash_message", None)
    kind = st.session_state.pop("flash_kind", "success")
    if message:
        if kind == "error":
            st.error(message)
        elif kind == "warning":
            st.warning(message)
        else:
            st.success(message)


def fmt_datetime(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return str(value)


def is_expired(value: str) -> bool:
    try:
        return datetime.fromisoformat(value) < now_local()
    except (TypeError, ValueError):
        return True


def qty(value: float) -> str:
    return f"{float(value):g} kg"


def donation_card(item: dict, compact: bool = False) -> None:
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.markdown(f"**🥕 {item['food_name']}** · {item['category']}")
            st.write(f"Donante: {item['donor_name']}")
            st.caption(f"Zona: {item['area']} · Recojo hasta: {fmt_datetime(item['available_until'])}")
            if item.get("notes") and not compact:
                st.caption(item["notes"])
        with right:
            st.metric("Disponible", qty(item["remaining_kg"]))
            if is_expired(item["available_until"]):
                st.caption("Plazo vencido")
            elif item["remaining_kg"] <= 0:
                st.caption("Cantidad reservada")


def need_card(item: dict, compact: bool = False) -> None:
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.markdown(f"**🍲 {item['kitchen_name']}** · {item['food_name']}")
            st.write(f"Contacto: {item['contact_name']}")
            st.caption(f"Zona: {item['area']} · Necesidad hasta: {fmt_datetime(item['needed_until'])}")
            if item.get("notes") and not compact:
                st.caption(item["notes"])
        with right:
            st.metric("Pendiente", qty(item["remaining_kg"]))
            if is_expired(item["needed_until"]):
                st.caption("Plazo vencido")


def show_header(title: str, subtitle: str) -> None:
    st.markdown(f"## {title}")
    st.markdown(f'<p class="section-note">{subtitle}</p>', unsafe_allow_html=True)


with st.sidebar:
    st.markdown('<div class="brand-title">🥕 VSE ALIMENTA</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Conectando alimentos con solidaridad</div>', unsafe_allow_html=True)
    st.divider()
    page = st.radio("NAVEGACIÓN", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption("PROTOTIPO · HACKODS UA 2026")
    st.caption("Villa El Salvador · ODS 2 y ODS 12")
    with st.expander("Herramientas de demostración"):
        st.warning("Restablecer borra los registros creados y vuelve a cargar los ejemplos ficticios.")
        confirm_reset = st.checkbox("Confirmo que deseo borrar los cambios")
        if st.button("Restablecer datos demo", disabled=not confirm_reset, use_container_width=True):
            reset_demo_data()
            set_flash("Los datos de demostración fueron restablecidos.")

show_flash()

if page == "Panel principal":
    st.markdown(
        """
        <div class="hero">
          <h1>La comida que sobra puede alimentar una comunidad.</h1>
          <p>VSE ALIMENTA conecta donantes y comedores populares de Villa El Salvador para reducir el desperdicio y facilitar la ayuda alimentaria.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Resumen de la plataforma")
    stats = dashboard_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Alimentos disponibles", qty(stats["available_kg"]))
    m2.metric("Alimentos entregados", qty(stats["delivered_kg"]))
    m3.metric("Reservas pendientes", stats["active_reservations"])
    m4.metric("Comedores atendidos", stats["delivered_kitchens"])

    st.info("Los registros precargados son ficticios y sirven únicamente para probar el prototipo. No representan donaciones ni comedores verificados.")
    st.markdown("### ¿Cómo funciona?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 1. Publicar")
        st.write("El donante registra el alimento, la cantidad y el plazo de recojo.")
    with c2:
        st.markdown("#### 2. Conectar")
        st.write("El sistema compara el alimento, la zona, la urgencia y la cantidad requerida.")
    with c3:
        st.markdown("#### 3. Entregar")
        st.write("El comedor reserva y, al recibir el alimento, se confirma la entrega.")

    st.markdown("### Donaciones recientes")
    donation_items = [x for x in list_donations() if x["remaining_kg"] > 0 and not is_expired(x["available_until"])][:3]
    if donation_items:
        cols = st.columns(min(3, len(donation_items)))
        for col, item in zip(cols, donation_items):
            with col:
                donation_card(item, compact=True)
    else:
        st.caption("Todavía no hay donaciones disponibles.")

    st.markdown("### Nuestro compromiso")
    st.markdown("**ODS 2 – Hambre cero:** facilitar el acceso a alimentos mediante redes de apoyo comunitario.  \n**ODS 12 – Producción y consumo responsables:** promover el aprovechamiento de alimentos aptos para el consumo.")

elif page == "Registrar donación":
    show_header("Registrar una donación", "Los comercios, mercados y personas pueden publicar alimentos disponibles para donar.")
    st.info("Registra únicamente alimentos aptos para el consumo. La plataforma no sustituye la revisión sanitaria ni garantiza la cadena de frío o el transporte.")
    default_until = now_local() + timedelta(hours=8)
    with st.form("donation_form", clear_on_submit=True):
        st.markdown("#### Datos del donante")
        a, b = st.columns(2)
        with a:
            donor_name = st.text_input("Nombre del donante o comercio *", placeholder="Ej. Mercado Vecinal")
            donor_phone = st.text_input("Teléfono de contacto", placeholder="Ej. 9XXXXXXXX")
        with b:
            area = st.text_input("Sector o zona de Villa El Salvador *", placeholder="Ej. Sector 2")
            pickup_address = st.text_input("Punto o dirección de recojo *", placeholder="Indica dónde se recogerá")

        st.markdown("#### Datos del alimento")
        a, b, c = st.columns(3)
        with a:
            food_name = st.text_input("Alimento *", placeholder="Ej. Arroz")
        with b:
            category = st.selectbox("Categoría *", CATEGORIES)
        with c:
            quantity_kg = st.number_input("Cantidad (kg) *", min_value=0.1, max_value=10000.0, value=5.0, step=0.5)

        st.markdown("#### Disponibilidad")
        a, b = st.columns(2)
        with a:
            until_date = st.date_input("Fecha límite de recojo *", value=default_until.date(), min_value=now_local().date())
        with b:
            until_time = st.time_input("Hora límite de recojo *", value=default_until.time().replace(second=0, microsecond=0))
        notes = st.text_area("Observaciones", placeholder="Estado, presentación, condiciones de conservación, etc.", height=80)
        safe_food = st.checkbox("Confirmo que el alimento está apto para el consumo y que informaré sus condiciones de conservación. *")
        submitted = st.form_submit_button("Publicar donación", type="primary", use_container_width=True)

    if submitted:
        expiry = datetime.combine(until_date, until_time)
        missing = not all([donor_name.strip(), area.strip(), pickup_address.strip(), food_name.strip()])
        if missing:
            st.error("Completa todos los campos obligatorios marcados con *.")
        elif expiry <= now_local():
            st.error("La fecha y hora límite deben ser posteriores al momento actual.")
        elif not safe_food:
            st.error("Debes confirmar las condiciones de aptitud del alimento.")
        else:
            try:
                new_id = add_donation({
                    "donor_name": donor_name,
                    "donor_phone": donor_phone,
                    "food_name": food_name,
                    "category": category,
                    "quantity_kg": quantity_kg,
                    "area": area,
                    "pickup_address": pickup_address,
                    "available_until": expiry.isoformat(sep=" ", timespec="minutes"),
                    "notes": notes,
                })
                set_flash(f"Donación #{new_id} publicada correctamente.")
            except Exception as exc:
                st.error(f"No se pudo guardar la donación: {exc}")

elif page == "Registrar necesidad":
    show_header("Registrar necesidad de un comedor", "Los comedores populares pueden indicar qué alimentos y cantidades necesitan.")
    with st.form("need_form", clear_on_submit=True):
        st.markdown("#### Datos del comedor")
        a, b = st.columns(2)
        with a:
            kitchen_name = st.text_input("Nombre del comedor popular *", placeholder="Ej. Comedor Las Flores")
            contact_name = st.text_input("Persona de contacto *", placeholder="Nombre y apellido")
        with b:
            phone = st.text_input("Teléfono de contacto", placeholder="Ej. 9XXXXXXXX")
            area = st.text_input("Sector o zona de Villa El Salvador *", placeholder="Ej. Sector 2")
        address = st.text_input("Punto o dirección de recepción *", placeholder="Indica dónde se recibiría la donación")

        st.markdown("#### Alimento requerido")
        a, b, c = st.columns(3)
        with a:
            food_name = st.text_input("Alimento solicitado *", placeholder="Ej. Arroz")
        with b:
            category = st.selectbox("Categoría *", CATEGORIES, key="need_category")
        with c:
            quantity_kg = st.number_input("Cantidad requerida (kg) *", min_value=0.1, max_value=10000.0, value=10.0, step=0.5, key="need_qty")

        default_until = now_local() + timedelta(hours=24)
        a, b = st.columns(2)
        with a:
            until_date = st.date_input("Necesario hasta la fecha *", value=default_until.date(), min_value=now_local().date(), key="need_date")
        with b:
            until_time = st.time_input("Hora límite *", value=default_until.time().replace(second=0, microsecond=0), key="need_time")
        notes = st.text_area("Observaciones", placeholder="Ej. Se requiere alimento en envase cerrado.", height=80, key="need_notes")
        submitted = st.form_submit_button("Registrar necesidad", type="primary", use_container_width=True)

    if submitted:
        deadline = datetime.combine(until_date, until_time)
        missing = not all([kitchen_name.strip(), contact_name.strip(), area.strip(), address.strip(), food_name.strip()])
        if missing:
            st.error("Completa todos los campos obligatorios marcados con *.")
        elif deadline <= now_local():
            st.error("La fecha y hora límite deben ser posteriores al momento actual.")
        else:
            try:
                new_id = add_need({
                    "kitchen_name": kitchen_name,
                    "contact_name": contact_name,
                    "phone": phone,
                    "food_name": food_name,
                    "category": category,
                    "quantity_kg": quantity_kg,
                    "area": area,
                    "address": address,
                    "needed_until": deadline.isoformat(sep=" ", timespec="minutes"),
                    "notes": notes,
                })
                set_flash(f"Necesidad #{new_id} registrada correctamente.")
            except Exception as exc:
                st.error(f"No se pudo guardar la necesidad: {exc}")

elif page == "Emparejar y reservar":
    show_header("Emparejar donaciones con comedores", "El sistema propone coincidencias según alimento, zona, cantidad y urgencia.")
    st.caption("El puntaje es una regla de priorización explicable; no es inteligencia artificial ni reemplaza la coordinación entre las partes.")
    donations = list_donations()
    needs = list_needs()
    matches = build_matches(donations, needs, limit=30)
    if not matches:
        st.warning("Todavía no hay coincidencias. Registra una donación y una necesidad con alimentos o categorías compatibles y plazos vigentes.")
    else:
        st.markdown(f"**{len(matches)} coincidencia(s) encontrada(s)**")
        for index, match in enumerate(matches, start=1):
            donation = match["donation"]
            need = match["need"]
            with st.container(border=True):
                top1, top2 = st.columns([3, 1])
                with top1:
                    st.markdown(f"### Coincidencia {index}: {donation['food_name']}")
                    st.write(f"**Donante:** {donation['donor_name']} · **Comedor:** {need['kitchen_name']}")
                    st.caption(f"Donación en {donation['area']} · Comedor en {need['area']}")
                with top2:
                    st.metric("Puntaje de compatibilidad", f"{match['score']}/100")
                st.markdown("**¿Por qué se recomienda?**")
                st.write(" · ".join(match["reasons"]))
                st.caption(f"Disponible: {qty(match['donation_remaining_kg'])} · Necesidad pendiente: {qty(match['need_remaining_kg'])} · Recojo hasta: {fmt_datetime(donation['available_until'])}")
                max_reservable = min(match["donation_remaining_kg"], match["need_remaining_kg"])
                c1, c2 = st.columns([1, 2])
                with c1:
                    reserve_qty = st.number_input(
                        "Cantidad para reservar (kg)", min_value=0.1, max_value=float(max_reservable),
                        value=float(max_reservable), step=0.5,
                        key=f"reserve_qty_{donation['id']}_{need['id']}",
                    )
                with c2:
                    st.write("")
                    st.write("")
                    if st.button("Reservar esta donación", key=f"reserve_btn_{donation['id']}_{need['id']}", type="primary", use_container_width=True):
                        try:
                            reservation_id = create_reservation(donation["id"], need["id"], reserve_qty)
                            set_flash(f"Reserva #{reservation_id} creada. Coordinen el recojo y la recepción.")
                        except ValueError as exc:
                            st.error(str(exc))
                        except Exception as exc:
                            st.error(f"No se pudo crear la reserva: {exc}")

elif page == "Entregas":
    show_header("Seguimiento de entregas", "Confirma la recepción de las donaciones reservadas o cancela una reserva que no se concretará.")
    reservations = list_reservations()
    if not reservations:
        st.info("Todavía no existen reservas. Ve a 'Emparejar y reservar' para crear la primera.")
    else:
        for item in reservations:
            with st.container(border=True):
                a, b = st.columns([3, 1])
                with a:
                    st.markdown(f"**#{item['id']} · {item['food_name']} — {qty(item['quantity_kg'])}**")
                    st.write(f"{item['donor_name']}  →  {item['kitchen_name']}")
                    st.caption(f"Reserva: {fmt_datetime(item['created_at'])}")
                    if item["status"] == "Entregada":
                        st.caption(f"Entrega confirmada: {fmt_datetime(item['delivered_at'])}")
                with b:
                    if item["status"] == "Reservada":
                        st.warning("Pendiente")
                    elif item["status"] == "Entregada":
                        st.success("Entregada")
                    else:
                        st.error("Cancelada")
                if item["status"] == "Reservada":
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Confirmar entrega", key=f"deliver_{item['id']}", type="primary", use_container_width=True):
                            try:
                                mark_delivered(item["id"])
                                set_flash(f"La entrega #{item['id']} fue confirmada.")
                            except ValueError as exc:
                                st.error(str(exc))
                    with c2:
                        if st.button("Cancelar reserva", key=f"cancel_{item['id']}", use_container_width=True):
                            try:
                                cancel_reservation(item["id"])
                                set_flash(f"La reserva #{item['id']} fue cancelada y la cantidad volvió a estar disponible.", "warning")
                            except ValueError as exc:
                                st.error(str(exc))

elif page == "Registros":
    show_header("Registros de la plataforma", "Consulta las donaciones publicadas y las necesidades registradas.")
    tab1, tab2 = st.tabs(["Donaciones", "Necesidades de comedores"])
    with tab1:
        all_donations = list_donations()
        if not all_donations:
            st.info("No hay donaciones registradas.")
        else:
            for item in all_donations:
                donation_card(item)
                st.caption(f"Registro #{item['id']} · Publicado: {fmt_datetime(item['created_at'])} · Punto de recojo: {item['pickup_address']}")
    with tab2:
        all_needs = list_needs()
        if not all_needs:
            st.info("No hay necesidades registradas.")
        else:
            for item in all_needs:
                need_card(item)
                st.caption(f"Registro #{item['id']} · Publicado: {fmt_datetime(item['created_at'])} · Recepción: {item['address']}")

st.divider()
st.markdown(
    '<p class="small-muted">VSE ALIMENTA · Prototipo académico para HackODS UA 2026 · Datos de demostración ficticios · ODS 2 y ODS 12</p>',
    unsafe_allow_html=True,
)
