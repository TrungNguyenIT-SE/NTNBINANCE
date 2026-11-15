# Stage M — Image pipeline v1

## Phạm vi

Pipeline xử lý cặp ảnh chart `1h` + `15m` hoàn toàn trên máy cục bộ. Phiên bản v1 chỉ hỗ trợ
`BTCUSDT`, `ETHUSDT`, ba bố cục đã biết (`BINANCE`, `TRADINGVIEW`, `SYNTHETIC`) và ảnh tối thiểu
800×600. Nó không dùng VLM, API OCR, cloud hay tự động đặt lệnh.

Hai ảnh Binance do chủ dự án cung cấp ngày 16/11/2026 được dùng làm tham chiếu thiết kế bố cục:
symbol ở header, timeframe gần vùng chart, trục giá bên phải và trục thời gian bên dưới. Vì ảnh đính
kèm hội thoại không phải artifact bất biến trong repository, chúng không được báo cáo như final-test
fixture. Ma trận tái lập trong repo dùng renderer point-in-time và ba layout đại diện.

## Luồng xử lý fail-safe

1. Stage L decode/re-encode ảnh và loại metadata trước khi Stage M đọc pixel.
2. Tìm vùng có cấu trúc nến màu; crop theo `Rect` và giữ aspect ratio bằng letterbox, không kéo méo.
3. Đo blur, contrast, edge density, số thành phần nến, hai trục và vùng che phủ.
4. OCR cục bộ chỉ trên 18% header để tránh grid/nến bị nhận nhầm thành chữ.
5. Chỉ parse symbol/timeframe/timestamp/`LAST` bằng regex allow-list; không fuzzy-correct.
6. Đối chiếu với khai báo người dùng, capture time và giá market authoritative bằng policy Stage K.
7. Trả `REJECTED_INPUT` cho ảnh/symbol/timeframe sai; trả `NO_TRADE` cho bằng chứng thiếu, ảnh cũ,
   giá lệch hoặc layout OOD. Chỉ `ACCEPT` khi tất cả gate đạt.

## Ngưỡng khóa v1

Nguồn cấu hình audit là `configs/images/image-pipeline-v1.toml`:

- OCR confidence tối thiểu: `0.70`; chênh timestamp OCR–khai báo tối đa: `120000 ms`.
- Contrast ≥ `0.035`; blur score ≥ `1.2`; edge density ≥ `0.006`.
- Right-axis ≥ `0.004`; bottom-axis ≥ `0.002`; occlusion ≤ `0.15`.
- Thành phần nến tối thiểu: 38 (`1h`) và 48 (`15m`).
- Không tune các ngưỡng này bằng final test. Thay đổi phải tạo config/ADR phiên bản mới.

## Synthetic chart và augmentation

`render_chart` chỉ nhận nến đã đóng có `close_time_ms <= decision_time_ms`, yêu cầu thứ tự tăng dần
và chỉ render tối đa 120 nến gần nhất. Header chứa các trường có thể kiểm chứng. Renderer hỗ trợ
dark/light/alternate theme và ba layout mà không dùng dữ liệu tương lai.

`augment_for_training` chỉ chạy khi `partition="TRAIN"`. Nó giới hạn ở brightness, contrast, color và
JPEG compression có seed. Không flip ngang/dọc, đảo thứ tự thời gian hoặc crop làm mất trục.

## OCR, vận hành và giới hạn

`tesserocr==2.13.0` chạy Tesseract cục bộ. `eng.traineddata` từ `tessdata_fast` được pin theo commit và
SHA-256 trong `models/ocr/MANIFEST.json`; mỗi lần OCR fail closed nếu checksum sai. Có thể phục hồi
artifact bằng `scripts/fetch-ocr-model.ps1`. Không có ảnh hay text nào rời khỏi máy.

- Latency CPU đo được khoảng 1.84 giây median và 4.60 giây p95/ảnh trong ma trận 27 case; đây là
  workflow bất đồng bộ, không phải feed real-time.
- Full-screen UI mới, font quá nhỏ, watermark lớn, indicator có màu giống nến hoặc header bị ẩn có thể
  bị từ chối. Đây là hành vi an toàn, không phải lý do bỏ gate.
- Stage M kiểm tra khả năng đọc và nhất quán đầu vào; không chứng minh chart là nguồn xác thực.
- Không suy ra `LONG/SHORT` ở Stage M. Model hybrid bắt đầu từ Stage O sau numeric features.

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe -m pytest tests/image_pipeline -q
.\.venv\Scripts\python.exe scripts/benchmark-image-pipeline.py
```

Bằng chứng: `reports/image-pipeline.md`, `reports/image-pipeline-benchmark.json` và
`tests/image_pipeline/`.
