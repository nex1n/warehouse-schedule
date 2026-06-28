import streamlit as st
from datetime import datetime
from sqlalchemy import and_
from database import get_db, Worker, Schedule, Vacation

st.title("📅 Daily Schedule Planner")
db = get_db()

selected_date = st.date_input("Select Date", datetime.now().date())

DAYS_ENG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_NL = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
day_idx = selected_date.weekday()
day_name_eng = DAYS_ENG[day_idx]
visual_date_str = f"{DAYS_NL[day_idx]} {selected_date.strftime('%d-%m')}"

current_shifts = db.query(Schedule).filter(Schedule.date == selected_date).all()
busy_worker_ids = [shift.worker_id for shift in current_shifts]

all_ct_workers = db.query(Worker).filter(
    Worker.is_fired == False,
    Worker.projectcode == "ALW ct",
    ~Worker.vacations.any(
        and_(Vacation.start_date <= selected_date, Vacation.end_date >= selected_date)
    )
).all()

recommended_list = []
hidden_list = []

for w in all_ct_workers:
    if w.id in busy_worker_ids:
        continue
    if w.fixed_course_days and day_name_eng in w.fixed_course_days:
        continue
        
    if w.is_active:
        recommended_list.append(w)
    else:
        hidden_list.append(w)
        
recommended_list.sort(key=lambda x: x.full_name)
hidden_list.sort(key=lambda x: x.full_name)

with st.expander("➕ Assign Worker to a Shift (Click to expand)", expanded=False):
    dropdown_options = {}
    for w in recommended_list:
        dropdown_options[w.id] = f"🟢 {str(w.full_name)} ({str(w.notes) if w.notes else 'no notes'})"
    for w in hidden_list:
        dropdown_options[w.id] = f"⏳ [Not Recommended] {str(w.full_name)} ({str(w.notes) if w.notes else 'no notes'})"
        
    if dropdown_options:
        with st.form("add_shift_form", clear_on_submit=True):
            selected_w_id = st.selectbox(
                "Available Workers (ALW ct)", 
                options=list(dropdown_options.keys()), 
                format_func=lambda x: dropdown_options[x]
            )
            
            all_merged = recommended_list + hidden_list
            chosen_worker_obj = next(w.preferred_object for w in all_merged if w.id == selected_w_id)
            obj_default_idx = ["Slego", "Conakry"].index(chosen_worker_obj) if chosen_worker_obj in ["Slego", "Conakry"] else 0
            
            col_obj, col_sub = st.columns(2)
            with col_obj:
                shift_object = st.selectbox("Object", ["Slego", "Conakry"], index=obj_default_idx)
            with col_sub:
                shift_sub_object = st.text_input("Sub-object (Optional)", placeholder="e.g., A").strip()
                
            submit_shift = st.form_submit_button("Assign to Shift")
            if submit_shift:
                new_shift = Schedule(
                    date=selected_date, 
                    worker_id=selected_w_id, 
                    object=shift_object, 
                    sub_object=shift_sub_object if shift_sub_object else None, 
                    hours=8.0
                )
                db.add(new_shift)
                db.commit()
                st.success("Worker assigned successfully!")
                st.rerun()
    else:
        st.info("🎉 No workers available for this date!")

st.markdown("---")
if current_shifts:
    slego_shifts = [s for s in current_shifts if s.object == "Slego"]
    conakry_shifts = [s for s in current_shifts if s.object == "Conakry"]
    
    st.markdown(f"### {visual_date_str}")
    st.markdown("")  
    
    if slego_shifts:
        st.markdown("Team 1 - Slego")
    if conakry_shifts:
        st.markdown("Team 2 - Conakry")
        
    st.markdown("")
    st.markdown("")  
    
    name_style = "style='font-size: 20px; font-weight: normal; line-height: 1.4;'"
    team_title_style = "style='font-size: 22px; font-weight: bold; margin-bottom: 8px; display: inline-block;'"
    sub_object_style = "style='font-size: 20px; font-weight: bold; margin-top: 6px; margin-bottom: 2px; display: inline-block;'"

    slego_html = ""
    if slego_shifts:
        slego_html += f"<span {team_title_style}>Team 1</span><br>"
        main_slego = [s for s in slego_shifts if not s.sub_object]
        for s in main_slego:
            slego_html += f"<span {name_style}>{s.worker.full_name}</span><br>"
            
        slego_groups = {}
        for s in [s for s in slego_shifts if s.sub_object]:
            slego_groups.setdefault(s.sub_object, []).append(s)
            
        for sub_name in sorted(slego_groups.keys()):
            slego_html += f"<span {sub_object_style}>{sub_name}</span><br>"
            for s in slego_groups[sub_name]:
                slego_html += f"<span {name_style}>{s.worker.full_name}</span><br>"

    conakry_html = ""
    if conakry_shifts:
        conakry_html += f"<span {team_title_style}>Team 2</span><br>"
        main_conakry = [s for s in conakry_shifts if not s.sub_object]
        for s in main_conakry:
            conakry_html += f"<span {name_style}>{s.worker.full_name}</span><br>"
            
        conakry_groups = {}
        for s in [s for s in conakry_shifts if s.sub_object]:
            conakry_groups.setdefault(s.sub_object, []).append(s)
            
        for sub_name in sorted(conakry_groups.keys()):
            conakry_html += f"<span {sub_object_style}>{sub_name}</span><br>"
            for s in conakry_groups[sub_name]:
                conakry_html += f"<span {name_style}>{s.worker.full_name}</span><br>"

    table_html = f"""
    <table style="width:100%; border:none; border-collapse:collapse; margin-bottom:20px;">
        <tr style="border:none;">
            <td style="width:50%; vertical-align:top; border:none; padding-right:15px;">
                {slego_html}
            </td>
            <td style="width:50%; vertical-align:top; border:none; padding-left:15px;">
                {conakry_html}
            </td>
        </tr>
    </table>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### Remove from planner:")
    for s in current_shifts:
        sub_info = f" ({s.sub_object})" if s.sub_object else ""
        if st.button(f"❌ Remove {s.worker.full_name} from {s.object}{sub_info}", key=f"del_shift_{s.id}"):
            db.delete(s)
            db.commit()
            st.rerun()
else:
    st.warning("No shifts planned for this date.")
db.close()