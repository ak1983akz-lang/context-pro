import streamlit as st
import requests

st.set_page_config(page_title="Context.Pro", page_icon="⚖️", layout="centered")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stSpinner > div {border-color: #1e3a5f !important;}
</style>
""", unsafe_allow_html=True)

def get_key():
    try:
        if "openrouter" in st.secrets:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return st.sidebar.text_input("🔑 API Key:", type="password")

def query(sys_prompt, user_text):
    key = get_key()
    if not key:
        return None, "❌ Введи ключ слева"
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

st.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <div style='font-size: 3rem;'>🇷🇺  ⚖️  🇧🇾</div>
    <div style='font-size: 2rem; font-weight: bold; color: #1e3a5f;'>Context.Pro Legal</div>
    <div style='color: #666;'>Профессиональный анализ договоров</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Настройки")
    jur = st.radio("Законы:", ["РФ", "РБ"], horizontal=True, index=1)
    st.markdown("---")
    if st.button("🗑️ Очистить всё", key="btn_clear_all", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.markdown("---")
    st.caption("🔒 Данные не сохраняются")

tab1, tab2 = st.tabs(["🔍 Проверка договора", "⚡ Консультация"])

with tab1:
    st.markdown("#### 📄 Анализ договора")
    txt = st.text_area("Вставьте текст договора:", height=250, key="txt_contract", 
                       placeholder="Скопируйте текст договора для анализа...")
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("🔍 Проверить", key="btn_check", type="primary", use_container_width=True):
            if not txt.strip():
                st.warning("⚠️ Введите текст договора")
            else:
                with st.spinner("⚖️ Анализирую договор..."):
                    res, err = query(f"Ты юрист ({jur}). Найди риски 🔴🟡, статьи законов, как исправить. Кратко и профессионально.", txt)
                    if err: 
                        st.error(err)
                    else: 
                        st.success("✅ Готово!")
                        st.markdown(f"<div style='background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #1e3a5f; margin: 20px 0;'>{res}</div>", unsafe_allow_html=True)
                        # 🔥 ИСПРАВЛЕНИЕ: используем bytes + UTF-8
                        st.download_button(
                            label="📥 Скачать результат",
                            data=res.encode('utf-8'),
                            file_name="analysis.txt",
                            mime="text/plain;charset=utf-8",
                            use_container_width=True
                        )
    with col2:
        if st.button("🗑️ Очистить", key="btn_clear_1", use_container_width=True):
            st.session_state.txt_contract = ""
            st.rerun()

with tab2:
    st.markdown("#### ⚖️ Юридическая консультация")
    q = st.text_area("Ваш вопрос:", height=200, key="txt_question",
                     placeholder="Опишите ситуацию или задайте вопрос...")
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("⚡ Получить ответ", key="btn_answer", type="primary", use_container_width=True):
            if not q.strip():
                st.warning("⚠️ Введите вопрос")
            else:
                with st.spinner("⚖️ Готовлю ответ..."):
                    res, err = query(f"Ты юрист ({jur}). Ответь со ссылками на статьи законов. Пошаговый план действий. Профессионально.", q)
                    if err: 
                        st.error(err)
                    else: 
                        st.success("✅ Ответ готов!")
                        st.markdown(f"<div style='background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #1e3a5f; margin: 20px 0;'>{res}</div>", unsafe_allow_html=True)
    with col2:
        if st.button("🗑️ Очистить", key="btn_clear_2", use_container_width=True):
            st.session_state.txt_question = ""
            st.rerun()

st.markdown("""
<div style='text-align: center; color: #666; padding: 30px; border-top: 1px solid #eee; margin-top: 40px;'>
    <div>⚖️ Context.Pro Legal © 2026</div>
    <div style='font-size: 0.8rem;'>🇷🇺 Российская Федерация • 🇧🇾 Республика Беларусь</div>
    <div style='font-size: 0.75rem; color: #999;'>Конфиденциально • Без сохранения данных</div>
</div>
""", unsafe_allow_html=True)
