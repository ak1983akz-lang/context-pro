import streamlit as st
import requests
import re

st.set_page_config(page_title="Context.Pro Legal", page_icon="⚖️", layout="centered")

# Session state
for key in ['contract_txt', 'question_txt', 'result', 'is_analyzing', 'last_mode', 'jurisdiction']:
    if key not in st.session_state:
        st.session_state[key] = "" if key in ['contract_txt', 'question_txt', 'result', 'jurisdiction'] else False if key == 'is_analyzing' else None

# Минимальный CSS - только тёмная тема
st.markdown("""
<style>
.stApp { background-color: #0e1117; color: #fafafa; }
.stTextArea textarea { background-color: #262730; color: #fafafa; }
.stTextInput input { background-color: #262730; color: #fafafa; }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.title("⚖️ Context.Pro Legal")
st.caption("Анализ договоров • Консультации • РФ/РБ")

# Сайдбар
with st.sidebar:
    st.markdown("### ⚙️ Настройки")
    jurisdiction = st.radio("⚖️ Юрисдикция:", ["🇷🇺 РФ", "🇧🇾 РБ"], index=0, key="jur_radio")
    st.session_state.jurisdiction = jurisdiction
    st.markdown("---")
    if st.button("🗑️ Очистить всё", use_container_width=True, key="clear_all"):
        for k in ['contract_txt', 'question_txt', 'result', 'last_mode']:
            st.session_state[k] = ""
        st.session_state.is_analyzing = False
        st.rerun()
    st.caption("🔒 Приватно • Без логов")

# Функции
def validate_input(text: str, mode: str):
    text = text.strip()
    if not text:
        return False, "⚠️ Поле не может быть пустым"
    if mode == "contract" and len(text) < 50:
        return False, "📋 Для анализа договора нужно минимум 50 символов"
    if mode == "question" and len(text) < 10:
        return False, "💬 Нужно минимум 10 символов"
    if mode == "contract":
        markers = ["договор", "контракт", "сторона", "обязательство", "статья", "ГК", "ФЗ", "пункт"]
        if not any(m in text.lower() for m in markers):
            return False, "🔍 Это не похоже на договор. Перейдите во вкладку «💬 Вопрос»"
    return True, ""

def build_prompt(jur: str, mode: str):
    jur_base = "РФ (ГК РФ, ФЗ)" if "РФ" in jur else "РБ (ГК РБ, Декреты)"
    if mode == "contract":
        return f"Ты юрист ({jur_base}). Найди риски, статьи, рекомендации. Формат: ### Риски ### Рекомендации"
    else:
        return f"Ты юрист ({jur_base}). Ответь со статьями. Структура: Суть → Нормы → Рекомендации"

def query_ai(sys_prompt: str, user_text: str):
    try:
        if "openrouter" not in st.secrets:
            return None, "❌ API ключ не настроен"
        key = st.secrets["openrouter"]["api_key"]
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "deepseek/deepseek-chat", "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_text}
            ], "temperature": 0.2, "max_tokens": 1500},
            timeout=60
        )
        if resp.status_code != 200:
            return None, f"❌ Ошибка {resp.status_code}"
        return resp.json()["choices"][0]["message"]["content"], None
    except Exception as e:
        return None, f"❌ {type(e).__name__}"

# Вкладки
tab_contract, tab_question = st.tabs(["📋 Анализ договора", "💬 Юридический вопрос"])

# Вкладка ДОГОВОР
with tab_contract:
    st.markdown("#### 📄 Вставьте текст договора")
    st.caption("💡 Минимум 50 символов")
    
    contract_text = st.text_area("Текст договора:", value=st.session_state.contract_txt, 
                                  height=220, key="contract_area", placeholder="Скопируйте текст договора...")
    st.session_state.contract_txt = contract_text
    
    if st.button("⚖️ Проверить договор", use_container_width=True, 
                 disabled=st.session_state.is_analyzing, key="btn_contract"):
        ok, msg = validate_input(contract_text, "contract")
        if not ok:
            st.warning(msg)
        else:
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            result, error = query_ai(build_prompt(jurisdiction, "contract"), contract_text)
            st.session_state.is_analyzing = False
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.rerun()
    
    if st.session_state.last_mode == "contract" and st.session_state.result:
        st.markdown("#### 🔍 Результаты анализа")
        st.write(st.session_state.result)
        st.download_button("📥 Скачать", st.session_state.result, "analysis.txt", "text/plain", key="dl_contract")
    
    if st.button("🗑️ Очистить поле", key="clear_contract"):
        st.session_state.contract_txt = ""
        st.session_state.result = ""
        st.session_state.last_mode = None
        st.rerun()

# Вкладка ВОПРОС
with tab_question:
    st.markdown("#### ⚖️ Задайте юридический вопрос")
    st.caption("💡 Минимум 10 символов")
    
    question_text = st.text_area("Ваш вопрос:", value=st.session_state.question_txt,
                                  height=200, key="question_area", placeholder="Сформулируйте вопрос...")
    st.session_state.question_txt = question_text
    
    if st.button("⚡ Получить ответ", use_container_width=True,
                 disabled=st.session_state.is_analyzing, key="btn_question"):
        ok, msg = validate_input(question_text, "question")
        if not ok:
            st.warning(msg)
        else:
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "question"
            result, error = query_ai(build_prompt(jurisdiction, "question"), question_text)
            st.session_state.is_analyzing = False
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.rerun()
    
    if st.session_state.last_mode == "question" and st.session_state.result:
        st.markdown("#### 💬 Консультация")
        st.write(st.session_state.result)
    
    if st.button("🗑️ Очистить поле", key="clear_question"):
        st.session_state.question_txt = ""
        st.session_state.result = ""
        st.session_state.last_mode = None
        st.rerun()

# Футер
st.markdown("---")
st.caption("⚖️ Context.Pro Legal | 🇷 РФ • 🇧 РБ | Приватно • Без логов\n\n⚠️ ИИ-помощник не заменяет очную консультацию юриста.")
