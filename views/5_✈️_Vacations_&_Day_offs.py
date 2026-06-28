import streamlit as st
from datetime import datetime, timedelta
from database import get_db, Worker, Vacation

st.title("✈️ Vacations & Blocked Calendar")
db = get_db()

workers = db.query(Worker).filter(Worker.is_fired == False).order_by(Worker.full_name).all()

if workers:
    with st.expander("➕ Grant New Vacation / Day Off Range (Click to expand)", expanded=False):
        w_dict = {w.id: w.full_name for w in workers}
        
        with st.form("vacation_form", clear_on_submit=True):
            v_worker_id = st.selectbox("Employee", options=list(w_dict.keys()), format_func=lambda x: w_dict[x])
            
            col_s, col_e = st.columns(2)
            with col_s:
                v_start = st.date_input("Start Date", datetime.now().date())
            with col_e:
                v_end = st.date_input("End Date", datetime.now().date() + timedelta(days=2))
                
            v_reason = st.text_input("Reason / Comment (e.g. Trip to Spain)").strip()
            
            if st.form_submit_button("🔒 Lock Dates"):
                if v_start <= v_end:
                    new_v = Vacation(
                        worker_id=v_worker_id, start_date=v_start, end_date=v_end, reason=v_reason if v_reason else None
                    )
                    db.add(new_v)
                    db.commit()
                    st.success("Dates locked! Worker will be hidden from planner for this period.")
                    st.rerun()
                else:
                    st.error("Start date must be before or equal to End date.")

st.markdown("---")
st.subheader("📅 Registered Vacations")
all_vacations = db.query(Vacation).order_by(Vacation.start_date.desc()).all()

if all_vacations:
    for v in all_vacations:
        with st.expander(f"✈️ {v.worker.full_name}: {v.start_date.strftime('%d/%m')} to {v.end_date.strftime('%d/%m')}"):
            updated_reason = st.text_input("New Reason", value=v.reason if v.reason else "", key=f"edit_reason_{v.id}").strip()
            
            col_up, col_del = st.columns([1, 4])
            with col_up:
                if st.button("Update Comment", key=f"upd_vac_{v.id}"):
                    v.reason = updated_reason if updated_reason else None
                    db.commit()
                    st.success("Comment updated!")
                    st.rerun()
            with col_del:
                if st.button("❌ Cancel Vacation", key=f"del_vac_{v.id}", type="primary"):
                    db.delete(v)
                    db.commit()
                    st.warning("Vacation deleted.")
                    st.rerun()
else:
    st.info("No vacations booked ahead.")
db.close()