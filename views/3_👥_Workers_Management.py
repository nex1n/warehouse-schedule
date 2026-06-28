import streamlit as st
from database import get_db, Worker

st.title("👥 Workers Database Management")
db = get_db()

# Разделяем интерфейс на Активных сотрудников, Регистрацию и Архив уволенных
tab_roster, tab_register, tab_archive = st.tabs([
    "🟢 Active Workers Roster", 
    "➕ Register Employee", 
    "🗄️ Fired Workers Archive"
])

# ==============================================================================
# ВКЛАДКА 1: СПИСОК АКТИВНЫХ СОТРУДНИКОВ И РЕДАКТИРОВАНИЕ
# ==============================================================================
with tab_roster:
    st.subheader("📝 Current Staff Profiles")
    active_workers = db.query(Worker).filter(Worker.is_fired == False).order_by(Worker.full_name).all()

    if active_workers:
        for w in active_workers:
            rec_status = "📋 In Planner" if w.is_active else "⏳ Hidden"
            
            with st.expander(f"👤 {w.full_name} ({w.projectcode} | {rec_status})", expanded=False):
                pref_choices = [None, "Slego", "Conakry"]
                pref_idx = pref_choices.index(w.preferred_object) if w.preferred_object in pref_choices else 0
                
                pcode_choices = ["ALW ct", "ALW FIX"]
                pcode_idx = pcode_choices.index(w.projectcode) if w.projectcode in pcode_choices else 0
                
                with st.container(border=True):
                    col_1, col_2 = st.columns(2)
                    with col_1:
                        edited_pref = st.selectbox("Preferred Object", pref_choices, index=pref_idx, key=f"pref_{w.id}")
                        edited_cc = st.text_input("CC Level", value=w.cc if w.cc else "", key=f"cc_{w.id}").strip()
                    with col_2:
                        edited_projectcode = st.selectbox("Projectcode", pcode_choices, index=pcode_idx, key=f"pcode_{w.id}")
                        edited_active = st.checkbox("Recommend this worker in Schedule Planner", value=bool(w.is_active), key=f"active_{w.id}")
                    
                    edited_notes = st.text_area("Notes / Constraints", value=w.notes if w.notes else "", key=f"notes_{w.id}").strip()
                    
                    # Десериализация дней курсов (из строки в список для multiselect)
                    current_course_days = w.fixed_course_days.split(", ") if w.fixed_course_days else []
                    select_key = f"course_select_{w.id}"
                    edited_courses = st.multiselect(
                        "Fixed Course/Off Days (Excluded from auto-planning on these days)", 
                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], 
                        default=current_course_days, 
                        key=select_key
                    )
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    # Кнопки действия в равных пропорциях для симметрии
                    col_save, col_fire = st.columns(2)
                    with col_save:
                        if st.button("💾 Save Profile", key=f"save_{w.id}", use_container_width=True):
                            w.preferred_object = edited_pref
                            w.projectcode = edited_projectcode
                            w.cc = edited_cc if edited_cc else None
                            w.notes = edited_notes if edited_notes else None
                            
                            user_choices = st.session_state[select_key]
                            w.fixed_course_days = ", ".join(user_choices) if user_choices else None
                            
                            w.is_active = edited_active
                            db.commit()
                            st.success("Saved successfully!")
                            st.rerun()
                            
                    with col_fire:
                        if st.button("🔥 Fire Worker", key=f"fire_{w.id}", type="primary", use_container_width=True):
                            w.is_fired = True
                            w.is_active = False  # Сразу убираем из предложений планировщика
                            db.commit()
                            st.warning(f"{w.full_name} moved to Archive.")
                            st.rerun()
    else:
        st.info("No active workers in database.")

# ==============================================================================
# ВКЛАДКА 2: РЕГИСТРАЦИЯ НОВОГО СОТРУДНИКА
# ==============================================================================
with tab_register:
    st.subheader("🆕 Add New Employee Profile")
    with st.form("create_worker_form", clear_on_submit=True):
        f_name = st.text_input("Full Name (e.g. John Doe)").strip()
        p_code = st.selectbox("Projectcode", ["ALW ct", "ALW FIX"])
        p_obj = st.selectbox("Preferred Object", [None, "Slego", "Conakry"])
        c_centre = st.text_input("CC Level (Optional)").strip()
        w_notes = st.text_area("Notes (Optional)").strip()
        
        # Регистрация
        if st.form_submit_button("➕ Register Employee", use_container_width=True):
            if f_name:
                new_w = Worker(
                    full_name=f_name, 
                    projectcode=p_code, 
                    preferred_object=p_obj,
                    cc=c_centre if c_centre else None, 
                    notes=w_notes if w_notes else None,
                    is_active=True, 
                    is_fired=False
                )
                db.add(new_w)
                db.commit()
                st.success(f"Successfully registered {f_name}!")
                st.rerun()
            else:
                st.error("Full Name cannot be empty.")

# ==============================================================================
# ВКЛАДКА 3: АРХИВ УВОЛЕННЫХ СОТРУДНИКОВ (ДЛЯ ИСПРАВЛЕНИЯ БАГА)
# ==============================================================================
with tab_archive:
    st.subheader("🗄️ Fired Workers Historical Archive")
    st.caption("People in this archive do not appear in the Daily Scheduler or Hours Tracker modules.")
    
    # Извлекаем из БД тех, у кого флаг ис_фиред выставлен в Тру
    fired_workers = db.query(Worker).filter(Worker.is_fired == True).order_by(Worker.full_name).all()
    
    if not fired_workers:
        st.info("The archive is empty. No fired workers found.")
    else:
        for f_worker in fired_workers:
            with st.container(border=True):
                col_info, col_action = st.columns([3, 1])
                with col_info:
                    st.markdown(f"**👤 {f_worker.full_name}**")
                    st.caption(f"Projectcode: {f_worker.projectcode} | Preferred: {f_worker.preferred_object if f_worker.preferred_object else 'None'}")
                with col_action:
                    # Кнопка восстановления
                    if st.button("🔄 Restore to Staff", key=f"restore_{f_worker.id}", use_container_width=True):
                        f_worker.is_fired = False
                        f_worker.is_active = True  # Снова возвращаем в пул планировщика
                        db.commit()
                        st.success(f"{f_worker.full_name} successfully restored!")
                        st.rerun()

db.close()