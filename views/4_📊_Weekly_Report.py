from collections import defaultdict

import streamlit as st
import datetime
from database import get_db, Schedule
from utils import generate_excel_report  # Импортируем именно Schedule из твоей database.py



st.title("📊 Weekly Accounting Report")


db = get_db()

st.subheader("Select Week for Export")
st.caption("The report will ONLY include workers who have at least 1 tracked hour during the selected week.")

selected_date = st.date_input("Select any day from the target week:", datetime.date.today())

# Вычисляем границы недели (Понедельник - Воскресенье)
start_of_week = selected_date - datetime.timedelta(days=selected_date.weekday())
end_of_week = start_of_week + datetime.timedelta(days=6)

week_number = start_of_week.isocalendar()[1]
year_number = start_of_week.isocalendar()[0]

st.info(f"📆 **Selected Period:** Monday {start_of_week.strftime('%d-%m-%Y')} — Sunday {end_of_week.strftime('%d-%m-%Y')} (Week {week_number}, {year_number})")

if st.button("🚀 Generate and Preview Excel Report", use_container_width=True):
    weekly_shifts = (
        db.query(Schedule)
        .filter(
            Schedule.date.between(start_of_week, end_of_week),
            Schedule.hours > 0
        )
        .order_by(Schedule.date)
        .all()
    )
    
    if not weekly_shifts:
        st.warning("No tracked hours found in schedule for this week. Nothing to export.")
    else:
        # Теперь структура будет: { worker_id: { "worker": worker_object, "dates": { date: hours } } }
        workers_data = {}

        for shift in weekly_shifts:
            worker = shift.worker
            if not worker or worker.is_fired:
                continue

            w_id = worker.id

            # Если сотрудника еще нет в словаре, создаем для него структуру
            if w_id not in workers_data:
                workers_data[w_id] = {
                    "worker": worker,
                    "dates": {}
                }

            # Суммируем часы за конкретный день по его ID
            current_hours = workers_data[w_id]["dates"].get(shift.date, 0.0)
            workers_data[w_id]["dates"][shift.date] = current_hours + float(shift.hours)

        # Жесткая фильтрация: оставляем только тех, у кого сумма часов > 0
        active_this_week = {}
        for w_id, info in workers_data.items():
            dates_dict = info["dates"]
            if sum(dates_dict.values()) > 0:
                # Передаем объект воркера как ключ, а даты как значение, 
                # чтобы не переписывать твою функцию generate_excel_report
                active_this_week[info["worker"]] = dates_dict
        
        if not active_this_week:
            st.warning("All filtered workers have 0 total hours for this period.")
        else:
            try:
                excel_file = generate_excel_report(
                    active_this_week,
                    week_number,
                    start_of_week
                )


                st.success(
                    f"📊 Report successfully generated for {len(active_this_week)} active workers!"
                )


                st.download_button(
                    label="📥 Download Ready Excel Report",
                    data=excel_file,
                    file_name=f"Amsterdam_Warehouse_Week_{week_number}_{year_number}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


            except Exception as e:

                st.error(
                    f"An error occurred during Excel generation: {e}"
                )

db.close()