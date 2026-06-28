import streamlit as st
from datetime import datetime
from database import get_db, Worker, Schedule

st.title("⏱ Daily Hours Tracker")
db = get_db()

selected_date = st.date_input("Select Date for Logging", datetime.now().date())

recorded_shifts = db.query(Schedule).filter(Schedule.date == selected_date).all()
recorded_worker_ids = [s.worker_id for s in recorded_shifts]

query_unrecorded = db.query(Worker).filter(Worker.is_fired == False)
if recorded_worker_ids:
    query_unrecorded = query_unrecorded.filter(~Worker.id.in_(recorded_worker_ids))
unrecorded_workers = query_unrecorded.order_by(Worker.full_name).all()

if unrecorded_workers:
    with st.expander("➕ Add Extra Unplanned Worker (Click to expand)", expanded=False):
        w_options = {w.id: f"{str(w.full_name)} ({str(w.projectcode)})" for w in unrecorded_workers}
        
        with st.form("extra_worker_form"):
            extra_w_id = st.selectbox("Select Worker", options=list(w_options.keys()), format_func=lambda x: w_options[x])
            col_o, col_h = st.columns(2)
            with col_o:
                extra_obj = st.selectbox("Object", ["Slego", "Conakry", "ALW FIX Office"])
            with col_h:
                extra_hours = st.number_input("Hours Worked", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
            
            if st.form_submit_button("Add to Tracker"):
                new_extra = Schedule(date=selected_date, worker_id=extra_w_id, object=extra_obj, hours=extra_hours)
                db.add(new_extra)
                db.commit()
                st.success("Added extra shift log successfully!")
                st.rerun()

st.markdown("---")
st.subheader(f"📝 Logging Hours for: {selected_date.strftime('%A, %d-%m-%Y')}")

if recorded_shifts:
    for s in recorded_shifts:
        with st.expander(f"👤 {s.worker.full_name} — {s.object} ({s.hours} hrs)"):
            col_hours, col_action = st.columns([3, 1])
            with col_hours:
                current_hours_float = float(s.hours) if s.hours is not None else 0.0
                new_h = st.number_input(f"Modify hours for {s.worker.full_name}", min_value=0.0, max_value=24.0, value=current_hours_float, step=0.5, key=f"hrs_input_{s.id}")
            with col_action:
                st.write("") 
                if st.button("💾 Update Hours", key=f"upd_hrs_{s.id}"):
                    s.hours = new_h
                    db.commit()
                    st.success(f"Updated hours for {s.worker.full_name}!")
                    st.rerun()
else:
    st.info("No logs generated for this date yet. Use Planner or add extra workers above.")
db.close()