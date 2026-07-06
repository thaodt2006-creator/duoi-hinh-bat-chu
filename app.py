import json
import re
import unicodedata
import speech_recognition as sr
import Levenshtein
from gtts import gTTS
from pydub import AudioSegment
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

with open("metadata.json", "r", encoding="utf-8") as f:
    config = json.load(f)

recognizer = sr.Recognizer()

def chuan_hoa(text):
    text = unicodedata.normalize("NFC", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\sÀ-ɏḀ-ỿ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tinh_do_tuong_dong(chuoi1, chuoi2):
    distance = Levenshtein.distance(chuoi1, chuoi2)
    max_len = max(len(chuoi1), len(chuoi2))
    if max_len == 0: return 1.0
    return 1.0 - (distance / max_len)

def lcs_length(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]

def tinh_do_tuong_dong_lcs(recognized_text, answer_text):
    if len(recognized_text) == 0 or len(answer_text) == 0:
        return 0.0
    lcs_len = lcs_length(recognized_text, answer_text)
    max_len = max(len(recognized_text), len(answer_text))
    return lcs_len / max_len

def so_khop_va_quyet_dinh(text_tu_stt, acceptedAnswers, matchThreshold=0.8):
    input_text = chuan_hoa(text_tu_stt)
    max_score_lev = 0.0
    max_score_lcs = 0.0

    for dap_an in acceptedAnswers:
        dap_an_chuan = chuan_hoa(dap_an)

        score_lev = tinh_do_tuong_dong(input_text, dap_an_chuan)
        if score_lev > max_score_lev:
            max_score_lev = score_lev

        score_lcs = tinh_do_tuong_dong_lcs(input_text, dap_an_chuan)
        if score_lcs > max_score_lcs:
            max_score_lcs = score_lcs

    print(f"\n[KIỂM THỬ THUẬT TOÁN]")
    print(f"Nhận dạng từ STT : '{input_text}'")
    print(f"Điểm Levenshtein : {max_score_lev:.2f}")
    print(f"Điểm LCS         : {max_score_lcs:.2f}")
    print(f"-----------------------------------\n")

    if max_score_lev >= matchThreshold:
        return True, max_score_lev
    else:
        return False, max_score_lev

@app.route('/api/cham-diem', methods=['POST'])
def xu_ly_am_thanh():
    if 'audio_file' not in request.files:
        return jsonify({"error": "Không tìm thấy file âm thanh gửi lên"}), 400

    id_cau_hoi = int(request.form.get('id_cau_hoi', 1))
    file_am_thanh = request.files['audio_file']

    cau_hoi = next((q for q in config["questions"] if q["id"] == id_cau_hoi), None)
    if cau_hoi is None:
        return jsonify({"error": f"Không tìm thấy câu hỏi id={id_cau_hoi}"}), 400

    dap_an_goc = cau_hoi["keyword"]
    danh_sach_chap_nhan = cau_hoi["acceptedAnswers"]
    threshold = cau_hoi.get("matchThreshold", config["game"]["matchThreshold"])

    duong_dan_goc = f"temp_{id_cau_hoi}_raw"
    duong_dan_wav = f"temp_{id_cau_hoi}.wav"
    file_am_thanh.save(duong_dan_goc)

    try:
        am_thanh = AudioSegment.from_file(duong_dan_goc)
        am_thanh = am_thanh.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        am_thanh.export(duong_dan_wav, format="wav")
    except Exception as e:
        if os.path.exists(duong_dan_goc): os.remove(duong_dan_goc)
        return jsonify({"error": "Không thể đọc file âm thanh gửi lên"}), 400

    try:
        with sr.AudioFile(duong_dan_wav) as source:
            audio = recognizer.record(source)
        van_ban_asr = recognizer.recognize_google(audio, language="vi-VN")
    except sr.UnknownValueError:
        van_ban_asr = ""
    except sr.RequestError as e:
        if os.path.exists(duong_dan_goc): os.remove(duong_dan_goc)
        if os.path.exists(duong_dan_wav): os.remove(duong_dan_wav)
        return jsonify({"error": "Không thể kết nối Google Speech API"}), 500

    is_correct, do_khop_cao_nhat = so_khop_va_quyet_dinh(van_ban_asr, danh_sach_chap_nhan, threshold)
    trang_thai = "DUNG" if is_correct else "SAI"
    loi_nhan = config["game"]["messages"]["correct"] if trang_thai == "DUNG" else config["game"]["messages"]["wrong"].format(keyword=dap_an_goc)

    tts = gTTS(text=loi_nhan, lang="vi")
    file_ket_qua = f"phan_hoi_{id_cau_hoi}.mp3"
    tts.save(file_ket_qua)

    if os.path.exists(duong_dan_goc):
        os.remove(duong_dan_goc)
    if os.path.exists(duong_dan_wav):
        os.remove(duong_dan_wav)

    return jsonify({
        "ket_qua": trang_thai,
        "do_khop": round(do_khop_cao_nhat, 2),
        "asr_nghe_duoc": van_ban_asr,
        "file_phan_hoi_url": f"/api/audio/{file_ket_qua}"
    })

@app.route('/api/audio/<ten_file>')
def lay_audio_phan_hoi(ten_file):
    return send_from_directory('.', ten_file, mimetype='audio/mpeg')

if __name__ == '__main__':
    print("MÁY CHỦ AI ĐANG CHẠY TẠI CỔNG 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
