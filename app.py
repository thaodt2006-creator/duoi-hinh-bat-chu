import json
from vosk import Model, KaldiRecognizer
import wave
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
    
vosk_model = Model("vosk-model-small-vn-0.4")

def chuan_hoa(text):
    return text.strip().lower()

def tinh_do_tuong_dong(chuoi1, chuoi2):
    distance = Levenshtein.distance(chuoi1, chuoi2)
    max_len = max(len(chuoi1), len(chuoi2))
    if max_len == 0: return 1.0
    return 1.0 - (distance / max_len)

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
    threshold = config["game"]["matchThreshold"]

    # Trình duyệt ghi âm ra webm/ogg, cần convert sang wav cho speech_recognition đọc được
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
        wf = wave.open(duong_dan_wav, "rb")
        rec = KaldiRecognizer(vosk_model, wf.getframerate())
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)
        van_ban_asr = json.loads(rec.FinalResult()).get("text", "")
        wf.close()
    except Exception as e:
        if os.path.exists(duong_dan_goc): os.remove(duong_dan_goc)
        if os.path.exists(duong_dan_wav): os.remove(duong_dan_wav)
        return jsonify({"error": "Không thể nhận diện giọng nói"}), 500

    chuoi_nguoi_dung = chuan_hoa(van_ban_asr)
    do_khop_cao_nhat = 0.0

    for dap_an in danh_sach_chap_nhan:
        chuoi_chuan = chuan_hoa(dap_an)
        do_tuong_dong = tinh_do_tuong_dong(chuoi_nguoi_dung, chuoi_chuan)
        if do_tuong_dong > do_khop_cao_nhat:
            do_khop_cao_nhat = do_tuong_dong

    trang_thai = "DUNG" if do_khop_cao_nhat >= threshold else "SAI"
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