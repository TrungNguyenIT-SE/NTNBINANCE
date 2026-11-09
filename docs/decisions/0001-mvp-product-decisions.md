# ADR-0001 — QUYẾT ĐỊNH SẢN PHẨM MVP D01–D08

> Status: `ACCEPTED`  
> Date: `09/11/2026`  
> Owner: Chủ dự án  
> Applies to: PRD v1.0 và toàn bộ local/private MVP

## Bối cảnh

Giai đoạn A yêu cầu khóa tám quyết định chi phối kiến trúc, dữ liệu, model, risk và cách nghiệm thu. Các lựa chọn phải đồng thời đáp ứng:

- Hai ảnh 1H + 15m là input trải nghiệm người dùng.
- Hệ thống không buộc giao dịch khi tín hiệu yếu.
- Kết quả có thể kiểm chứng bằng backtest/paper trading.
- Tổng chi tiền mặt tăng thêm bằng 0 VNĐ.
- MVP không mở rộng thành hệ thống giao dịch thật hoặc dịch vụ public.

## D01 — Sản phẩm chỉ phát tín hiệu

**Quyết định:** MVP phân tích và phát `LONG / SHORT / NO_TRADE`; không gửi lệnh đến Binance.

**Lý do:**

- Giảm rủi ro mất vốn, secret leakage và lỗi execution.
- Cho phép đánh giá edge trước khi thêm độ phức tạp của fill/reconciliation.
- Phù hợp ngân sách 0 VNĐ và phạm vi local research.

**Hệ quả:**

- Không cần API key trading/account ở MVP.
- UI không có nút đặt lệnh.
- Order execution chỉ được mô phỏng trong backtest/paper ledger.
- Auto-trading cần PRD/ADR mới; không được bật bằng config ẩn.

## D02 — Horizon chính là 60 phút

**Quyết định:** label và KPI chính dùng 4 nến 15m sau decision time. Horizon 2 nến (30 phút) và 8 nến (120 phút) chỉ dùng sensitivity/secondary analysis.

**Lý do:**

- Khớp vai trò chart 15m làm điểm kích hoạt và chart 1H làm context.
- Đủ thời gian để tín hiệu ngắn hạn phát triển nhưng chưa biến thành chiến lược dài hạn.
- Một horizon chính ngăn chọn horizon thuận lợi sau khi xem test.

**Hệ quả:**

- Embargo tối thiểu không nhỏ hơn horizon chính.
- Paper outcome chính chốt sau 60 phút theo label/backtest spec.
- Không gộp metrics của 30/60/120 phút thành một con số.

## D03 — Hai symbol USDⓈ-M perpetual

**Quyết định:** chỉ `BTCUSDT` và `ETHUSDT` Binance USDⓈ-M perpetual.

**Lý do:**

- Thanh khoản và lịch sử tốt hơn nhiều altcoin.
- Giảm khối lượng dữ liệu, training và số chiều kiểm thử trên máy local.
- Vẫn cho phép kiểm tra model trên hơn một tài sản.

**Hệ quả:**

- API reject symbol khác.
- Metrics và threshold phải báo cáo theo từng symbol, không chỉ aggregate.
- Thêm symbol cần coverage report, backtest và paper gate riêng.

## D04 — Nguồn ảnh Binance và TradingView

**Quyết định:** chấp nhận ảnh PNG/JPEG/WebP từ Binance hoặc TradingView theo template/rubric được kiểm định; nguồn `UNKNOWN` có thể upload nhưng phải qua quality/context gate nghiêm ngặt và không mặc định được coi là tương thích.

**Lý do:**

- Đây là hai nguồn chart phổ biến với user flow dự kiến.
- Giới hạn nguồn giúp kiểm soát layout/theme/domain shift.
- Cho phép render synthetic templates để tạo dữ liệu nghiên cứu nhưng không giả định chúng đại diện hoàn hảo cho ảnh thật.

**Hệ quả:**

- Phải có golden set sáng/tối/layout khác nhau.
- Không scrape UI; user chủ động cung cấp ảnh.
- Vision model không được chọn nếu chỉ học artifact renderer và không vượt domain test.

## D05 — Người dùng nội bộ/private beta

**Quyết định:** user là chủ dự án và nhóm beta được kiểm soát trên localhost/LAN riêng.

**Lý do:**

- Không có hạ tầng/SLA/DDoS protection cho public service.
- Cần paper validation và security self-review trước mọi mở rộng.
- Phù hợp zero-cost boundary.

**Hệ quả:**

- Default bind `127.0.0.1`.
- Không domain, public tunnel hoặc public deployment guide.
- Public/commercial launch cần đánh giá pháp lý, bảo mật và ngân sách mới.

## D06 — Ngân sách tiền mặt tăng thêm 0 VNĐ

**Quyết định:** không mua phần mềm/data/domain, không thuê cloud/GPU/server/SaaS/tư vấn và không dùng dịch vụ yêu cầu thanh toán.

**Lý do:** yêu cầu bắt buộc của chủ dự án.

**Hệ quả:**

- Dùng CPU/RAM/GPU/disk/Internet đã có.
- Stack ưu tiên SQLite, DuckDB, Parquet, filesystem và công cụ open-source/free.
- Nếu thiếu tài nguyên: giảm symbol/lịch sử/model/ảnh trước; không tự phát sinh phí.
- Free tier không là dependency bắt buộc vì có thể thay đổi điều khoản.
- “0 VNĐ” là không có khoản thanh toán mới, không phủ nhận chi phí kinh tế của điện, máy, Internet và thời gian đã có.

## D07 — Local/private research tại Việt Nam

**Quyết định:** MVP chỉ dùng nội bộ để nghiên cứu và paper trading; không public, không bán, không nhận tiền, không giữ tài sản, không giao dịch thật.

**Lý do:**

- Giữ đúng product/risk boundary.
- Tránh giả định self-review thay thế tư vấn pháp lý độc lập.
- Quy định và điều khoản có thể thay đổi theo thời gian.

**Hệ quả:**

- Disclaimer và known limitations luôn hiện diện.
- Trước public/commercial/live cần legal/security gate mới, có thể không còn đáp ứng 0 VNĐ.
- Không gọi crypto perpetual là chứng khoán nếu không có cơ sở pháp lý phù hợp.

## D08 — Risk reference 0,25–0,5%

**Quyết định:** nếu output có risk sizing tham khảo, mức rủi ro tối đa mặc định là 0,25–0,5% hypothetical equity/tín hiệu; không khuyến nghị đòn bẩy cao.

**Lý do:**

- Futures có đòn bẩy và tail risk.
- Model confidence không loại bỏ nguy cơ thua lỗ/liquidation.
- Risk engine phải độc lập với model.

**Hệ quả:**

- Đây là giới hạn mô phỏng/tham khảo, không phải tư vấn phù hợp cho mọi người.
- Hard risk gate có quyền chuyển signal thành `NO_TRADE`.
- Không martingale hoặc tăng size để gỡ lỗ.
- Mọi thay đổi risk band cần ADR/policy version mới.

## Các lựa chọn đã không chọn

| Lựa chọn | Lý do không chọn trong MVP |
|---|---|
| Luôn trả Long hoặc Short | Tạo giao dịch khi không có edge; xác suất sai cao |
| Chỉ dùng ảnh, không lấy market data | Khó xác minh timestamp/symbol/nến đóng; mất dữ liệu phái sinh |
| Hỗ trợ nhiều altcoin | Tăng data/model/validation cost và regime heterogeneity |
| Public free-tier hosting | Không bảo đảm miễn phí, quota, privacy hoặc SLA |
| Auto-trading testnet ngay từ đầu | Làm rộng scope trước khi chứng minh research pipeline |
| Auto-trading tiền thật | Rủi ro vốn, security, legal và execution vượt MVP |
| Thuê GPU để train vision | Vi phạm ngân sách 0 VNĐ |

## Exit Gate A verification

- [x] D01 có quyết định, lý do và hệ quả.
- [x] D02 có horizon chính và horizon phụ rõ ràng.
- [x] D03 khóa product/symbol scope.
- [x] D04 khóa nguồn ảnh và domain-quality condition.
- [x] D05 khóa user/private boundary.
- [x] D06 khóa zero-cost boundary.
- [x] D07 khóa local/research/legal boundary.
- [x] D08 khóa risk reference.
- [x] Không có public hosting trong MVP.
- [x] Không có auto-trading trong MVP.

**Kết luận:** `PASS — ADR-0001 ACCEPTED`.

## Supersession rule

ADR này chỉ bị thay thế bởi ADR mới có liên kết ngược, lý do và tác động đầy đủ. Không sửa status `ACCEPTED` thành một quyết định khác mà không lưu lịch sử.
