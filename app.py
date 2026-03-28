import streamlit as st
import requests
import re
import os
import time
import PyPDF2 # Библиотека для чтения PDF (нужно добавить в requirements.txt)
import io

# =============================================================================
# 📱 PWA MANIFEST
# =============================================================================
pwa_manifest = """
<link rel="manifest" href="application/manifest+json,{
    &quot;name&quot;: &quot;Context.Pro Legal&quot;,
    &quot;short_name&quot;: &quot;ContextPro&quot;,
    &quot;description&quot;: &quot;AI-анализ договоров РФ и РБ&quot;,
    &quot;start_url&quot;: &quot;/&quot;,
    &quot;display&quot;: &quot;standalone&quot;,
    &quot;background_color&quot;: &quot;#0e1117&quot;,
    &quot;theme_color&quot;: &quot;#1f77b4&quot;,
    &quot;orientation&quot;: &quot;portrait&quot;,
    &quot;icons&quot;: [{
        &quot;src&quot;: &quot;https://cdn-icons-png.flaticon.com/512/3094/3094427.png&quot;,
        &quot;sizes&quot;: &quot;512x512&quot;,
        &quot;type&quot;: &quot;image/png&quot;
    }]
}">
<meta name="theme-color" content="#1f77b4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Context.Pro">
<link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/3094/3094427.png">
"""
st.markdown(pwa_manifest, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INIT
# =============================================================================
defaults = {
    'contract_txt': "",
    'question_txt': "",
    'result': "",
    'is_analyzing': False,
    'last_mode': None,
    'jurisdiction': "🇷🇺 РФ",
    'history': [], # История сессии
    'show_rules': False
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================================================
# 🛠 ФУНКЦИИ (OCR пока эмулируем, но добавим загрузчик PDF)
# =============================================================================

def extract_text_from_pdf(uploaded_file):
    """Извлекает текст из загруженного PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"⚠️ Ошибка чтения PDF: {str(e)}"

# def ocr_image(image_file):
#     """
#     ЗАГОТОВКА ДЛЯ OCR (Распознавание фото).
#     Чтобы это работало, на сервере должны быть установлены:
#     1. Tesseract OCR (системная утилита)
#     2. Библиотека pytesseract и pillow
#     Сейчас возвращает заглушку, так как на стандартном Streamlit Cloud это не работает без донастроек.
#     """
#     return "⚠️ Распознавание фото требует настройки сервера. Пожалуйста, скопируйте текст вручную или загрузите текстовый PDF."

# =============================================================================
# 🔒 ВАЛИДАЦИЯ
# =============================================================================
def validate_input(text: str, mode: str):
    text = text.strip()
    if not text:
        return False, "⚠️ Поле не может быть пустым"
    # Упрощенная проверка на "осмысленность"
    if len(text) < 10:
        return False, "⚠️ Слишком короткий текст"
    
    if mode == "contract":
        if len(text) < 50:
            return False, "📋 Для анализа договора нужно минимум 50 символов"
        legal_markers = ["договор", "контракт", "сторона", "обязательство", "статья", "ГК", "ФЗ", "пункт", "соглашение", "аренда", "поставка", "услуга", "оплата"]
        # Если нет явных маркеров, предупреждаем, но не блокируем (вдруг специфичный договор)
        if not any(marker in text.lower() for marker in legal_markers):
            return True, "⚠️ Внимание: Текст может не быть договором, но мы попробуем проанализировать." 
    return True, ""

# =============================================================================
# 🧠 ПРОМПТЫ
# =============================================================================
def build_system_prompt(jur: str, mode: str) -> str:
    jur_base = "Российская Федерация (ГК РФ, ФЗ, практика ВС РФ)" if "РФ" in jur else "Республика Беларусь (ГК РБ, Декреты, практика ВС РБ)"
    
    base_rules = "Ты — профессиональный ИИ-помощник юриста Context.Pro Legal. Отвечай строго, по делу, без воды. Используй маркированные списки."
    
    if mode == "contract":
        return f"""{base_rules}
Юрисдикция: {jur_base}.
ЗАДАЧА: Проанализируй текст договора.
СТРУКТУРА ОТВЕТА:
1. ### 🔍 Ключевые риски (с указанием статей закона и уровня опасности 🔴/🟡/🟢)
2. ### ✅ Что составлено грамотно
3. ### 📝 Рекомендации по изменению пунктов
4. ### ⚖️ Итоговый вердикт (Безопасно / Требует правок / Опасно)
Если текст не похож на договор, сразу напиши об этом."""
    else:
        return f"""{base_rules}
Юрисдикция: {jur_base}.
ЗАДАЧА: Дать юридическую консультацию.
СТРУКТУРА ОТВЕТА:
1. 📌 **Суть вопроса** (кратко)
2. ⚖️ **Нормативная база** (конкретные статьи ГК, ФЗ, кодексов)
3. 🔄 **Практическое решение** (пошаговый алгоритм действий)
4. ⚠️ **Подводные камни** (нюансы судебной практики)
В конце добавь дисклеймер: 'Ответ носит информационный характер'."""

# =============================================================================
# 🔑 API KEY & REQUEST
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets and "api_key" in st.secrets["openrouter"]:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return os.getenv("OPENROUTER_API_KEY")

def query_ai(system_prompt: str, user_text: str):
    api_key = get_api_key()
    if not api_key:
        return None, "❌ Ошибка конфигурации: Не найден API ключ."
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}", 
                "Content-Type": "application/json", 
                "HTTP-Referer": "https://context-pro.streamlit.app", 
                "X-Title": "Context.Pro Legal"
            },
            json={
                "model": "deepseek/deepseek-chat", # Или другая модель, например 'meta-llama/llama-3-70b-instruct'
                "messages": [
                    {"role": "system", "content": system_prompt}, 
                    {"role": "user", "content": user_text}
                ], 
                "temperature": 0.2, 
                "max_tokens": 2000, 
                "top_p": 0.9
            },
            timeout=90
        )
        if response.status_code != 200:
            return None, f"❌ Ошибка сервиса ({response.status_code})"
        
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return None, "❌ Пустой ответ от нейросети"
            
        return data["choices"][0]["message"]["content"], None
    except requests.exceptions.Timeout:
        return None, "⏱ Превышено время ожидания. Попробуйте сократить текст."
    except Exception as e:
        return None, f"❌ Ошибка соединения: {type(e).__name__}"

# =============================================================================
# 🎨 UI — CSS & STYLING
# =============================================================================
st.markdown("""
<style>
/* Основные цвета и шрифты */
.stApp { background: #0e1117; color: #fafafa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.stTextArea textarea { background: #1e2329; color: #fff; border: 1px solid #333; font-size: 16px !important; }
.stButton>button { 
    background: linear-gradient(90deg, #1f77b4, #2c8ad6); 
    color: white; font-weight: bold; 
    border: none; border-radius: 8px; 
    height: 50px; font-size: 16px; 
    transition: all 0.3s;
}
.stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(31, 119, 180, 0.4); }
.stButton>button:disabled { background: #444; color: #888; transform: none; }

/* Заголовки */
h1 { font-size: 1.8rem !important; color: #fff; margin-bottom: 0.5rem !important; }
h2, h3, h4 { color: #ddd; }

/* Блок правил (аккуратный) */
.rules-box {
    background: #161b22; border-left: 4px solid #1f77b4; padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 20px;
}
.rule-item { display: flex; align-items: start; margin-bottom: 10px; font-size: 0.95rem; }
.rule-icon { margin-right: 10px; min-width: 24px; }

/* Анимация загрузки */
@keyframes pulse-gold { 
    0%, 100% { opacity: 1; } 50% { opacity: 0.6; } 
}
.loading-box {
    background: #1a233a; border: 1px dashed #D4AF37; color: #D4AF37;
    padding: 20px; border-radius: 10px; text-align: center; font-weight: bold;
    animation: pulse-gold 1.5s infinite;
}

/* Мобильная адаптация */
@media (max-width: 768px) {
    .block-container { padding-top: 1rem !important; }
    h1 { font-size: 1.4rem !important; }
    .stButton>button { width: 100%; }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🏗 СТРУКТУРА ПРИЛОЖЕНИЯ
# =============================================================================

# 1. ШАПКА
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("⚖️ Context.Pro Legal")
    st.caption("Анализ договоров • Консультации • РФ/РБ")
with col_h2:
    # Кнопка вызова правил
    if st.button("❓ Правила", use_container_width=True, key="btn_rules_toggle"):
        st.session_state.show_rules = not st.session_state.show_rules

# 2. БЛОК ПРАВИЛ (Скрытый/Раскрывающийся)
if st.session_state.show_rules:
    st.markdown("""
    <div class="rules-box">
        <h3 style="margin-top:0;">📜 Правила сервиса</h3>
        <div class="rule-item"><span class="rule-icon">1️⃣</span><span>Выберите юрисдикцию (РФ или РБ). Это критически важно для ссылок на законы.</span></div>
        <div class="rule-item"><span class="rule-icon">2️⃣</span><span>Загрузите документ (PDF) или вставьте текст договора.</span></div>
        <div class="rule-item"><span class="rule-icon">3️⃣</span><span>Для фото-документов: используйте встроенное распознавание текста в телефоне (Live Text), затем вставляйте текст сюда.</span></div>
        <div class="rule-item"><span class="rule-icon">4️⃣</span><span>Нажмите «Анализировать». ИИ проверит риски за 15-30 секунд.</span></div>
        <div class="rule-item"><span class="rule-icon">🔒</span><span>Ваши данные не сохраняются на сервере после завершения сессии.</span></div>
    </div>
    """, unsafe_allow_html=True)

# 3. НАСТРОЙКИ (Юрисдикция)
st.markdown("### ⚙️ Настройки анализа")
jur = st.radio(
    "Законодательство:",
    ["🇷🇺 РФ (Россия)", "🇧🇾 РБ (Беларусь)"],
    horizontal=True,
    index=0,
    label_visibility="collapsed",
    key="jur_radio"
)
st.session_state.jurisdiction = "🇷🇺 РФ" if "РФ" in jur else "🇧🇾 РБ"
st.divider()

# 4. ВКЛАДКИ
tab_doc, tab_q = st.tabs(["📄 Анализ документа", "💬 Юридический вопрос"])

# --- ВКЛАДКА 1: ДОКУМЕНТ ---
with tab_doc:
    st.markdown("#### 📤 Загрузка или ввод текста")
    
    # Загрузчик файлов
    uploaded_file = st.file_uploader(
        "Загрузить договор (PDF, TXT)", 
        type=["pdf", "txt"], 
        help="Поддерживаются текстовые PDF. Фотографии пока нужно конвертировать в текст через телефон.",
        key="file_uploader_contract"
    )
    
    # Логика обработки файла
    file_text = ""
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            with st.spinner("📖 Читаю PDF..."):
                file_text = extract_text_from_pdf(uploaded_file)
                if file_text.startswith("⚠️"):
                    st.error(file_text)
                    file_text = ""
                else:
                    st.success(f"✅ Извлечено {len(file_text)} символов из PDF")
        elif uploaded_file.type == "text/plain":
            file_text = uploaded_file.read().decode("utf-8")
            st.success("✅ Текстовый файл загружен")
        
        # Автозаполнение поля, если файл прочитан успешно и поле пустое
        if file_text and not st.session_state.contract_txt:
            st.session_state.contract_txt = file_text

    # Поле ввода текста (ручное или из файла)
    contract_text = st.text_area(
        "Текст договора:", 
        value=st.session_state.contract_txt, 
        height=300, 
        key="area_contract",
        placeholder="Вставьте текст сюда или загрузите файл выше..."
    )
    
    # Синхронизация состояния
    if contract_text != st.session_state.contract_txt:
        st.session_state.contract_txt = contract_text

    # Кнопки управления
    c1, c2 = st.columns([3, 1])
    with c1:
        analyze_btn = st.button("🚀 Проверить договор", use_container_width=True, type="primary", disabled=st.session_state.is_analyzing or len(contract_text.strip()) < 10)
    with c2:
        if st.button("🗑️ Очистить", use_container_width=True):
            st.session_state.contract_txt = ""
            st.session_state.result = ""
            st.rerun()

    # ЛОГИКА АНАЛИЗА
    if analyze_btn:
        is_valid, msg = validate_input(contract_text, "contract")
        if not is_valid and "Внимание" in msg:
             st.warning(msg) # Предупреждение, но не стоп
        elif not is_valid:
            st.error(msg)
        else:
            if "Внимание" not in msg: st.info("✅ Текст принят в работу")
            
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            
            # Индикатор загрузки
            progress_bar = st.progress(0)
            status_text = st.empty()
            loader = st.markdown('<div class="loading-box">⚖️ ИИ изучает пункты договора...</div>', unsafe_allow_html=True)
            
            # Имитация прогресса для красоты
            for i in range(10):
                time.sleep(0.1)
                progress_bar.progress((i + 1) * 10)
                status_text.text("Связь с нейросетью...")
            
            sys_prompt = build_system_prompt(st.session_state.jurisdiction, "contract")
            result, error = query_ai(sys_prompt, contract_text)
            
            progress_bar.progress(100)
            loader.empty()
            status_text.empty()
            st.session_state.is_analyzing = False
            
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                # Сохраняем в историю
                st.session_state.history.insert(0, {"type": "Договор", "preview": contract_text[:50]+"...", "res": result})
                st.rerun()

    # ВЫВОД РЕЗУЛЬТАТА
    if st.session_state.last_mode == "contract" and st.session_state.result:
        st.markdown("### 📊 Результаты анализа")
        st.markdown(st.session_state.result)
        
        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            st.download_button("📥 Скачать отчет (.txt)", st.session_state.result, "legal_analysis.txt", "text/plain", use_container_width=True)
        with c_dl2:
            st.copy_to_clipboard(st.session_state.result) # Кнопка копирования (новая фича Streamlit)
            st.button("📋 Копировать текст", use_container_width=True)

# --- ВКЛАДКА 2: ВОПРОС ---
with tab_q:
    st.markdown("#### 💬 Ваш вопрос юристу")
    q = st.text_area(
        "Опишите ситуацию:", 
        value=st.session_state.question_txt, 
        height=200, 
        key="area_question",
        placeholder="Например: Можно ли расторгнуть договор аренды в одностороннем порядке?"
    )
    st.session_state.question_txt = q
    
    ask_btn = st.button("⚡ Получить консультацию", use_container_width=True, type="primary", disabled=st.session_state.is_analyzing or len(q.strip()) < 5)
    
    if ask_btn:
        st.session_state.is_analyzing = True
        st.session_state.last_mode = "question"
        
        loader = st.markdown('<div class="loading-box">🧠 Формулирую ответ на основе законов...</div>', unsafe_allow_html=True)
        
        sys_prompt = build_system_prompt(st.session_state.jurisdiction, "question")
        result, error = query_ai(sys_prompt, q)
        
        loader.empty()
        st.session_state.is_analyzing = False
        
        if error:
            st.error(error)
        else:
            st.session_state.result = result
            st.session_state.history.insert(0, {"type": "Вопрос", "preview": q[:50]+"...", "res": result})
            st.rerun()

    if st.session_state.last_mode == "question" and st.session_state.result:
        st.markdown("### 💡 Консультация")
        st.markdown(st.session_state.result)
        st.copy_to_clipboard(st.session_state.result)
        st.button("📋 Копировать ответ", use_container_width=True)

# =============================================================================
# FOOTER & HISTORY
# =============================================================================
st.divider()

# Блок истории (только если есть записи)
if st.session_state.history:
    with st.expander("🕒 История текущей сессии", expanded=False):
        for i, item in enumerate(st.session_state.history):
            with st.chat_message("user" if "Вопрос" in item['type'] else "assistant"):
                st.write(f"**{item['type']}**: {item['preview']}")
                # Можно добавить кнопку "Показать снова", но пока просто список

st.markdown("""
<div style="text-align: center; color: #555; font-size: 0.8rem; margin-top: 20px;">
    <p>⚖️ Context.Pro Legal AI | Версия 2.0 (Mobile Optimized)</p>
    <p>Не является публичной офертой. Не заменяет живого юриста.</p>
</div>
""", unsafe_allow_html=True)
