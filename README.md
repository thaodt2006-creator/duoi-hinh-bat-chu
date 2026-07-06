# Đuổi hình bắt chữ — Nhận diện giọng nói tiếng Việt

Game đuổi hình bắt chữ sử dụng nhận diện giọng nói offline bằng **Vosk** và Flask backend.

---

## Yêu cầu hệ thống

- Python 3.9+
- ffmpeg (cần thiết để pydub convert audio từ webm → wav)
  - Windows: tải tại https://ffmpeg.org/download.html, thêm vào PATH

---

## Cài đặt

```bash
# 1. Tạo và kích hoạt môi trường ảo
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Tải model Vosk tiếng Việt (nếu chưa có)
# Tải vosk-model-small-vn-0.4 tại https://alphacephei.com/vosk/models
# Giải nén vào thư mục gốc của dự án (cùng cấp với app.py)
```

---

## Chạy server

```bash
python app.py
```

Server khởi động tại: **http://localhost:5000**

---

## Chơi game

Mở trình duyệt và truy cập:

```
http://localhost:5000/game.html
```

> ⚠️ Phải mở qua `http://localhost:5000` (không dùng `file://`) để trình duyệt cho phép truy cập microphone.

---

## Cấu trúc dự án

```
├── app.py              # Flask backend: nhận audio, chạy Vosk ASR, chấm điểm
├── game.html           # Giao diện game
├── metadata.json       # Cấu hình câu hỏi, đáp án, điểm số
├── requirements.txt    # Danh sách thư viện Python
├── Images/             # Ảnh câu đố
├── Audio/              # File audio mẫu
└── vosk-model-small-vn-0.4/  # Model Vosk (không commit lên git)
```

---

## API

| Endpoint | Method | Mô tả |
|---|---|---|
| `POST /api/cham-diem` | POST | Nhận file audio + id câu hỏi, trả về kết quả ASR và điểm |
| `GET /api/audio/<file>` | GET | Trả về file mp3 phản hồi TTS |