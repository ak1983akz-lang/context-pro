import streamlit as st
import requests

st.set_page_config(page_title="Context.Pro", page_icon="⚖️", layout="centered")

st.markdown("""
<style>
    .main {background: #f8f9fa;}
    .stTextArea textarea {font-size: 1rem;}
    .stButton button {
        background: #1e3a5f; color: white; border: none;
        padding: 12px 30px; border-radius: 8px; font-weight: bold;
    }
    .stButton button:hover {background: #2c5282;}
    .result {
        background: white; padding: 20px; border-radius: 10px;
        border-left: 4px solid #1e3a5f; margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .flags {font-size: 2rem; text-align: center;}
    .title {font-size: 1.8rem; font-weight: bold; color: #1a1a2e; text-align: center;}
    .footer {
        text-align: center; color: #666; font-size: 0.8rem;
        padding: 20px; border-top: 1px solid #eee; margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)

def get_key():
    try:
        if "openrouter" in st.secrets:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return None

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

st.markdown('<div class="flags">🇷🇺 &nbsp; ⚖️ &nbsp; 🇧🇾</div>', unsafe_allow_html=True)
st.markdown('<div class="title">Context.Pro Legal</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#666;margin-bottom:30px">Анализ договоров • Консультации • РФ/РБ</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️")
    jur = st.radio("Законы:", ["РФ", "РБ"], horizontal=True, index=1)
    st.markdown("---")
    if st.button("🗑️ Очистить всё", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.markdown("---")
    st.caption("🔒 Данные не сохраняются")

tab1, tab2 = st.tabs(["🔍 Договор", "⚡ Вопрос"])

with tab1:
    txt = st.text_area("Текст договора:", height=250, key="contract_txt")
    if st.button("🔍 Проверить", use_container_width=True):
        if not txt.strip():
            st.warning("Введите текст")
        else:
            with st.spinner("Анализ..."):
                sys = f"Ты юрист ({jur}). Найди риски 🔴🟡, статьи законов, как исправить. Кратко."
                res, err = query(sys, txt)
                if err:
                    st.error(err)
                else:
                    st.markdown(f'<div class="result">{res}</div>', unsafe_allow_html=True)
                    st.download_button("📥 Скачать", res, "result.txt", "text/plain", use_container_width=True)
    if st.button("🗑️ Очистить поле", key="clear_c"):
        st.session_state.contract_txt = ""
        st.rerun()

with tab2:
    q = st.text_area("Ваш вопрос:", height=200, key="question_txt")
    if st.button("⚡ Ответить", use_container_width=True):
        if not q.strip():
            st.warning("Введите вопрос")
        else:
            with st.spinner("Думаю..."):
                sys = f"Ты юрист ({jur}). Ответь со статьями законов. Пошагово. Кратко."
                res, err = query(sys, q)
                if err:
                    st.error(err)
                else:
                    st.markdown(f'<div class="result">{res}</div>', unsafe_allow_html=True)
    if st.button("🗑️ Очистить поле", key="clear_q"):
        st.session_state.question_txt = ""
        st.rerun()

st.markdown('<div class="footer">⚖️ Context.Pro | 🇷🇺 РФ • 🇧🇾 РБ | Приватно • Без логов</div>', unsafe_allow_html=True)
