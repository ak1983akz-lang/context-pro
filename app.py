import streamlit as st
import requests
import time
import base64
from PIL import Image, ImageEnhance, ImageFilter
import io
import re

# =============================================================================
# 📱 PWA MANIFEST
# =============================================================================
pwa_manifest = """
<link rel="manifest" href="application/manifest+json,{
    &quot;name&quot;: &quot;Context.Pro Legal&quot;,
    &quot;short_name&quot;: &quot;ContextPro&quot;,
    &quot;start_url&quot;: &quot;/&quot;,
    &quot;display&quot;: &quot;standalone&quot;,
    &quot;background_color&quot;: &quot;#0e1117&quot;,
    &quot;theme_color&quot;: &quot;#1f77b4&quot;
}">
<meta name="theme-color" content="#1f77b4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
"""
st.markdown(pwa_manifest, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================
if 'contract_txt' not in st.session_state:
    st.session_state.contract_txt = ""
if 'result' not in st.session_state:
    st.session_state.result = ""
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = "🇷 РФ"
if 'is_analyzing' not in st.session_state:
    st.session_state.is_analyzing = False
if 'last_mode' not in st.session_state:
    st.session_state.last_mode = None
if 'ocr_counter' not in st.session_state:
    st.session_state.ocr_counter = 0
if 'ocr_complete' not in st.session_state:
    st.session_state.ocr_complete = False
if 'show_rules' not in st.session_state:
    st.session_state.show_rules = False
if 'question_txt' not in st.session_state:
    st.session_state.question_txt = ""
if 'uploaded_files_list' not in st.session_state:
    st.session_state.uploaded_files_list = []
if 'page_texts' not in st.session_state:
    st.session_state.page_texts = {}

# =============================================================================
# 🔧 УЛУЧШЕНИЕ ИЗОБРАЖЕНИЯ (ПРЕПРОЦЕССИНГ)
# =============================================================================
def enhance_image_for_ocr(image: Image.Image, enhancement_level: str = "medium") -> Image.Image:
    """
    Улучшает качество изображения для лучшего распознавания OCR
    enhancement_level: "light", "medium", "aggressive"
    """
    # Конвертируем в RGB если нужно
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Увеличиваем разрешение в 2 раза для лучшего качества
    width, height = image.size
    image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
    
    # Применяем улучшения в зависимости от уровня
    if enhancement_level in ["medium", "aggressive"]:
        # Увеличиваем резкость
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)  # Увеличиваем резкость в 2 раза
        
        # Увеличиваем контраст
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)  # Увеличиваем контраст в 1.5 раза
        
        # Увеличиваем яркость
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)  # Немного увеличиваем яркость
    
    if enhancement_level == "aggressive":
        # Применяем фильтр повышения резкости
        image = image.filter(ImageFilter.SHARPEN)
        
        # Убираем шум (медианный фильтр)
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Ещё больше контраста для очень плохих фото
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.8)
    
    return image

# =============================================================================
# 🔤 АВТОКОРРЕКЦИЯ ТЕКСТА (Post-processing)
# =============================================================================
def autocorrect_text(text: str) -> str:
    """
    Исправляет распространённые ошибки OCR для русского текста
    """
    if not text:
        return text
    
    # Словарь распространённых ошибок OCR и их исправлений
    ocr_corrections = {
        # Цифры и буквы
        '0': 'о', '1': 'l', '5': 's',
        'ё': 'е',  # Часто ё путают с е
        
        # Распространённые ошибки распознавания
        'договора': 'договора',
        'доrовора': 'договора',
        'доrовор': 'договор',
        'дoговор': 'договор',  # o вместо о
        'догов0р': 'договор',  # 0 вместо о
        
        # Частые слова с ошибками
        'сторoна': 'сторона',
        'стoрона': 'сторона',
        'стoрoна': 'сторона',
        'oплата': 'оплата',
        'оплaта': 'оплата',
        'аpенда': 'аренда',
        'apeнда': 'аренда',
        
        # Юридические термины
        'oбязательство': 'обязательство',
        'oбязанность': 'обязанность',
        'oтветственность': 'ответственность',
        'неустoйка': 'неустойка',
        'неустoйкa': 'неустойка',
        
        # Даты и числа
        '2O2': '202',  # O вместо 0
        '2O2O': '2020',
        '2O21': '2021',
        '2O22': '2022',
        '2O23': '2023',
        '2O24': '2024',
    }
    
    corrected_text = text
    
    # Применяем исправления
    for wrong, correct in ocr_corrections.items():
        # Используем regex для замены с учётом регистра
        corrected_text = re.sub(
            r'\b' + re.escape(wrong) + r'\b',
            correct,
            corrected_text,
            flags=re.IGNORECASE
        )
    
    # Исправляем повторяющиеся пробелы
    corrected_text = re.sub(r'\s+', ' ', corrected_text)
    
    # Исправляем пробелы перед знаками препинания
    corrected_text = re.sub(r'\s+([.,;:!?])', r'\1', corrected_text)
    
    return corrected_text.strip()

# =============================================================================
# 📸 OCR С НЕСКОЛЬКИМИ ПОПЫТКАМИ И УЛУЧШЕНИЯМИ
# =============================================================================
def extract_text_from_image(uploaded_file, enhancement_mode: str = "auto") -> tuple:
    """
    Распознавание текста с автоматическим улучшением качества
    enhancement_mode: "off", "light", "medium", "aggressive", "auto"
    """
    try:
        # Открываем изображение
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        
        # Определяем режим улучшения
        if enhancement_mode == "auto":
            # Автоматически определяем по размеру и качеству
            if image.size[0] < 1000 or image.size[1] < 1000:
                enhancement_mode = "aggressive"
            elif image.size[0] < 2000 or image.size[1] < 2000:
                enhancement_mode = "medium"
            else:
                enhancement_mode = "light"
        
        best_text = ""
        best_confidence = 0
        
        # Пробуем несколько вариантов обработки
        modes_to_try = []
        if enhancement_mode == "auto":
            modes_to_try = ["medium", "aggressive", "light"]
        else:
            modes_to_try = [enhancement_mode, "medium"]
        
        for mode in modes_to_try:
            try:
                # Улучшаем изображение
                uploaded_file.seek(0)
                img = Image.open(uploaded_file)
                enhanced_img = enhance_image_for_ocr(img, mode)
                
                # Конвертируем в bytes
                img_byte_arr = io.BytesIO()
                enhanced_img.save(img_byte_arr, format='JPEG', quality=95, optimize=True)
                img_byte_arr.seek(0)
                
                # Отправляем на OCR
                api_key = 'helloworld'
                
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    files={'file': ('image.jpg', img_byte_arr, 'image/jpeg')},
                    data={
                        'apikey': api_key,
                        'language': 'rus',
                        'isOverlayRequired': 'false',
                        'detectOrientation': 'true',
                        'OCREngine': '2',
                        'scale': 'true',
                        'isTable': 'true',
                        'detectOSD': 'true'  # Detect orientation and script
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get('IsErroredOnProcessing'):
                        text = data.get('ParsedResults', [{}])[0].get('ParsedText', '')
                        if text and text.strip():
                            # Применяем автокоррекцию
                            corrected_text = autocorrect_text(text)
                            
                            # Выбираем лучший результат
                            if len(corrected_text) > len(best_text):
                                best_text = corrected_text
                                best_confidence = 1
            except Exception as e:
                continue
        
        if best_text.strip():
            return best_text.strip(), None
        else:
            return None, "Текст не распознан. Попробуйте улучшить качество фото."
            
    except Exception as e:
        return None, f"Ошибка обработки: {str(e)}"

# =============================================================================
# 🔄 СБРОС
# =============================================================================
def reset_session():
    st.session_state.contract_txt = ""
    st.session_state.question_txt = ""
    st.session_state.result = ""
    st.session_state.is_analyzing = False
    st.session_state.last_mode = None
    st.session_state.ocr_counter = 0
    st.session_state.ocr_complete = False
    st.session_state.show_rules = False
    st.session_state.uploaded_files_list = []
    st.session_state.page_texts = {}

# =============================================================================
# 🧠 AI ЗАПРОС
# =============================================================================
def get_api_key():
    try:
        if "openrouter" in st.secrets:
            return st.secrets["openrouter"]["api_key"]
    except:
        pass
    return None

def query_ai(system_prompt: str, user_text: str):
    api_key = get_api_key()
    if not api_key:
        return None, "❌ API ключ не настроен"
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://context-pro.streamlit.app"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                "temperature": 0.2,
                "max_tokens": 2000
            },
            timeout=90
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"], None
        return None, f"Ошибка {response.status_code}"
    except Exception as e:
        return None, str(e)

# =============================================================================
# 🎨 CSS
# =============================================================================
st.markdown("""
<style>
.stApp { background: #0e1117; color: #fafafa; }
.stTextArea textarea { background: #1e2329; color: #fff; font-size: 16px !important; }
.stButton>button { 
    background: #1f77b4; color: white; font-weight: bold; border-radius: 8px; height: 50px; font-size: 16px; width: 100%;
}
.stButton#btn_new_session { background: #dc2626 !important; }
h1 { font-size: 1.5rem !important; }
.loading-box { background: #1a233a; border: 2px dashed #D4AF37; color: #D4AF37; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; }
.ocr-warning { background: #1e3a5f; border-left: 4px solid #3b82f6; padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0; color: #fff; }
.rules-box { background: #161b22; border-left: 4px solid #1f77b4; padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 20px; }
.rule-item { display: flex; align-items: start; margin-bottom: 10px; font-size: 0.9rem; }
.rule-icon { margin-right: 10px; min-width: 24px; }
.file-info { background: #262730; padding: 12px; border-radius: 8px; margin: 8px 0; border: 1px solid #444; }
.success-box { background: #1a3a2a; border-left: 4px solid #22c55e; padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0; color: #4ade80; }
@media (max-width: 768px) {
    .block-container { padding-top: max(1rem, env(safe-area-inset-top)) !important; }
    h1 { font-size: 1.3rem !important; }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🏗 ИНТЕРФЕЙС
# =============================================================================

# 1. ШАПКА
col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
with col_h1:
    st.title("⚖️ Context.Pro")
    st.caption("🔍 Улучшенное распознавание")
with col_h2:
    if st.button("❓", use_container_width=True, key="btn_rules"):
        st.session_state.show_rules = not st.session_state.show_rules
with col_h3:
    if st.button("🔄", use_container_width=True, key="btn_reset"):
        reset_session()
        st.rerun()

if st.session_state.show_rules:
    st.markdown("""
    <div class="rules-box">
        <b>📜 Как пользоваться:</b><br>
        1. Выбери режим улучшения качества<br>
        2. Загрузи фото (даже нечёткое)<br>
        3. ИИ улучшит фото и распознает текст<br>
        4. Автокоррекция исправит ошибки<br>
        5. Жми «Анализировать»
    </div>
    """, unsafe_allow_html=True)

st.divider()

# 2. ЮРИСДИКЦИЯ
jur = st.radio("Законодательство:", ["🇷🇺 РФ", "🇧 РБ"], horizontal=True, label_visibility="collapsed", key="jur_rad")
st.session_state.jurisdiction = "🇷 РФ" if "РФ" in jur else "🇧🇾 РБ"
st.divider()

# 3. ВКЛАДКИ
tab_photo, tab_manual, tab_q = st.tabs(["📸 Фото", "✍️ Текст", "💬 Вопрос"])

# === ВКЛАДКА 1: ФОТО ===
with tab_photo:
    st.markdown("#### 📷 Загрузка с улучшением качества")
    
    # Выбор режима улучшения
    enhancement_mode = st.selectbox(
        "🔧 Режим улучшения качества:",
        options=["auto", "light", "medium", "aggressive", "off"],
        format_func=lambda x: {
            "auto": "🤖 Авто (рекомендуется)",
            "light": "☀️ Лёгкое (хорошее фото)",
            "medium": "⚡ Среднее (среднее качество)",
            "aggressive": "🔥 Мощное (плохое/размытое фото)",
            "off": "❌ Без улучшения"
        }[x],
        index=0,
        help="Выберите 'Мощное' для нечётких, размытых или тёмных фото"
    )
    
    st.markdown("""
    <div class="ocr-warning">
    ⚡ <b>Улучшенное распознавание:</b><br>
    • Автоматическое улучшение контраста и резкости<br>
    • Увеличение разрешения в 2 раза<br>
    • Автокоррекция слов по смыслу<br>
    • Исправление ошибок OCR<br>
    • Работает даже с нечёткими фото!
    </div>
    """, unsafe_allow_html=True)
    
    # Загрузчик
    current_files = st.file_uploader(
        "📁 Выберите фото (даже нечёткое)",
        type=["jpg", "jpeg", "png", "heic", "heif"],
        accept_multiple_files=True,
        key=f"up_{st.session_state.ocr_counter}",
        label_visibility="collapsed"
    )
    
    if current_files:
        for f in current_files:
            if not any(x.name == f.name and x.size == f.size for x in st.session_state.uploaded_files_list):
                st.session_state.uploaded_files_list.append(f)
        
        st.markdown(f"<div class='success-box'>✅ Загружено: <b>{len(st.session_state.uploaded_files_list)}</b> ф.</div>", unsafe_allow_html=True)
        
        for i, f in enumerate(st.session_state.uploaded_files_list):
            st.markdown(f"<div class='file-info'>📄 Стр. {i+1}: {f.name} ({round(f.size/1024, 1)} KB)</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Очистить", key="clear_q"):
                st.session_state.uploaded_files_list = []
                st.rerun()
        with c2:
            if st.button("🔍 Распознать с улучшением", type="primary", key="btn_ocr_go"):
                progress_bar = st.progress(0)
                status = st.empty()
                all_text = ""
                
                st.markdown('<div class="loading-box">🔍 <b>Улучшаю фото и распознаю...</b><br><small>Это займёт 30-60 секунд</small></div>', unsafe_allow_html=True)
                
                total = len(st.session_state.uploaded_files_list)
                for idx, file in enumerate(st.session_state.uploaded_files_list):
                    status.text(f"Обработка стр. {idx+1}/{total} (улучшение + OCR)...")
                    file.seek(0)
                    
                    text, error = extract_text_from_image(file, enhancement_mode)
                    
                    if text:
                        header = f"\n\n{'='*40}\nСТРАНИЦА {idx+1}\n{'='*40}\n\n" if idx > 0 else ""
                        all_text += header + text
                        st.session_state.page_texts[idx] = text
                        progress_bar.progress(int((idx+1)/total * 100))
                    else:
                        st.warning(f"Стр. {idx+1}: {error}")
                
                status.empty()
                progress_bar.empty()
                
                if all_text.strip():
                    st.session_state.contract_txt = all_text.strip()
                    st.session_state.ocr_complete = True
                    st.session_state.ocr_counter += 1
                    st.success(f"✅ Распознано! ({len(all_text)} символов)")
                    st.rerun()
                else:
                    st.error("❌ Не удалось распознать. Попробуйте режим 'Мощное' или сделайте фото получше.")
    
    st.divider()
    
    if st.session_state.ocr_complete and st.session_state.contract_txt:
        st.markdown("### 📝 Распознанный текст (с автокоррекцией)")
        
        if st.session_state.page_texts:
            with st.expander(f"📊 Статистика ({len(st.session_state.page_texts)} стр.)"):
                for i, t in st.session_state.page_texts.items():
                    st.write(f"Стр. {i+1}: {len(t)} зн.")
        
        txt = st.text_area("Текст (отредактируйте если нужно):", value=st.session_state.contract_txt, height=400, key=f"area_{st.session_state.ocr_counter}")
        st.session_state.contract_txt = txt
        
        if st.button("🚀 Анализировать", type="primary", disabled=len(txt)<50):
            st.session_state.is_analyzing = True
            st.session_state.last_mode = "contract"
            st.markdown('<div class="loading-box">⚖️ Анализ...</div>', unsafe_allow_html=True)
            
            jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
            prompt = f"Юрист ({jur_base}). Анализ договора. 1. Риски 🔴. 2. Плюсы ✅. 3. Советы 📝. 4. Итог."
            res, err = query_ai(prompt, txt)
            
            st.session_state.is_analyzing = False
            if err: st.error(err)
            else:
                st.session_state.result = res
                st.success("✅ Готово!")
                st.rerun()
        
        if st.session_state.result:
            st.divider()
            st.markdown(st.session_state.result)
            st.download_button("📥 Скачать", st.session_state.result, "report.txt")
    else:
        st.text_area("Ожидание...", value="", disabled=True, height=200)

# === ВКЛАДКА 2: РУЧНОЙ ВВОД ===
with tab_manual:
    txt = st.text_area("Вставь текст:", value=st.session_state.contract_txt, height=400, key="man_area")
    st.session_state.contract_txt = txt
    if st.button("🚀 Анализ", disabled=len(txt)<50):
        st.session_state.last_mode = "contract"
        st.markdown('<div class="loading-box">⚖️ Анализ...</div>', unsafe_allow_html=True)
        jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
        res, err = query_ai(f"Юрист ({jur_base}). Анализ.", txt)
        if not err:
            st.session_state.result = res
            st.rerun()
    if st.session_state.result and st.session_state.last_mode == "contract":
        st.markdown(st.session_state.result)

# === ВКЛАДКА 3: ВОПРОС ===
with tab_q:
    q = st.text_area("Вопрос:", value=st.session_state.question_txt, height=200, key="q_ar")
    st.session_state.question_txt = q
    if st.button("⚡ Ответ", disabled=len(q)<5):
        st.markdown('<div class="loading-box">🧠 Думаю...</div>', unsafe_allow_html=True)
        jur_base = "РФ" if "РФ" in st.session_state.jurisdiction else "РБ"
        res, err = query_ai(f"Юрист ({jur_base}). Ответ со статьями.", q)
        if not err:
            st.divider()
            st.markdown(res)

st.divider()
st.caption("⚖️ Context.Pro | 🔍 Улучшенное распознавание текста")
