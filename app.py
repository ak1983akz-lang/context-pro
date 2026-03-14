import streamlit as st
import requests
import re

# =============================================================================
# 🏛 CONTEXT.PRO LEGAL — v1.1 STABLE EDITION
# 🤖 Модель: Qwen 2.5 72B | ⏱ Тайм-аут: 120 сек | 🎨 Чистый Streamlit
# =============================================================================

st.set_page_config(
    page_title="Context.Pro Legal",
    page_icon="⚖️",
    layout="centered"
)

# --- SESSION STATE ---
for key in ['jurisdiction', 'contract_txt', 'question_txt', 'result', 'last_mode']:
    if key not in st.session_state:
        st.session_state[key] = "🇷🇺 РФ" if key == 'jurisdiction' else "" if key in ['contract_txt', 'question_txt', 'result'] else None

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
        markers = ["договор", "контракт", "сторона", "обязательство", "статья", "ГК", "ФЗ", "пункт", "аренда", "оплата", "соглашение"]
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
    jur_base = "Российская Федерация (ГК РФ, ФЗ, практика ВС РФ)" if "РФ" in jur else "Республика Беларусь (ГК РБ, Декреты, практика ВС РБ)"
    if mode == "contract":
        return f"""Ты — профессиональный ИИ-помощник юриста. Юрисдикция: {jur_base}.
ЗАДАЧА: Проанализируй договор на риски.
ФОРМАТ ОТВЕТА:
### 🔍 Выявленные риски
• [Уровень] Риск: описание → Статья закона → Рекомендация
### ✅ Что в порядке
• Пункты без нарушений
### 📋 Итог
Краткая оценка + "Результат носит рекомендательный характер"
ПРАВИЛА: Не выдумывай статьи. Если не уверен — укажи. Цитируй только реальные нормы."""
    else:
        return f"""Ты — профессиональный ИИ-консультант по праву. Юрисдикция: {jur_base}.
ЗАДАЧА: Ответь на юридический вопрос.
ФОРМАТ:
### 📌 Суть вопроса
### ⚖️ Нормативная база (статьи ГК/ФЗ/Декретов)
### 🔄 Пошаговые рекомендации
### ⚠️ Важные нюансы
ПРАВИЛА: Указывай только реальные статьи. Добавь дисклеймер в конце."""

# =============================================================================
# 🔑 API
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets and "api_key" in st.secrets["openrouter"]:
            return st.secrets["openrouter"]["api_key"].strip()
    except:
        pass
    return None

def query_ai(prompt: str, text: str):
    key = get_api_key()
    if not key:
        return None, "❌ API ключ не настроен. Проверьте .streamlit/secrets.toml"
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://context-pro.streamlit.app",
                "X-Title": "Context.Pro Legal"
            },
            json={
                "model": "qwen/qwen-2.5-72b-instruct",  # ✅ ОБНОВЛЕНО: Быстрее и стабильнее для РФ/РБ
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.2,
                "max_tokens": 1500,
                "top_p": 0.9
            },
            timeout=120  # ✅ УВЕЛИЧЕНО: 120 секунд вместо 60
        )
        
        if response.status_code != 200:
            return None, f"❌ Ошибка сервиса ({response.status_code}). Попробуйте позже."
        
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return None, "❌ Пустой ответ от сервиса"
        
        return data["choices"][0]["message"]["content"], None
        
    except requests.exceptions.Timeout:
        return None, "⏱ Тайм-аут: сервер отвечает медленно. Проверьте интернет или повторите запрос."
    except requests.exceptions.ConnectionError:
        return None, "🔌 Ошибка подключения. Проверьте интернет-соединение."
    except Exception as e:
        return None, f"❌ Ошибка: {type(e).__name__}"

# =============================================================================
# 🎨 UI — ЧИСТЫЙ STREAMLIT
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
    key="jur_radio_main"
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
        if st.button("⚖️ Проверить договор", use_container_width=True, type="primary", key="btn_contract_run"):
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
        if st.button("🗑️ Очистить", use_container_width=True, key="btn_contract_clear"):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.rerun()
    
    # Результат
    if st.session_state.result and st.session_state.last_mode == "contract":
        st.markdown("### 📋 Результат анализа:")
        st.write(st.session_state.result)
        st.download_button(
            "📥 Скачать отчёт",
            st.session_state.result,
            "context_pro_analysis.txt",
            "text/plain",
            use_container_width=True,
            key="btn_contract_download"
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
        if st.button("⚡ Получить ответ", use_container_width=True, type="primary", key="btn_question_run"):
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
        if st.button("🗑️ Очистить", use_container_width=True, key="btn_question_clear"):
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
st.caption("⚠️ ИИ-помощник не заменяет очную консультацию юриста. Результаты носят рекомендательный характер.")
