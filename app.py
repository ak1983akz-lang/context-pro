import streamlit as st
import requests
import re

# =============================================================================
# 🏛 CONTEXT.PRO LEGAL — v1.0 CLEAN EDITION
# ✅ Без сложного CSS | ✅ Без спортивных спиннеров | ✅ Всё на главном
# =============================================================================

st.set_page_config(
    page_title="Context.Pro Legal",
    page_icon="⚖️",
    layout="centered"
)

# --- SESSION STATE ---
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = "🇷🇺 РФ"
if 'contract_txt' not in st.session_state:
    st.session_state.contract_txt = ""
if 'question_txt' not in st.session_state:
    st.session_state.question_txt = ""
if 'result' not in st.session_state:
    st.session_state.result = ""
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = None

# =============================================================================
# 🔒 ВАЛИДАЦИЯ
# =============================================================================
def validate_input(text: str, mode: str):
    text = text.strip()
    if not text:
        return False, "⚠️ Поле не может быть пустым"
    if len(set(text.lower())) < 5 or not re.search(r'[а-яА-Яa-zA-Z]', text):
        return False, "⚠️ Введите осмысленный текст"
    if mode == "contract":
        if len(text) < 50:
            return False, "📋 Для анализа договора нужно минимум 50 символов"
        markers = ["договор", "контракт", "сторона", "обязательство", "статья", "ГК", "ФЗ", "пункт", "аренда", "оплата"]
        if not any(m in text.lower() for m in markers):
            return False, "🔍 Это не похоже на договор. Перейдите во вкладку «Вопрос»"
    elif mode == "question":
        if len(text) < 10:
            return False, "💬 Нужно минимум 10 символов"
    return True, ""

# =============================================================================
# 🧠 ПРОМПТЫ
# =============================================================================
def build_prompt(jur: str, mode: str) -> str:
    jur_base = "Российская Федерация (ГК РФ, ФЗ)" if "РФ" in jur else "Республика Беларусь (ГК РБ, Декреты)"
    if mode == "contract":
        return f"""Ты — ИИ-помощник юриста. Юрисдикция: {jur_base}.
Найди риски в договоре. Укажи: [Риск] → [Статья] → [Рекомендация].
Если текст не договор — скажи об этом."""
    else:
        return f"""Ты — ИИ-консультант по праву. Юрисдикция: {jur_base}.
Ответь на вопрос со ссылками на статьи. Структура: Суть → Нормы → Рекомендации."""

# =============================================================================
# 🔑 API
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return None

def query_ai(prompt: str, text: str):
    key = get_api_key()
    if not key:
        return None, "❌ API ключ не настроен"
    try:
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
                "max_tokens": 1500
            },
            timeout=60
        )
        if r.status_code != 200:
            return None, f"❌ Ошибка {r.status_code}"
        data = r.json()
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"], None
        return None, "❌ Пустой ответ"
    except Exception as e:
        return None, f"❌ {type(e).__name__}"

# =============================================================================
# 🎨 UI — ЧИСТЫЙ STREAMLIT (БЕЗ АГРЕССИВНОГО CSS)
# =============================================================================

# Заголовок
st.title("⚖️ Context.Pro Legal")
st.caption("Анализ договоров • Консультации • РФ/РБ")

st.divider()

# === ГЛАВНЫЙ ЭКРАН: ЮРИСДИКЦИЯ ===
st.subheader("🌍 Юрисдикция")
jur = st.radio(
    "Выберите законодательство:",
    ["🇷🇺 РФ", "🇧🇾 РБ"],
    horizontal=True,
    key="jur_radio"
)
st.session_state.jurisdiction = jur

st.divider()

# === ВКЛАДКИ ===
tab_contract, tab_question = st.tabs(["📋 Анализ договора", "💬 Юридический вопрос"])

# -------------------------------------------------------------------------
# ВКЛАДКА 1: ДОГОВОР
# -------------------------------------------------------------------------
with tab_contract:
    st.session_state.last_mode = "contract"
    
    st.text_area(
        "Текст договора:",
        value=st.session_state.contract_txt,
        height=200,
        key="contract_area",
        placeholder="Вставьте текст договора для анализа рисков..."
    )
    
    # Кнопки в ряд
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("⚖️ Проверить договор", use_container_width=True, type="primary", key="btn_contract"):
            text = st.session_state.get("contract_area", "")
            ok, msg = validate_input(text, "contract")
            if not ok:
                st.warning(msg)
            else:
                with st.spinner("⏳ Анализирую договор..."):
                    result, err = query_ai(build_prompt(jur, "contract"), text)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.result = result
                        st.success("✅ Анализ завершён")
    
    with col2:
        if st.button("🗑️ Очистить", use_container_width=True, key="clear_contract"):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    # Результат
    if st.session_state.result and st.session_state.last_mode == "contract":
        st.markdown("### 📋 Результат:")
        st.write(st.session_state.result)
        st.download_button(
            "📥 Скачать",
            st.session_state.result,
            "analysis.txt",
            "text/plain",
            use_container_width=True,
            key="dl_contract"
        )

# -------------------------------------------------------------------------
# ВКЛАДКА 2: ВОПРОС
# -------------------------------------------------------------------------
with tab_question:
    st.session_state.last_mode = "question"
    
    st.text_area(
        "Ваш вопрос:",
        value=st.session_state.question_txt,
        height=200,
        key="question_area",
        placeholder="Задайте юридический вопрос..."
    )
    
    # Кнопки в ряд
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("⚡ Получить ответ", use_container_width=True, type="primary", key="btn_question"):
            text = st.session_state.get("question_area", "")
            ok, msg = validate_input(text, "question")
            if not ok:
                st.warning(msg)
            else:
                with st.spinner("⏳ Готовлю ответ..."):
                    result, err = query_ai(build_prompt(jur, "question"), text)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.result = result
                        st.success("✅ Ответ готов")
    
    with col2:
        if st.button("🗑️ Очистить", use_container_width=True, key="clear_question"):
            st.session_state.question_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    # Результат
    if st.session_state.result and st.session_state.last_mode == "question":
        st.markdown("### 💬 Ответ:")
        st.write(st.session_state.result)

# =============================================================================
# 📎 FOOTER
# =============================================================================
st.divider()
st.caption("⚖️ Context.Pro Legal | 🇷🇺 РФ • 🇧🇾 РБ | Приватно • Без логов")
st.caption("⚠️Программа не заменяет очную консультацию юриста")
