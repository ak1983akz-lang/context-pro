import streamlit as st
import requests

st.set_page_config(
    page_title="Context.Pro", 
    page_icon="⚖️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ИНИЦИАЛИЗАЦИЯ SESSION STATE ---
if 'contract_txt' not in st.session_state:
    st.session_state.contract_txt = ""
if 'question_txt' not in st.session_state:
    st.session_state.question_txt = ""
if 'result' not in st.session_state:
    st.session_state.result = ""

# --- КНОПКА МЕНЮ ДЛЯ ТЕЛЕФОНА (3 БЕЛЫЕ ПОЛОСЫ) ---
st.markdown("""
<style>
    /* СКРЫВАЕМ ВЕРХ STREAMLIT */
    .stApp > header {display: none !important;}
    header {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    
    /* СКРЫВАЕМ НИЗ */
    footer {visibility: hidden !important;}
    .stApp > footer {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
        padding: 10px;
    }
    .flags {font-size: 2.5rem; text-align: center; margin: 10px 0;}
    .title {font-size: 1.6rem; font-weight: bold; color: #1a1a2e; text-align: center;}
    .subtitle {text-align: center; color: #555; font-size: 0.9rem; margin-bottom: 20px;}
    .stTextArea textarea {font-size: 16px !important;}
    .stButton button {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        color: white !important;
        border: none;
        padding: 15px 30px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 16px;
        width: 100%;
    }
    .result {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #1e3a5f;
        margin: 20px 0;
        box-shadow: 0 3px 10px rgba(0,0,0,0.15);
        color: #1a1a2e !important;
    }
    .result * {color: #1a1a2e !important;}
    .footer {text-align: center; color: #666; font-size: 0.75rem; padding: 20px; border-top: 1px solid #ddd; margin-top: 30px;}
    
    /* ✅ КАСТОМНАЯ КНОПКА МЕНЮ - 3 БЕЛЫЕ ПОЛОСЫ */
    .mobile-menu-btn {
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 9999;
        background: #1e3a5f;
        border: none;
        border-radius: 8px;
        padding: 10px 14px;
        cursor: pointer;
        display: none;
        flex-direction: column;
        gap: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    .mobile-menu-btn span {
        display: block;
        width: 22px;
        height: 3px;
        background: white;
        border-radius: 2px;
    }
    .mobile-menu-btn:hover {
        background: #2c5282;
    }
    
    /* ПОКАЗЫВАЕМ КНОПКУ ТОЛЬКО НА МОБИЛЬНЫХ */
    @media (max-width: 768px) {
        .mobile-menu-btn {
            display: flex !important;
        }
    }
    
    /* САЙДБАР */
    section[data-testid="stSidebar"] {
        background: #1a1a2e;
        color: white;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- КНОПКА МЕНЮ (3 ПОЛОСЫ) ---
st.markdown("""
<button class="mobile-menu-btn" onclick="document.querySelector('div[data-testid="stSidebar"]').click()">
    <span></span>
    <span></span>
    <span></span>
</button>
<script>
    document.querySelector('.mobile-menu-btn').addEventListener('click', function() {
        var sidebar = document.querySelector('button[title="Close sidebar"]');
        if (sidebar) {
            sidebar.click();
        } else {
            var openBtn = document.querySelector('button[aria-label="Open sidebar"]');
            if (openBtn) openBtn.click();
        }
    });
</script>
""", unsafe_allow_html=True)

# --- КЛЮЧ ---
def get_key():
    try:
        if "openrouter" in st.secrets:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return None

# --- ЗАПРОС К ИИ ---
def query(sys_prompt, user_text):
    key = get_key()
    if not key:
        return None, "❌ API ключ не настроен"
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_text}
                ],
                "temperature": 0.2,
                "max_tokens": 1200
            },
            timeout=45
        )
        if r.status_code != 200:
            return None, f"❌ Ошибка {r.status_code}"
        data = r.json()
        if "choices" not in data or not data["choices"]:
            return None, "❌ Пустой ответ"
        return data["choices"][0]["message"]["content"], None
    except Exception as e:
        return None, f"❌ {e}"

# --- HEADER С ФЛАГАМИ ---
st.markdown('<div class="flags">🇷🇺 &nbsp; ⚖️ &nbsp; 🇧🇾</div>', unsafe_allow_html=True)
st.markdown('<div class="title">Context.Pro Legal</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Анализ договоров • Консультации • РФ/РБ</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Настройки")
    jur = st.radio(
        "Законы:",
        ["🇷🇺 РФ", "🇧🇾 РБ"],
        horizontal=False,
        index=1
    )
    st.markdown("---")
    if st.button("🗑️ Очистить всё", use_container_width=True):
        st.session_state.contract_txt = ""
        st.session_state.question_txt = ""
        st.session_state.result = ""
        st.rerun()
    st.markdown("---")
    st.caption("🔒 Данные не сохраняются")

# --- ВКЛАДКИ ---
tab1, tab2 = st.tabs(["📋 Договор", "💬 Вопрос"])

# --- ТАБ 1 ---
with tab1:
    st.markdown("#### 📄 Текст договора")
    txt = st.text_area(
        "Вставьте текст договора:",
        value=st.session_state.contract_txt,
        height=200,
        key="contract_input",
        placeholder="Скопируйте сюда текст договора..."
    )
    st.session_state.contract_txt = txt
    
    if st.button("⚖️ Проверить договор", use_container_width=True):
        if not txt.strip():
            st.warning("⚠️ Введите текст договора")
        else:
            with st.spinner("Анализ..."):
                sys = f"Ты юрист ({jur}). Найди риски, статьи законов, как исправить. Кратко."
                res, err = query(sys, txt)
                if err:
                    st.error(err)
                else:
                    st.session_state.result = res
                    st.markdown(f'<div class="result">{res}</div>', unsafe_allow_html=True)
                    st.download_button("📥 Скачать", res, "result.txt", "text/plain", use_container_width=True)
    
    if st.button("🗑️ Очистить поле", key="clear_contract"):
        st.session_state.contract_txt = ""
        st.session_state.result = ""
        st.rerun()

# --- ТАБ 2 ---
with tab2:
    st.markdown("#### ⚖️ Ваш вопрос")
    q = st.text_area(
        "Задайте вопрос юристу:",
        value=st.session_state.question_txt,
        height=180,
        key="question_input",
        placeholder="Например: Что делать если заказчик не платит?"
    )
    st.session_state.question_txt = q
    
    if st.button("⚡ Получить ответ", use_container_width=True):
        if not q.strip():
            st.warning("⚠️ Введите вопрос")
        else:
            with st.spinner("Готовлю ответ..."):
                sys = f"Ты юрист ({jur}). Ответь со статьями законов. Пошагово. Кратко."
                res, err = query(sys, q)
                if err:
                    st.error(err)
                else:
                    st.session_state.result = res
                    st.markdown(f'<div class="result">{res}</div>', unsafe_allow_html=True)
    
    if st.button("🗑️ Очистить поле", key="clear_question"):
        st.session_state.question_txt = ""
        st.session_state.result = ""
        st.rerun()

# --- FOOTER ---
st.markdown('<div class="footer">⚖️ Context.Pro | 🇷🇺 РФ • 🇧🇾 РБ | Приватно • Без логов</div>', unsafe_allow_html=True)
