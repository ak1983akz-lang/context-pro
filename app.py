import streamlit as st
import requests

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️", layout="centered")

# Простая инициализация
if "jur" not in st.session_state:
    st.session_state.jur = "🇷🇺 РФ"

# Заголовок
st.title("⚖️ Context.Pro Legal")
st.caption("Анализ договоров • РФ / РБ")

# Сайдбар
with st.sidebar:
    st.session_state.jur = st.radio("Юрисдикция:", ["🇷🇺 РФ", "🇧🇾 РБ"])
    if st.button("🗑️ Сбросить"):
        st.session_state.clear()
        st.rerun()

# Промпты
def get_prompt(jur, mode):
    base = "ГК РФ и законы РФ" if "РФ" in jur else "ГК РБ и законы РБ"
    if mode == "contract":
        return f"Ты юрист ({base}). Проанализируй договор: найди риски, укажи статьи, дай рекомендации. Будь краток."
    return f"Ты юрист ({base}). Ответь на вопрос со ссылками на статьи. Будь краток."

# Запрос к AI
def ask_ai(prompt, text):
    try:
        key = st.secrets.get("openrouter", {}).get("api_key")
        if not key:
            return None, "❌ Нет API ключа"
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.2,
                "max_tokens": 1200
            },
            timeout=45
        )
        if r.status_code != 200:
            return None, f"❌ Ошибка {r.status_code}"
        return r.json()["choices"][0]["message"]["content"], None
    except Exception as e:
        return None, f"❌ {e}"

# Вкладки
tab1, tab2 = st.tabs(["📋 Договор", "💬 Вопрос"])

# === ВКЛАДКА: ДОГОВОР ===
with tab1:
    txt = st.text_area("Текст договора:", height=200, key="c_txt", placeholder="Вставьте текст...")
    
    if st.button("⚖️ Проверить", key="c_btn"):
        if not txt or len(txt.strip()) < 50:
            st.warning("📋 Введите минимум 50 символов")
        else:
            with st.spinner("Анализ..."):
                prompt = get_prompt(st.session_state.jur, "contract")
                res, err = ask_ai(prompt, txt)
                if err:
                    st.error(err)
                else:
                    st.success("✅ Готово")
                    st.markdown(res)
                    st.download_button("📥 Скачать", res, "result.txt", "text/plain")

# === ВКЛАДКА: ВОПРОС ===
with tab2:
    q = st.text_area("Ваш вопрос:", height=200, key="q_txt", placeholder="Задайте вопрос...")
    
    if st.button("⚡ Ответить", key="q_btn"):
        if not q or len(q.strip()) < 10:
            st.warning("💬 Введите минимум 10 символов")
        else:
            with st.spinner("Готовлю ответ..."):
                prompt = get_prompt(st.session_state.jur, "question")
                res, err = ask_ai(prompt, q)
                if err:
                    st.error(err)
                else:
                    st.success("✅ Готово")
                    st.markdown(res)

# Футер
st.markdown("---")
st.caption("⚠️ ИИ не заменяет юриста • Конфиденциально")
