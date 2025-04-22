import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model

st.set_page_config(page_title="שיבוץ מתמחים אוטומטי", layout="wide")
st.title("📅 פתרון אוטומטי לשיבוץ רופאים מתמחים - משימה 2 בלבד")

st.markdown("האפליקציה מנסה למצוא את המספר המינימלי של מתמחים הנדרשים כדי לעמוד בדרישות משימה 2.")

run_button = st.button("▶ התחל חישוב אוטומטי")

if run_button:
    NUM_DAYS = 30
    SHIFT_TYPES = ['regular_weekday', 'night_weekday', 'regular_friday', 'night_friday', 'night_saturday']
    SHIFT_HOURS = {'regular_weekday': 16, 'night_weekday': 32,
                   'regular_friday': 10, 'night_friday': 38, 'night_saturday': 48}  # כפול 2
    WEEKEND_SHIFTS = ['night_friday', 'night_saturday']

    found = False
    max_interns = 40
    min_required = None
    final_schedule_df = None

    for num_interns in range(10, max_interns + 1):
        model = cp_model.CpModel()
        intern_assigned = {}
        for i in range(num_interns):
            for d in range(NUM_DAYS):
                for s in SHIFT_TYPES:
                    intern_assigned[(i, d, s)] = model.NewBoolVar(f"intern_{i}_day_{d}_{s}")

        for d in range(NUM_DAYS):
            for s in SHIFT_TYPES:
                model.AddExactlyOne(intern_assigned[(i, d, s)] for i in range(num_interns))

        for i in range(num_interns):
            for week in range(4):
                start_day = week * 7
                end_day = min(start_day + 7, NUM_DAYS)
                total_hours = []
                night_shifts = []
                for d in range(start_day, end_day):
                    for s in SHIFT_TYPES:
                        total_hours.append(intern_assigned[(i, d, s)] * SHIFT_HOURS[s])
                    for s in ['night_weekday', 'night_friday', 'night_saturday']:
                        night_shifts.append(intern_assigned[(i, d, s)])
                model.Add(cp_model.LinearExpr.Sum(total_hours) <= 143)
                model.Add(cp_model.LinearExpr.Sum(night_shifts) <= 2)

            weekend_shifts = [intern_assigned[(i, d, s)] for d in range(NUM_DAYS) for s in WEEKEND_SHIFTS]
            model.Add(cp_model.LinearExpr.Sum(weekend_shifts) <= 1)

            for d in range(NUM_DAYS - 2):
                current_night = [intern_assigned[(i, d, s)] for s in ['night_weekday', 'night_friday', 'night_saturday']]
                next_48h = [intern_assigned[(i, d2, s)] for d2 in [d+1, d+2] if d2 < NUM_DAYS for s in ['night_weekday', 'night_friday', 'night_saturday']]
                for c in current_night:
                    for n in next_48h:
                        model.Add(c + n <= 1)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            rows = []
            for d in range(NUM_DAYS):
                for s in SHIFT_TYPES:
                    for i in range(num_interns):
                        if solver.Value(intern_assigned[(i, d, s)]):
                            rows.append({'יום': d + 1, 'משמרת': s, 'מתמחה': i})
            final_schedule_df = pd.DataFrame(rows)
            min_required = num_interns
            found = True
            break

    if found:
        st.success(f"✔ נמצא פתרון עבור {min_required} מתמחים בלבד!")
        st.dataframe(final_schedule_df)
        excel_file = final_schedule_df.to_excel(index=False)
        st.download_button(
            label="📥 הורד את השיבוץ לקובץ Excel",
            data=excel_file,
            file_name="shifts_schedule_task2.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("❌ לא נמצא פתרון לשיבוץ, גם עבור 40 מתמחים. ייתכן שהאילוצים נוקשים מדי.")
