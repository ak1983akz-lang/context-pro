import streamlit as st
import time

# === НАСТРОЙКА СТРАНИЦЫ И PWA ===
st.set_page_config(
    page_title="Context.Pro Legal — AI-анализ договоров",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Скрываем стандартные элементы Streamlit для вида "приложения"
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    <!-- PWA Manifest (встроенный) -->
    <link rel="manifest" href="data:application/manifest+json,{
        &quot;name&quot;: &quot;Context.Pro Legal&quot;,
        &quot;short_name&quot;: &quot;ContextPro&quot;,
        &quot;description&quot;: &quot;AI-анализ юридических договоров РФ и РБ&quot;,
        &quot;start_url&quot;: &quot;/&quot;,
        &quot;display&quot;: &quot;standalone&quot;,
        &quot;background_color&quot;: &quot;#FFFFFF&quot;,
        &quot;theme_color&quot;: &quot;#1E3A8A&quot;,
        &quot;icons&quot;: [{
            &quot;src&quot;: &quot;https://cdn-icons-png.flaticon.com/512/3094/3094427.png&quot;,
            &quot;sizes&quot;: &quot;512x512&quot;,
            &quot;type&quot;: &quot;image/png&quot;
        }]
    }">
    <meta name="theme-color" content="#1E3A8A">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# === БОКОВАЯ ПАНЕЛЬ ===
with st.sidebar:
    st.markdown("## ⚖️ Context.Pro Legal")
    st.markdown("*AI-помощник для анализа договоров*")
    st.markdown("---")
    
    # Выбор юрисдикции
    jurisdiction = st.radio(
        "🌍 Юрисдикция",
        ["🇷🇺 Российская Федерация", "🇧🇾 Республика Беларусь"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 🔐 Безопасность")
    st.info("✅ Текст не сохраняется в логах\n✅ Данные передаются по HTTPS\n✅ Сервер в РФ")
    
    st.markdown("---")
    st.markdown("### 📱 Приложение")
    # ИСПРАВЛЕНИЕ ЗДЕСЬ: убран параметр icon
    st.caption("📲 Нажми «Поделиться» → «На экран Домой»")
    
    st.markdown("---")
    st.markdown("[📄 Политика конфиденциальности](#)")

# === ОСНОВНОЙ КОНТЕНТ ===
st.title("⚖️ Проверь договор за 30 секунд")
st.markdown("""
**Context.Pro Legal** — искусственный интеллект, который найдёт риски в договоре:
- 🔴 Скрытые штрафы и неустойки
- 🟡 Нечёткие формулировки  
- 🟢 Выгодные для вас условия

> *⚠️ Важно: Результаты анализа носят информационный характер и не являются юридической консультацией. Для важных сделок обратитесь к лицензированному юристу.*
""")

# === ФОРМА ВВОДА ===
col1, col2 = st.columns([3, 1])

with col1:
    contract_text = st.text_area(
        "📋 Вставьте текст договора",
        height=250,
        placeholder="Скопируйте текст договора сюда (например, из Word или PDF)..."
    )

with col2:
    st.markdown("### 💡 Примеры вопросов")
    preset_questions = [
        "Найди скрытые штрафы",
        "Какие риски для меня как для арендатора?",
        "Можно ли расторгнуть договор без штрафов?",
        "Есть ли неустойки за просрочку?",
        "Проверь пункт о конфиденциальности"
    ]
    user_question = st.selectbox("Или выбери готовый:", ["Свой вопрос"] + preset_questions)
    
    if user_question != "Свой вопрос":
        user_question = st.text_input("Уточни вопрос:", value=user_question)
    else:
        user_question = st.text_input("Твой вопрос:", placeholder="Что проверить в договоре?")

# === СОГЛАСИЕ С ПОЛИТИКОЙ ===
agree = st.checkbox(
    "✅ Я согласен с политикой конфиденциальности и понимаю, что ИИ может ошибаться",
    key="privacy_consent"
)

# === КНОПКА АНАЛИЗА ===
if st.button("🔍 Проанализировать договор", type="primary", use_container_width=True, disabled=not agree):
    if not contract_text.strip():
        st.error("❌ Введите текст договора")
    elif not user_question.strip():
        st.error("❌ Введите вопрос для анализа")
    else:
        with st.spinner("🤖 ИИ анализирует документ... Это займёт ~15-30 секунд"):
            # === ЗДЕСЬ ТВОЯ ЛОГИКА АНАЛИЗА ===
            # Пока стоит имитация задержки. Когда подключишь API - замени этот блок.
            time.sleep(2)
            
            # === РЕЗУЛЬТАТ ===
            st.success("✅ Анализ завершён!")
            
            # Блок с рисками
            with st.expander("🔴 Найденные риски", expanded=True):
                st.markdown("""
                - **Пункт 5.2**: Штраф 50% от суммы договора — выше среднего по рынку
                - **Пункт 8.1**: Одностороннее изменение условий заказчиком
                - **Отсутствует**: Порядок возврата аванса при расторжении
                """)
            
            # Блок с рекомендациями
            with st.expander("🟢 Рекомендации по правкам"):
                st.markdown("""
                1. Предложите снизить штраф до 10-20%
                2. Добавьте пункт: "Изменение договора только по письменному согласию обеих сторон"
                3. Внесите условие возврата аванса в течение 10 дней
                """)
            
            # Ответ на вопрос
            st.markdown(f"### 💬 Ответ на вопрос: *«{user_question}»*")
            st.markdown(f"""
            На основе анализа договора и законодательства **{jurisdiction}**, ИИ рекомендует:
            > *Текст ответа от модели будет здесь...*
            
            ⚠️ **Важно**: Это автоматический анализ. Для юридически значимых выводов обратитесь к сертифицированному юристу.
            """)
            
            # Кнопка скачать
            st.download_button(
                label="📥 Скачать отчёт (демо)",
                data="Контекст: " + jurisdiction + "\n\nВопрос: " + user_question + "\n\n[Здесь будет сформированный отчет]",
                file_name="context-pro-report.txt",
                mime="text/plain"
            )

# === ПОДВАЛ ===
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    st.markdown("### 🏢 О сервисе")
    st.markdown("Context.Pro Legal — AI-инструмент для быстрой проверки договоров. Сервер в РФ, данные не сохраняются.")

with col_f2:
    st.markdown("### 📜 Документы")
    st.markdown("[Политика конфиденциальности](#)\n[Пользовательское соглашение](#)\n[Оферта](#)")

with col_f3:
    st.markdown("### 📞 Контакты")
    st.markdown("support@context-pro.ru\nTelegram: @contextpro_support")

st.markdown("---")
st.markdown("<center style='color: #666; font-size: 0.9em;'>© 2026 Context.Pro Legal. Все права защищены.</center>", unsafe_allow_html=True)
