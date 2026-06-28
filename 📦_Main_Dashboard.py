import os
import time
import streamlit as st
from dotenv import load_dotenv
import extra_streamlit_components as stx
from database import check_db_connection, init_db

load_dotenv()

# 1. Глобальная конфигурация приложения (ОБЯЗАТЕЛЬНО самый первый вызов Streamlit)
st.set_page_config(
    page_title="Warehouse Schedule Pro",
    page_icon="📦",
    layout="wide"
)

# ==============================================================================
# 2. ОПРЕДЕЛЕНИЕ ФУНКЦИИ ХАБА (Теперь она в самом верху, NameError исключен!)
# ==============================================================================
def render_hub_dashboard():
    if not check_db_connection():
        st.error(
            "### 🔌 Database Connection Error\n\n"
            "Cannot connect to the cloud PostgreSQL database. Check connection credentials.",
            icon="🚨"
        )
        st.stop()

    init_db()

    st.title("📦 Warehouse Management Panel")
    st.subheader("Welcome to the warehouse operations coordination system")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown(
                "### 📅 Operational Planning\n"
                "* **Schedule Planner** — Allocate personnel across Slego and Conakry objects.\n"
                "* **Hours Tracker** — Log and correct actual hours worked by the team."
            )
    with col2:
        with st.container(border=True):
            st.markdown(
                "### 👥 Staff & Analytics\n"
                "* **Workers Management** — Oversee employee profiles.\n"
                "* **Weekly Report** — Export consolidated shift metrics.\n"
                "* **Vacations & Day Offs** — Lock calendar ranges for vacations."
            )


# ==============================================================================
# 3. ИНИЦИАЛИЗАЦИЯ КУКИ И СИНХРОНИЗАЦИЯ
# ==============================================================================
cookie_manager = stx.CookieManager()

# Синхронизатор куки через Session State (без использования .ready())
if "initial_cookie_sync" not in st.session_state:
    time.sleep(0.1)
    st.session_state["initial_cookie_sync"] = True
    st.rerun()

# Читаем токен авторизации
auth_cookie = cookie_manager.get(cookie="warehouse_auth_token")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Автоматический вход, если куки совпадает с паролем из .env
env_pass = os.getenv("SITE_PASSWORD", "super_secret_password_123")
if auth_cookie == env_pass:
    st.session_state["authenticated"] = True


# ==============================================================================
# 4. ШЛЮЗ БЕЗОПАСНОСТИ И ДИНАМИЧЕСКАЯ НАВИГАЦИЯ
# ==============================================================================

if not st.session_state["authenticated"]:
    # Пользователь НЕ авторизован — показываем только форму входа
    st.title("🔒 Access Restricted")
    st.subheader("Please sign in to access the Warehouse Management Panel")
    
    env_user = os.getenv("SITE_USERNAME", "admin")
    
    with st.form("login_form", clear_on_submit=False):
        input_user = st.text_input("Username")
        input_pass = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In")
        
        if submit:
            if input_user == env_user and input_pass == env_pass:
                st.session_state["authenticated"] = True
                
                # Записываем куки в браузер на 30 дней
                cookie_manager.set(
                    cookie="warehouse_auth_token",
                    val=env_pass,
                    max_age=30 * 24 * 3600
                )
                st.success("Access granted!")
                time.sleep(0.5)  # Даем куки физически записаться
                st.rerun()
            else:
                st.error("Invalid username or password")
                
    st.stop()  # Останавливаем выполнение скрипта для неавторизованных

else:
    # Пользователь авторизован — собираем меню из твоих файлов
    pages = [
        st.Page(render_hub_dashboard, title="Main Dashboard", icon="📦", default=True),
        st.Page("views/1_📅_Schedule_Planner.py", title="Schedule Planner", icon="📅"),
        st.Page("views/2_⏱_Hours_Tracker.py", title="Hours Tracker", icon="⏱"),
        st.Page("views/3_👥_Workers_Management.py", title="Workers Management", icon="👥"),
        st.Page("views/4_📊_Weekly_Report.py", title="Weekly Report", icon="📊"),
        st.Page("views/5_✈️_Vacations_&_Day_offs.py", title="Vacations & Day Offs", icon="✈️"),
    ]
    
    # Кнопка Logout внизу бокового меню
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state["authenticated"] = False
        cookie_manager.delete(cookie="warehouse_auth_token")
        if "initial_cookie_sync" in st.session_state:
            del st.session_state["initial_cookie_sync"]
        st.rerun()

    # Запуск безопасного роутера страниц
    pg = st.navigation(pages)
    pg.run()