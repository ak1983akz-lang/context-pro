import streamlit as st
import requests
import re
import os
from PIL import Image, ImageEnhance, ImageFilter

# =============================================================================
# 🔧 НАСТРОЙКА TESSERACT (для Streamlit Cloud — ЗАКОММЕНТИРОВАНО)
# =============================================================================
# import pytesseract
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# =============================================================================
# SESSION STATE
# =============================================================================
for key in ['contract_txt', 'question_txt', 'result', 'is_analyzing', 'last_mode', 'jurisdiction']:
    if key not in st.session_state:
        st.session_state[key] = "" if key in ['contract_txt', 'question_txt', 'result', 'jurisdiction'] else False

# =============================================================================
# CSS — СТИЛИ + СПИНЕР
# =============================================================================
st.markdown("""
<style>
.stApp { background: #0e1117; color: #fafafa; }
.stTextArea textarea { background: #262730; color: #fafafa; }
.stButton>button { background: #1f77b4; color: white; }

@keyframes empire-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(0.98); }
}
.empire-loading {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: #D4AF37 !important;
    font-weight: 500 !important;
    font-size: 1.1rem !important;
    animation: empire-pulse 2s infinite ease-in-out !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    background: #1a233a !important;
    border: 1px dashed #B8962E !important;
    border-radius: 8px !important;
}
.empire-loading::before {
    content: "⚖️";
    margin-right: 0.75rem !important;
    font-size: 1.4rem !important;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🔒 ВАЛИДАЦИЯ ВВОДА
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
        legal_markers = ["договор", "контракт", "сторона", "обязательство", "статья", "ГК", "ФЗ", "пункт", "параграф", "соглашение", "аренда", "поставка", "услуга", "оплата", "ответственность"]
        if not any(marker in text.lower() for marker in legal_markers):
            return False, "🔍 Это не похоже на текст договора. Перейдите во вкладку «💬 Вопрос»"
    elif mode == "question":
        if len(text) < 10:
            return False, "💬 Сформулируйте вопрос подробнее (мин. 10 символов)"
    return True, ""

# =============================================================================
# 🧠 СИСТЕМНЫЕ ПРОМПТЫ
# =============================================================================
def build_system_prompt(jur: str, mode: str) -> str:
    jur_base = "Российская Федерация (ГК РФ, ФЗ, практика ВС РФ)" if "РФ" in jur else "Республика Беларусь (ГК РБ, Декреты, практика ВС РБ)"
    if mode == "contract":
        return f"""Ты — профессиональный ИИ-помощник юриста Context.Pro Legal. Юрисдикция: {jur_base}.

ПРАВИЛА:
1. Если текст не является договором → ОТВЕТЬ: "⚠️ Это не похоже на текст договора."
2. Выдели риски: [🔴 Критический] / [🟡 Средний] / [🟢 Низкий]
3. Цитируй статьи законов (ГК РФ/РБ, ФЗ, Декреты)
4. Дай рекомендацию по исправлению
5. Не выдумывай статьи
6. ФОРМАТ: ### 🔍 Риски • ### ✅ Что в порядке • ### 📋 Итог
"""
    else:
        return f"""Ты — ИИ-консультант по праву. Юрисдикция: {jur_base}.

ПРАВИЛА:
1. Отвечай только на юридические вопросы
2. Указывай статьи ГК/ФЗ/Декретов
3. Структура: 📌 Суть → ⚖️ Нормы → 🔄 Рекомендации → ⚠️ Нюансы
4. Дисклеймер в конце
"""

# =============================================================================
# 🔑 API KEY
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets and "api_key" in st.secrets["openrouter"]:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return os.getenv("OPENROUTER_API_KEY")

# =============================================================================
# 🤖 ЗАПРОС К AI
# =============================================================================
def query_ai(system_prompt: str, user_text: str):
    api_key = get_api_key()
    if not api_key:
        return None, "❌ API ключ не настроен. Проверьте secrets.toml"
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
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "temperature": 0.2,
                "max_tokens": 1500,
                "top_p": 0.9
            },
            timeout=60
        )
        if response.status_code != 200:
            return None, f"❌ Ошибка сервиса ({response.status_code})"
        data = response.json()
        if "choices" not in data or not data["choices"]:
            return None, "❌ Пустой ответ"
        return data["choices"][0]["message"]["content"], None
    except requests.exceptions.Timeout:
        return None, "⏱ Тайм-аут соединения."
    except requests.exceptions.ConnectionError:
        return None, "🔌 Ошибка подключения."
    except Exception as e:
        return None, f"❌ Ошибка: {type(e).__name__}"

# =============================================================================
# 📷 OCR — УЛУЧШЕННОЕ РАСПОЗНАВАНИЕ С ПРЕДОБРАБОТКОЙ
# =============================================================================
def extract_text_from_image(image_file):
    """Распознаёт текст на фото договора с предобработкой изображения"""
    try:
        import pytesseract
        
        # Открываем изображение
        img = Image.open(image_file).convert('L')  # Конвертируем в ч/б
        
        # === ПРЕДОБРАБОТКА ИЗОБРАЖЕНИЯ ===
        
        # 1. Увеличиваем контраст
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # 2. Увеличиваем резкость
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)
        
        # 3. Убираем шум
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # 4. Бинаризация (чёрно-белый порог)
        threshold = 150
        img = img.point(lambda p: 255 if p > threshold else 0)
        
        # === РАСПОЗНАВАНИЕ ===
        config = '--psm 6 -l rus+eng'
        text = pytesseract.image_to_string(img, config=config)
        text = text.strip()
        
        # Проверка качества
        if len(text) < 20 or not any(c.isalpha() for c in text):
            return None, "⚠️ Не удалось распознать текст. Сделайте фото чётче, при хорошем освещении."
        
        return text, None
        
    except ImportError as e:
        return None, f"❌ pytesseract не установлен. Установите: pip install pytesseract"
    except Exception as e:
        return None, f"❌ Ошибка OCR: {str(e)}"

# =============================================================================
# 🎨 UI — ШАПКА
# =============================================================================
st.title("⚖️ Context.Pro Legal")
st.caption("Анализ договоров • Консультации • РФ/РБ")

# =============================================================================
# ⚖️ ЮРИСДИКЦИЯ НА ГЛАВНОЙ
# =============================================================================
st.markdown("### ⚖️ Юрисдикция")
jur = st.radio(
    "Выберите законодательство:",
    ["🇷🇺 РФ", "🇧🇾 РБ"],
    horizontal=True,
    index=0,
    key="jurisdiction_radio"
)
st.session_state.jurisdiction = jur
st.markdown("---")

# =============================================================================
# 📋 ВКЛАДКИ
# =============================================================================
tab1, tab2 = st.tabs(["📋 Договор", "💬 Вопрос"])

# =============================================================================
# ВКЛАДКА 1: ДОГОВОР (С КАМЕРОЙ)
# =============================================================================
with tab1:
    st.markdown("#### 📄 Текст договора")
    st.caption("💡 Вставьте текст ИЛИ сфотографируйте договор")
    
    # Переключатель: текст или фото
    input_mode = st.radio(
        "Способ ввода:",
        ["✍️ Вставить текст", "📷 Сфотографировать"],
        horizontal=True,
        key="contract_input_mode"
    )
    
    contract_text = ""
    
    if input_mode == "✍️ Вставить текст":
        contract_text = st.text_area(
            "Текст договора:",
            value=st.session_state.contract_txt,
            height=220,
            key="contract_text_input",
            placeholder="Скопируйте сюда текст договора..."
        )
    else:
        # 📷 КАМЕРА
        st.info("📱 Наведите камеру на текст. Освещение должно быть хорошим, текст — крупным и чётким.")
        img_file = st.camera_input("📸 Сделайте фото договора", key="contract_camera")
        
        if img_file:
            with st.spinner("🔍 Распознаю текст..."):
                extracted, error = extract_text_from_image(img_file)
                if error:
                    st.error(error)
                elif extracted:
                    contract_text = extracted
                    st.success(f"✅ Распознано {len(extracted)} символов")
                    with st.expander("👁️ Показать текст"):
                        st.text(extracted[:500] + "..." if len(extracted) > 500 else extracted)
                    st.session_state.contract_txt = extracted
                else:
                    st.warning("⚠️ Не удалось распознать. Попробуйте ещё раз.")
    
    if contract_text:
        st.session_state.contract_txt = contract_text
    
    # Кнопки
    col1, col2 = st.columns([3, 1])
    with col1:
        analyze_btn = st.button(
            "⚖️ Проверить договор", 
            use_container_width=True, 
            key="btn_contract",
            disabled=st.session_state.is_analyzing or not (contract_text.strip() if contract_text else False)
        )
    with col2:
        if st.button("🗑️", key="clear_contract"):
            for k in ['contract_txt', 'result', 'last_mode']:
                st.session_state[k] = "" if k != 'last_mode' else None
            st.rerun()
    
    # ОБРАБОТКА АНАЛИЗА
    if analyze_btn and contract_text and contract_text.strip():
        is_valid, message = validate_input(contract_text, "contract")
        if not is_valid:
            st.warning(message)
        else:
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            st.markdown('<div class="empire-loading">Анализирую договор по нормам ' + jur + '...</div>', unsafe_allow_html=True)
            sys_prompt = build_system_prompt(jur, "contract")
            result, error = query_ai(sys_prompt, contract_text)
            st.session_state.is_analyzing = False
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.success("✅ Анализ завершён!")
                st.rerun()
    
    # Показ результата
    if st.session_state.last_mode == "contract" and st.session_state.result:
        st.markdown("---")
        st.markdown("### 🔍 Результаты анализа")
        st.markdown(st.session_state.result)
        st.download_button(
            "📥 Скачать отчёт",
            st.session_state.result,
            "context_pro_analysis.txt",
            "text/plain",
            use_container_width=True,
            key="download_contract"
        )

# =============================================================================
# ВКЛАДКА 2: ВОПРОС
# =============================================================================
with tab2:
    st.markdown("#### ⚖️ Ваш вопрос")
    st.caption("💡 Минимум 10 символов")
    
    q = st.text_area(
        "Задайте юридический вопрос:",
        value=st.session_state.question_txt,
        height=220,
        key="question_input",
        placeholder="Например: Какие риски по ст. 651 ГК РФ?"
    )
    st.session_state.question_txt = q
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ask_btn = st.button(
            "⚡ Получить ответ", 
            use_container_width=True, 
            key="btn_question",
            disabled=st.session_state.is_analyzing or not (q.strip() if q else False)
        )
    with col2:
        if st.button("🗑️", key="clear_question"):
            for k in ['question_txt', 'result', 'last_mode']:
                st.session_state[k] = "" if k != 'last_mode' else None
            st.rerun()
    
    # ОБРАБОТКА ВОПРОСА
    if ask_btn and q and q.strip():
        is_valid, message = validate_input(q, "question")
        if not is_valid:
            st.warning(message)
        else:
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "question"
            st.markdown('<div class="empire-loading">Готовлю консультацию по ' + jur + '...</div>', unsafe_allow_html=True)
            sys_prompt = build_system_prompt(jur, "question")
            result, error = query_ai(sys_prompt, q)
            st.session_state.is_analyzing = False
            if error:
                st.error(error)
            else:
                st.session_state.result = result
                st.success("✅ Ответ готов!")
                st.rerun()
    
    # Показ результата
    if st.session_state.last_mode == "question" and st.session_state.result:
        st.markdown("---")
        st.markdown("### 💬 Консультация")
        st.markdown(st.session_state.result)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 15px; color: #718096; font-size: 0.85rem;">
    <p>⚖️ <strong>Context.Pro Legal</strong> | 🇷🇺 РФ • 🇧🇾 РБ</p>
    <p style="font-size: 0.75rem;">🔒 Приватно • Без логов • Конфиденциально</p>
    <p style="font-size: 0.75rem;">⚠️ ИИ-помощник не заменяет очную консультацию юриста</p>
</div>
""", unsafe_allow_html=True)
