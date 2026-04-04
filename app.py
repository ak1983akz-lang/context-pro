from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import os
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

def compress_image(file_bytes, max_size_kb=500):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ('RGBA', 'P', 'LA'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P': img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = bg
        elif img.mode != 'RGB': img = img.convert('RGB')
        w, h = img.size
        if max(w, h) > 1600:
            scale = 1600 / max(w, h)
            img = img.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
        quality = 85
        for _ in range(10):
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=quality, optimize=True)
            if buf.tell() <= max_size_kb * 1024: return buf.getvalue()
            quality -= 5
        return buf.getvalue()
    except: return file_bytes

@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    try:
        file = request.files['file']
        compressed = compress_image(file.read())
        files = {'file': ('image.jpg', io.BytesIO(compressed), 'image/jpeg')}
        data = {'apikey': OCR_API_KEY, 'language': 'rus', 'isOverlayRequired': 'false', 'detectOrientation': 'true', 'OCREngine': '2'}
        resp = requests.post('https://api.ocr.space/parse/image', files=files, data=data, timeout=60)
        result = resp.json()
        if result.get('IsErroredOnProcessing'):
            return jsonify({'error': result.get('ErrorMessage', ['Error'])[0]}), 400
        text = result.get('ParsedResults', [{}])[0].get('ParsedText', '')
        return jsonify({'text': text.strip() if text else ''})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    try:
        data = request.json
        text = data.get('text', '')
        jurisdiction = data.get('jurisdiction', 'RU')
        contract_type = data.get('contract_type', 'Другое')
        
        if not OPENROUTER_API_KEY:
            return jsonify({'error': 'API key not set'}), 500
        
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
        
        resp = requests.post('https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENROUTER_API_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'deepseek/deepseek-chat', 'messages': [
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': text}
            ], 'temperature': 0.2, 'max_tokens': 3000}, timeout=120)
        
        if resp.status_code == 200:
            result = resp.json()['choices'][0]['message']['content'].strip()
            risk_summary = {
                'critical': len(re.findall(r'🔴', result)),
                'medium': len(re.findall(r'🟡', result)),
                'low': len(re.findall(r'🟢', result)),
                'verdict': 'Требует правок' if 'требует' in result.lower() else 'Опасно' if 'опасно' in result.lower() else 'Нормально'
            }
            return jsonify({'result': result, 'risk_summary': risk_summary})
        return jsonify({'error': f'API error: {resp.status_code}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        data = request.json
        question = data.get('question', '')
        jurisdiction = data.get('jurisdiction', 'RU')
        
        if not OPENROUTER_API_KEY:
            return jsonify({'error': 'API key not set'}), 500
        
        jur_base = 'РФ' if jurisdiction == 'RU' else 'РБ'
        resp = requests.post('https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENROUTER_API_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'deepseek/deepseek-chat', 'messages': [
                {'role': 'system', 'content': f'Ты юрист ({jur_base}). Отвечай со ссылками на законы.'},
                {'role': 'user', 'content': question}
            ], 'temperature': 0.2, 'max_tokens': 2000}, timeout=90)
        
        if resp.status_code == 200:
            answer = resp.json()['choices'][0]['message']['content'].strip()
            return jsonify({'answer': answer})
        return jsonify({'error': f'API error: {resp.status_code}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
