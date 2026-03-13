import streamlit as st
import requests

st.set_page_config(
    page_title="Context.Pro", 
    page_icon="⚖️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- УЛУЧШЕННЫЙ ДИЗАЙН (с мобильной адаптацией) ---
st.markdown("""
<style>
    /* Основной фон */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
        padding: 10px;
    }
    
    /* Заголовок */
    .flags {
        font-size: 2.5rem; 
        text-align: center;
        margin: 10px 0;
    }
    .title {
        font-size: 1.6rem; 
        font-weight: bold; 
        color: #1a1a2e; 
        text-align: center;
        margin-bottom: 5px;
    }
    .subtitle {
        text-align: center;
        color: #555;
        font-size: 0.9rem;
        margin-bottom: 20px;
        padding: 0 10px;
    }
    
    /* Поля ввода — адаптивные */
    .stTextArea {
        margin: 10px 0;
    }
    .stTextArea textarea {
        font-size: 16px !important;  /* Чтобы не зумило на iPhone */
        min-height: 200px;
    }
    
    /* Кнопки — большие для пальца */
    .stButton button {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
        color: white !important;
        border: none;
        padding: 15px 30px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 16px;
        width: 100%;
        cursor: pointer;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #2c5282 0%, #1e3a5f 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
    }
    
    /* Результат — ЧЁТКИЙ КОНТРАСТ */
    .result {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #1e3a5f;
        margin: 20px 0;
        box-shadow: 0 3px 10px rgba(0,0,0,0.15);
        color: #1a1a2e !important;
        font-size: 15px;
        line-height: 1.6;
    }
    .result * {
        color: #1a1a2e !important;
    }
    .result h1, .result h2, .result h3 {
        color: #1e3a5f !important;
        margin-top: 15px;
    }
    .result p {
        color: #2d3748 !important;
        margin: 10px 0;
    }
    .result ul, .result ol {
        color: #2d3748 !important;
        padding-left: 20px;
    }
    .result strong {
        color: #1e3a5f !important;
    }
    
    /* Риски */
    .risk-high {
        background: #fff0f0;
        border-left: 4px solid #e53e3e;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
        color: #742a2a !important;
    }
    .risk-med {
        background: #fffaf0;
        border-left: 4px solid #ed8936;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
        color: #744210 !important;
    }
    
    /* Сайдбар */
    .sidebar-content {
        background: #1a1a2e;
        color: white;
    }
    
    /* Футер */
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.75rem;
        padding: 20px 10px;
        border-top: 1px solid #ddd;
        margin-top: 30px;
    }
    
    /* Мобильная адаптация */
    @media (max-width: 768px) {
        .main {
            padding: 5px;
        }
        .title {
            font-size: 1.4rem;
        }
        .flags {
            font-size: 2rem;
        }
        .stTextArea textarea {
            font-size: 16px !important;
        }
        .result {
            padding: 15px;
            font-size: 14px;
        }
    }
    
    /* Скрываем меню Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
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

# --- HEADER ---
st.markdown('<div class="flags">🇷🇺 &nbsp; ⚖️ &nbsp; 🇧🇾</div>', unsafe_allow_html=True)
st.markdown('<div class="title">Context.Pro Legal</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Анализ договоров • Консультации • РФ/РБ</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Настройки")
    jur = st.radio("Законы:", ["РФ", "РБ"], horizontal=True, index=1)
    st.markdown("---")
    if st.button("🗑️ Очистить всё", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.markdown("---")
    st.caption("🔒 Данные не сохраняются")

# --- ВКЛАДКИ ---
tab1, tab2 = st.tabs(["🔍 Договор", "⚡ Вопрос"])

# --- ТАБ 1: ДОГОВОР ---
with tab1:
    st.markdown("#### 📄 Текст договора")
    txt = st.text_area(
        "Вставьте текст договора:",
        height=200,
        key="contract_txt",
        placeholder="Скопируйте сюда текст договора..."
    )
    if st.button("🔍 Проверить договор", use_container_width=True):
        if not txt.strip():
            st.warning("⚠️ Введите текст договора")
        else:
            with st.spinner("🤖 Анализирую..."):
                sys = f"Ты юрист ({jur}). Найди риски 🔴🟡, статьи законов, как исправить. Кратко."
                res, err = query(sys, txt)
                if err:
                    st.error(err)
                else:
                    # ✅ ИСПОЛЬЗУЕМ st.markdown С ПРАВИЛЬНЫМ ОТОБРАЖЕНИЕМ
                    st.markdown(f'<div class="result">{res}</div>', unsafe_allow_html=True)
                    st.download_button(
                        "📥 Скачать результат",
                        res,
                        "result.txt",
                        "text/plain",
                        use_container_width=True
                    )
    if st.button("🗑️ Очистить поле", key="clear_c"):
        st.session_state.contract_txt = ""
        st.rerun()

# --- ТАБ 2: ВОПРОС ---
with tab2:
    st.markdown("#### ⚖️ Ваш вопрос")
    q = st.text_area(
        "Задайте вопрос юристу:",
        height=180,
        key="question_txt",
        placeholder="Например: Что делать если заказчик не платит?"
    )
    if st.button("⚡ Получить ответ", use_container_width=True):
        if not q.strip():
            st.warning("⚠️ Введите вопрос")
        else:
            with st.spinner("🤖 Готовлю ответ..."):
                sys = f"Ты юрист ({jur}). Ответь со статьями законов. Пошагово. Кратко."
                res, err = query(sys, q)
                if err:
                    st.error(err)
                else:
                    # ✅ ИСПОЛЬЗУЕМ st.markdown С ПРАВИЛЬНЫМ ОТОБРАЖЕНИЕМ
                    st.markdown(f'<div class="result">{res}</div>', unsafe_allow_html=True)
    if st.button("🗑️ Очистить поле", key="clear_q"):
        st.session_state.question_txt = ""
        st.rerun()

# --- FOOTER ---
st.markdown('<div class="footer">⚖️ Context.Pro | 🇷🇺 РФ • 🇧🇾 РБ | Приватно • Без логов</div>', unsafe_allow_html=True)
