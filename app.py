import streamlit as st
import requests
import re
import os
from PIL import Image
import io

# ================= CONFIG =================
OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ================= SESSION STATE =================
if 'contract_txt' not in st.session_state:
    st.session_state.contract_txt = ""
if 'result' not in st.session_state:
    st.session_state.result = None
if 'jurisdiction' not in st.session_state:
    st.session_state.jurisdiction = "RU"
if 'contract_type' not in st.session_state:
    st.session_state.contract_type = "Другое"
if 'risk_summary' not in st.session_state:
    st.session_state.risk_summary = None

# ================= VK BRIDGE =================
st.markdown("""
<script src="https://unpkg.com/@vkontakte/vk-bridge/dist/browser.min.js"></script>
<script>
if (window.vkBridge) {
    vkBridge.send('VKWebAppInit').catch(()=>{});
}
</script>
""", unsafe_allow_html=True)

# ================= CSS =================
st.markdown("""
<style>
    #MainMenu, footer, .stDeployButton {visibility: hidden;}
    .stApp { background: #0e1117; color: #fafafa; }
    .stTextArea textarea { background: #1e2329 !important; color: #fff !important; }
    .stButton>button { 
        background: #1f77b4 !important; color: white !important; 
        border: none !important; border-radius: 8px !important; 
        height: 50px !important; font-weight: bold !important; width: 100% !important;
    }
    .risk-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0; }
    .risk-card { background: #1e2329; border-radius: 10px; padding: 12px; text-align: center; border: 2px solid #3a3f47; }
    .risk-card.critical { border-color: #ef4444; }
    .risk-card.medium { border-color: #f59e0b; }
    .risk-card.low { border-color: #22c55e; }
    .risk-card.verdict { border-color: #1f77b4; background: #1e3a5f; }
    .risk-num { font-size: 22px; font-weight: bold; display: block; }
    .risk-num.critical { color: #ef4444; }
    .risk-num.medium { color: #f59e0b; }
    .risk-num.low { color: #22c55e; }
    .risk-label { font-size: 11px; color: #a0a0a0; }
    .result-box { background: #1e2329; border-radius: 10px; padding: 16px; margin-top: 15px; white-space: pre-wrap; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# ================= FUNCTIONS =================
def compress_image(file_bytes, max_size_kb=500):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ('RGBA', 'P', 'LA'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P': img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        w, h = img.size
        if max(w, h) > 1600:
            scale = 1600 / max(w, h)
            img = img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
        quality = 85
        for _ in range(10):
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=quality, optimize=True)
            if buf.tell() <= max_size_kb * 1024:
                return buf.getvalue()
            quality -= 5
        return buf.getvalue()
    except:
        return file_bytes

def ocr_space(file_bytes, filename="img.jpg"):
    try:
        compressed = compress_image(file_bytes)
        files = {'file': (filename, io.BytesIO(compressed), 'image/jpeg')}
        data = {'apikey': OCR_API_KEY, 'language': 'rus', 'isOverlayRequired': 'false', 'detectOrientation': 'true', 'OCREngine': '2'}
        resp = requests.post('https://api.ocr.space/parse/image', files=files, data=data, timeout=60)
        result = resp.json()
        if result.get('IsErroredOnProcessing'):
            return None, result.get('ErrorMessage', ['Error'])[0]
        text = result.get('ParsedResults', [{}])[0].get('ParsedText', '')
        return text.strip() if text else None, None
    except Exception as e:
        return None, str(e)

def correct_text(text, jurisdiction):
    if not OPENROUTER_API_KEY or len(text) < 50:
        return text
    jur_name = 'Российская Федерация' if jurisdiction == 'RU' else 'Республика Беларусь'
    try:
        resp = requests.post('https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENROUTER_API_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'deepseek/deepseek-chat', 'messages': [
                {'role': 'system', 'content': f'Редактор юр. документов ({jur_name}). Исправь опечатки.'},
                {'role': 'user', 'content': f'Исправь:\n\n{text}'}
            ], 'temperature': 0.1, 'max_tokens': 3000}, timeout=120)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'].strip()
    except: pass
    return text

def analyze_contract(text, jurisdiction, contract_type):
    if not OPENROUTER_API_KEY:
        return None, "API ключ не настроен"
    jur_base = 'РФ' if jurisdiction == 'RU' else 'РБ'
    prompt = f"""Ты юрист по праву {jur_base}. Договор: {contract_type}.
Проанализируй:
1. 🔴 Критические риски
2. 🟡 Средние риски  
3. 🟢 Что хорошо
4. 💡 Рекомендации
5. ✅ Вердикт

Текст:
{text}"""
    try:
        resp = requests.post('https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENROUTER_API_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'deepseek/deepseek-chat', 'messages': [
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': text}
            ], 'temperature': 0.2, 'max_tokens': 3000}, timeout=120)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content'].strip(), None
        return None, "Ошибка сервиса"
    except Exception as e:
        return None, str(e)

def extract_risks(text):
    return {
        'critical': len(re.findall(r'🔴', text)),
        'medium': len(re.findall(r'🟡', text)),
        'low': len(re.findall(r'🟢', text)),
        'verdict': 'Требует правок' if 'требует' in text.lower() else 'Опасно' if 'опасно' in text.lower() else 'Нормально'
    }

# ================= UI =================
st.title("⚖️ umnyj-yurist")
st.caption("Анализ договоров")

# Настройки
col_j, col_t = st.columns(2)
with col_j:
    st.session_state.jurisdiction = st.selectbox("Юрисдикция", ["🇷🇺 РФ", "🇧🇾 РБ"], label_visibility="collapsed")
    st.session_state.jurisdiction = "RU" if "РФ" in st.session_state.jurisdiction else "BY"
with col_t:
    st.session_state.contract_type = st.selectbox("Тип договора", ["Договор аренды", "Купли-продажи", "Услуг", "Подряда", "Трудовой", "Поставки", "Займа", "Другое"], label_visibility="collapsed")

st.divider()

# Вкладки
tab1, tab2 = st.tabs(["📸 Фото", "📝 Текст"])

with tab1:
    uploaded = st.file_uploader("Загрузи фото", type=['jpg','jpeg','png'], label_visibility="collapsed")
    if uploaded:
        with st.spinner("🔍 Распознаю..."):
            text, err = ocr_space(uploaded.read(), uploaded.name)
            if err:
                st.error(f"Ошибка: {err}")
            elif text:
                st.session_state.contract_txt = correct_text(text, st.session_state.jurisdiction)
                st.success("✅ Готово!")
    
    if st.session_state.contract_txt:
        st.session_state.contract_txt = st.text_area("Текст:", value=st.session_state.contract_txt, height=250, label_visibility="collapsed")
        
        if st.button("⚖️ Анализировать", disabled=len(st.session_state.contract_txt)<50):
            with st.spinner("Анализирую..."):
                result, err = analyze_contract(st.session_state.contract_txt, st.session_state.jurisdiction, st.session_state.contract_type)
                if err:
                    st.error(err)
                else:
                    st.session_state.result = result
                    st.session_state.risk_summary = extract_risks(result)
                    st.success("✅ Готово!")

with tab2:
    txt = st.text_area("Вставь текст", height=250, label_visibility="collapsed")
    if st.button("Анализировать", disabled=len(txt)<50):
        with st.spinner("Анализирую..."):
            res, err = analyze_contract(txt, st.session_state.jurisdiction, st.session_state.contract_type)
            if not err:
                st.session_state.result = res
                st.session_state.risk_summary = extract_risks(res)
                st.rerun()

# РЕЗУЛЬТАТ
if st.session_state.result and st.session_state.risk_summary:
    st.divider()
    st.markdown("### 📊 Карта рисков")
    rs = st.session_state.risk_summary
    st.markdown(f"""
    <div class="risk-cards">
        <div class="risk-card critical"><span class="risk-num critical">{rs['critical']}</span><span class="risk-label">Критич.</span></div>
        <div class="risk-card medium"><span class="risk-num medium">{rs['medium']}</span><span class="risk-label">Средн.</span></div>
        <div class="risk-card low"><span class="risk-num low">{rs['low']}</span><span class="risk-label">ОК</span></div>
        <div class="risk-card verdict"><span class="risk-num">{rs['verdict']}</span><span class="risk-label">Вердикт</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 📋 Анализ")
    st.markdown(f"<div class='result-box'>{st.session_state.result}</div>", unsafe_allow_html=True)
