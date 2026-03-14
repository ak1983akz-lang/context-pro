import streamlit as st
import requests

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️", layout="centered")

# Session state
if "jur" not in st.session_state:
    st.session_state.jur = "🇷🇺 РФ"

# Заголовок — только название, без переключателей
st.title("⚖️ Context.Pro Legal")
st.caption("Анализ договоров • РФ / РБ")

# === САЙДБАР — единственное место для настроек ===
with st.sidebar:
    st.markdown("### ⚙️ Настройки")
    st.session_state.jur = st.radio("Юрисдикция:", ["🇷🇺 РФ", "🇧🇾 РБ"])
    st.markdown("---")
    if st.button("🗑️ Очистить всё", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    st.caption("🔒 Все данные обрабатываются конфиденциально")

# === ПРОМПТЫ ===
def get_prompt(jur, mode):
    base = "ГК РФ и законы РФ" if "РФ" in jur else "ГК РБ и законы РБ"
    if mode == "contract":
        return f"Ты юрист ({base}). Проанализируй договор: найди риски, укажи статьи, дай рекомендации. Будь краток."
    return f"Ты юрист ({base}). Ответь на вопрос со ссылками на статьи. Будь краток."

# === ЗАПРОС К AI ===
def ask_ai(prompt, text):
    try:
        key = st.secrets.get("openrouter", {}).get("api_key")
        if not key:
            return None, "❌ Нет API ключа в secrets.toml"
        
        for attempt in range(2):
            try:
                r = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": "qwen/qwen-2.5-7b-instruct",
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": text}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1200
                    },
                    timeout=90
                )
                if r.status_code == 401:
                    return None, "❌ Неверный API ключ"
                if r.status_code == 429:
                    return None, "⏳ Лимит запросов. Подождите 1 минуту."
                if r.status_code != 200:
                    return None, f"❌ Ошибка {r.status_code}"
                return r.json()["choices"][0]["message"]["content"], None
            except requests.exceptions.Timeout:
                if attempt == 0:
                    continue
                return None, "⏱ Тайм-аут. Проверьте интернет."
            except requests.exceptions.ConnectionError:
                return None, "🔌 Нет соединения с сервером."
    except Exception as e:
        return None, f"❌ {type(e).__name__}"

# === ВКЛАДКИ ===
tab_contract, tab_question = st.tabs(["📋 Договор", "💬 Вопрос"])

# ▼▼▼ ВКЛАДКА: ДОГОВОР ▼▼▼
with tab_contract:
    st.markdown("#### 📄 Вставьте текст договора")
    st.caption("💡 Минимум 50 символов")
    
    txt = st.text_area("Текст договора:", height=200, key="c_txt", placeholder="Скопируйте текст договора...")
    
    if st.button("⚖️ Проверить договор", key="c_btn"):
        if not txt or len(txt.strip()) < 50:
            st.warning("📋 Введите минимум 50 символов")
        else:
            # Простой стандартный спиннер — БЕЗ кастомной анимации
            with st.spinner("Анализирую договор..."):
                prompt = get_prompt(st.session_state.jur, "contract")
                res, err = ask_ai(prompt, txt)
                if err:
                    st.error(err)
                else:
                    st.success("✅ Анализ завершён")
                    st.markdown(res)
                    st.download_button("📥 Скачать результат", res, "analysis.txt", "text/plain")

# ▼▼▼ ВКЛАДКА: ВОПРОС ▼▼▼
with tab_question:
    st.markdown("#### ⚖️ Задайте юридический вопрос")
    st.caption("💡 Минимум 10 символов")
    
    q = st.text_area("Ваш вопрос:", height=200, key="q_txt", placeholder="Например: Какие риски по ст. 651 ГК РФ?")
    
    if st.button("⚡ Получить ответ", key="q_btn"):
        if not q or len(q.strip()) < 10:
            st.warning("💬 Введите минимум 10 символов")
        else:
            # Простой стандартный спиннер — БЕЗ кастомной анимации
            with st.spinner("Готовлю ответ..."):
                prompt = get_prompt(st.session_state.jur, "question")
                res, err = ask_ai(prompt, q)
                if err:
                    st.error(err)
                else:
                    st.success("✅ Ответ готов")
                    st.markdown(res)

# === ФУТЕР — нейтральный дисклеймер ===
st.markdown("---")
st.caption("Инструмент предварительного анализа • Для официальной консультации обратитесь к юристу • Конфиденциально")
