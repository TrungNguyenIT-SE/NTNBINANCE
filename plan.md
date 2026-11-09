# KẾ HOẠCH A–Z: HỆ THỐNG DỰ ĐOÁN BINANCE FUTURES TỪ ẢNH NẾN 1H + 15M

> Phiên bản: 1.2 — bổ sung checklist thực thi A–Z  
> Ngày lập: 09/11/2026  
> Trạng thái hiện tại: **Giai đoạn C hoàn tất / 3 trên 26 giai đoạn / 11,54%**  
> Phạm vi mặc định: Binance USDⓈ-M Perpetual, phát tín hiệu `LONG / SHORT / NO_TRADE`; chưa tự động đặt lệnh ở MVP.  
> Ràng buộc bắt buộc: **chi phí tiền mặt tăng thêm để xây và chạy MVP = 0 VNĐ**.

### 0. Nguyên tắc “0 đồng” — ràng buộc không được vi phạm

Kế hoạch này hiểu “không tốn phí” là **không mua phần mềm, không thuê máy chủ/GPU, không mua domain, không trả phí API, không thuê dịch vụ SaaS và không thuê tư vấn bên ngoài**. Dự án tận dụng máy tính, điện và kết nối Internet mà chủ dự án đã có. Nếu tính cả khấu hao máy, điện, Internet, thời gian lao động hoặc vốn giao dịch thì không có dự án thực tế nào có chi phí kinh tế tuyệt đối bằng 0; các khoản này được xem là tài nguyên sẵn có, không phải khoản chi mới.

Các quy tắc bắt buộc:

- Chạy local trên Windows hiện có; chỉ truy cập qua `localhost` hoặc LAN riêng ở MVP.
- Chỉ dùng phần mềm mã nguồn mở/miễn phí, kiểm tra license trước khi đưa vào repo.
- Chỉ dùng API market data công khai của Binance; không mua data vendor.
- Không thuê cloud, GPU, database, object storage, monitoring, email/SMS, CAPTCHA hoặc CDN.
- Không mua domain/SSL; không cam kết public Internet trong phạm vi 0 đồng.
- Không thuê luật sư, pentest hay audit. Thay bằng tự rà soát và công cụ miễn phí; điều này **không tương đương** chứng nhận pháp lý hoặc kiểm thử độc lập.
- Không nạp tiền và không đặt lệnh thật trong MVP; paper trading dùng sổ lệnh mô phỏng.
- Free tier của bên thứ ba không được coi là nền tảng bắt buộc vì điều khoản/hạn mức có thể thay đổi hoặc yêu cầu thẻ thanh toán.
- Bất kỳ tính năng nào phát sinh phí phải được feature-flag tắt và cần một quyết định thay đổi phạm vi riêng.
- Binance API và Internet là phụ thuộc bên ngoài: nếu bị giới hạn theo IP/khu vực/điều khoản, hệ thống chỉ dùng dữ liệu đã cache hoặc tạm dừng; không mua proxy/VPN/data thay thế.

Phân biệt rõ hai loại “chi phí” trong tài liệu:

1. **Chi phí dự án:** tiền xây/vận hành phần mềm — bắt buộc bằng 0 VNĐ trong MVP.
2. **Chi phí giao dịch mô phỏng:** fee, spread, funding, slippage — vẫn phải tính trong nhãn/backtest để kết quả không bị ảo; MVP không thực trả các khoản này vì không giao dịch thật.

---

## CHECKLIST THỰC THI A–Z

Đây là bảng điều khiển tiến độ chính. Thực hiện đúng thứ tự từ A đến Z; không bắt đầu giai đoạn phụ thuộc khi giai đoạn trước chưa qua Exit Gate.

### Quy tắc tick

- Chỉ đổi `[ ]` thành `[x]` khi đầu việc đã hoàn thành và có bằng chứng kiểm tra được.
- Chỉ tick dòng **Hoàn tất giai đoạn** khi mọi checkbox con của giai đoạn đã tick và Exit Gate đạt.
- Nếu một mục không áp dụng, ghi `[x] N/A — lý do: ...`; không xóa mục.
- Nếu Gate không đạt, ghi nguyên nhân vào `docs/decisions/` hoặc `reports/`, sửa lỗi rồi kiểm tra lại; không hạ ngưỡng sau khi đã xem final test chỉ để được pass.
- Mỗi bằng chứng nên là đường dẫn file trong repo, mã commit hoặc báo cáo có ngày tạo.
- Tiến độ tổng = số giai đoạn đã hoàn tất / 26 × 100%; không tính theo số checkbox nhỏ.

### Bảng tiến độ tổng

- [x] A — Chốt bài toán và phạm vi
- [x] B — Kiểm kê tài nguyên và khóa ngân sách 0 VNĐ
- [x] C — Khởi tạo repository và tiêu chuẩn kỹ thuật
- [ ] D — Đặc tả dữ liệu và hợp đồng thời gian
- [ ] E — Thu thập dữ liệu Binance
- [ ] F — Làm sạch và kiểm định dữ liệu
- [ ] G — Định nghĩa nhãn dự đoán
- [ ] H — Chia tập dữ liệu chống leakage
- [ ] I — Xây baseline
- [ ] J — Xây backtest đáng tin cậy
- [ ] K — Đặc tả ảnh đầu vào
- [ ] L — Xây upload ảnh an toàn
- [ ] M — Xử lý và hiểu ảnh
- [ ] N — Xây numeric features
- [ ] O — Huấn luyện và chọn mô hình hybrid
- [ ] P — Calibration, uncertainty và `NO_TRADE`
- [ ] Q — Risk engine
- [ ] R — Backend API và job lifecycle
- [ ] S — Giao diện web local
- [ ] T — Kiểm thử toàn hệ thống
- [ ] U — Logging, monitoring và cảnh báo local
- [ ] V — Versioning, model registry và reproducibility
- [ ] W — Walk-forward và paper trading
- [ ] X — Rà soát bảo mật, riêng tư và pháp lý
- [ ] Y — Nghiệm thu Go/No-Go
- [ ] Z — Đóng gói local release và bàn giao

**Tiến độ hiện tại:** `3/26 giai đoạn = 11,54%`  
**Giai đoạn đang làm:** `D`  
**Ngày cập nhật:** `09/11/2026`

### A — Chốt bài toán và phạm vi

- [x] Viết `docs/PRD.md`: người dùng, vấn đề, input, output, non-goals.
- [x] Chốt D01–D08 trong mục 2.3; không còn quyết định bắt buộc để trống.
- [x] Chốt `BTCUSDT`, `ETHUSDT`, USDⓈ-M perpetual cho MVP.
- [x] Chốt input gồm ảnh 1H + 15m của cùng symbol và thời điểm.
- [x] Chốt output ba lớp `LONG / SHORT / NO_TRADE`.
- [x] Chốt horizon chính 4 nến 15m; 2 và 8 nến chỉ là phân tích phụ.
- [x] Chốt MVP chỉ nghiên cứu/paper trading, không đặt lệnh thật.
- [x] Viết acceptance criteria có thể đo được.
- [x] **Hoàn tất A — PRD được khóa phiên bản 1.0.**

**Exit Gate A:** mọi quyết định D01–D08 có câu trả lời; phạm vi không chứa public hosting hoặc auto-trading.  
**Bằng chứng:** `docs/PRD.md`, `docs/decisions/`

### B — Kiểm kê tài nguyên và khóa ngân sách 0 VNĐ

- [x] Ghi CPU, RAM, GPU, dung lượng trống, hệ điều hành vào `docs/HARDWARE.md`.
- [x] Benchmark đọc/ghi disk, CPU và inference mẫu; lưu kết quả ban đầu.
- [x] Đặt trần disk/RAM/CPU và thời gian train.
- [x] Xác nhận chỉ dùng máy, điện và Internet đã có.
- [x] Xác nhận không nhập thẻ/thông tin thanh toán vào dịch vụ nào.
- [x] Lập `THIRD_PARTY_LICENSES.md` và quy trình kiểm tra license.
- [x] Xác nhận localhost/LAN là phạm vi triển khai.
- [x] Lập bảng ngân sách với tổng chi mới `0 VNĐ`.
- [x] **Hoàn tất B — Resource budget và zero-cost gate được ký xác nhận.**

**Exit Gate B:** không có dependency bắt buộc trả phí; cấu hình máy đủ chạy spike tối thiểu.  
**Bằng chứng:** `docs/HARDWARE.md`, `docs/ZERO_COST.md`, `THIRD_PARTY_LICENSES.md`

### C — Khởi tạo repository và tiêu chuẩn kỹ thuật

- [x] Tạo cấu trúc `apps/`, `src/`, `tests/`, `data/`, `models/`, `reports/`, `docs/`.
- [x] Tạo `.gitignore`; loại `.env`, secret, upload, database và model lớn khỏi Git.
- [x] Tạo Python virtual environment và khóa dependency.
- [x] Khởi tạo frontend được chọn sau spike React/Vite hoặc Jinja.
- [x] Cấu hình formatter, linter, type check, pytest và pre-commit chạy local.
- [x] Tạo `README.md` với lệnh setup/run/test.
- [x] Tạo config `local-dev`, `local-test`, `local-release`.
- [x] Chạy smoke test sạch từ một checkout/thư mục mới.
- [x] **Hoàn tất C — repository có thể dựng lại bằng tài liệu.**

**Exit Gate C:** một lệnh hoặc chuỗi lệnh được tài liệu hóa có thể setup và chạy smoke test.  
**Bằng chứng:** `README.md`, lockfile, log `reports/setup-smoke.txt`

### D — Đặc tả dữ liệu và hợp đồng thời gian

- [ ] Viết data dictionary cho OHLCV, mark/index price, funding, OI và metadata.
- [ ] Quy định UTC cho storage; timezone chỉ đổi ở UI.
- [ ] Định nghĩa rõ `event_time`, `open_time`, `close_time`, `ingested_at`, `decision_time`.
- [ ] Quy định chỉ dùng nến `is_closed=true` khi dự đoán.
- [ ] Định nghĩa unique key, schema version và quality flags.
- [ ] Định nghĩa raw/clean/feature layer trên Parquet/DuckDB.
- [ ] Định nghĩa retention cho ảnh, logs, raw data và artifacts.
- [ ] Viết invariant tests trước khi ingest lớn.
- [ ] **Hoàn tất D — data contract được khóa.**

**Exit Gate D:** timestamp semantics không mơ hồ và có test chống dùng nến chưa đóng.  
**Bằng chứng:** `docs/DATA_DICTIONARY.md`, `docs/DATA_CONTRACT.md`, `tests/data_contract/`

### E — Thu thập dữ liệu Binance

- [ ] Viết REST client có timeout, retry hữu hạn, backoff + jitter.
- [ ] Đọc rate limit động/response headers; xử lý 429/418/5xx.
- [ ] Backfill OHLCV BTCUSDT và ETHUSDT ở độ phân giải gốc đã chọn.
- [ ] Thu mark/index price, funding và feature phái sinh có coverage phù hợp.
- [ ] Viết WebSocket client có heartbeat, reconnect và resubscribe.
- [ ] Reconcile stream với REST sau reconnect/gap.
- [ ] Lưu raw append-only kèm source và ingestion timestamp.
- [ ] Không dùng API trading key; không log credential.
- [ ] **Hoàn tất E — pipeline ingest chạy lại được và không tạo duplicate.**

**Exit Gate E:** ingest liên tục 24 giờ thử nghiệm hoặc qua một chu kỳ vận hành tương đương, gap được phát hiện/recover.  
**Bằng chứng:** `reports/ingestion-qa.md`, manifest raw data, logs thử nghiệm

### F — Làm sạch và kiểm định dữ liệu

- [ ] Test invariant OHLC và volume không âm.
- [ ] Phát hiện duplicate, missing bar, out-of-order và clock skew.
- [ ] Gắn quality flag thay vì âm thầm sửa dữ liệu.
- [ ] Resample 1m/5m sang 15m và 1H theo UTC, chỉ từ nến đóng.
- [ ] So sánh mẫu resample với dữ liệu Binance cùng interval.
- [ ] Lập báo cáo coverage theo symbol/ngày/feature.
- [ ] Quarantine partition lỗi và hỗ trợ reprocess idempotent.
- [ ] Xác nhận ≥ 99,9% expected bars hoặc giải thích mọi gap bị loại.
- [ ] **Hoàn tất F — Gate A/Data pass.**

**Exit Gate F:** không có lỗi data Critical; mọi gap ảnh hưởng training được loại/flag có chủ đích.  
**Bằng chứng:** `reports/data-quality.md`, `tests/data_quality/`

### G — Định nghĩa nhãn dự đoán

- [ ] Viết `LABEL_SPEC.md` cho triple-barrier.
- [ ] Chốt ATR/window và upper/lower/vertical barriers bằng train/validation protocol.
- [ ] Quy định `LONG`, `SHORT`, `NO_TRADE` rõ ràng.
- [ ] Quy định cách xử lý hai barrier cùng chạm trong một bar.
- [ ] Đưa fee, spread, slippage, funding và latency giả lập vào net label.
- [ ] Unit test các case biên bằng dữ liệu nhỏ tính tay.
- [ ] Version hóa label config; không thay âm thầm.
- [ ] Kiểm tra phân bố lớp theo thời gian/symbol/regime.
- [ ] **Hoàn tất G — label v1 có test và review.**

**Exit Gate G:** cùng input + config luôn tạo cùng label; không đọc dữ liệu sau vertical barrier.  
**Bằng chứng:** `docs/LABEL_SPEC.md`, `tests/labels/`, `reports/label-distribution.md`

### H — Chia tập dữ liệu chống leakage

- [ ] Chốt train/validation/test theo thời gian.
- [ ] Khóa final holdout và lưu hash/manifest.
- [ ] Áp dụng purged walk-forward + embargo ≥ prediction horizon.
- [ ] Ngăn các window/sample chồng lấn đi qua split boundary.
- [ ] Fit scaler/selector/calibrator chỉ trên partition hợp lệ.
- [ ] Split sample gốc trước augmentation ảnh.
- [ ] Viết automated leakage tests.
- [ ] Ghi ai/khi nào được phép mở final holdout.
- [ ] **Hoàn tất H — dataset split v1 bị khóa.**

**Exit Gate H:** leakage test pass; final test chưa được dùng để chọn feature/model/threshold.  
**Bằng chứng:** `data/manifests/split-v1.*`, `tests/leakage/`, `reports/split-audit.md`

### I — Xây baseline

- [ ] Đo majority/random/always-no-trade baseline.
- [ ] Xây rule baseline: trend 1H + trigger 15m + ATR filter.
- [ ] Xây Logistic Regression baseline.
- [ ] Xây LightGBM/XGBoost baseline nếu chạy được trên máy.
- [ ] Ghi accuracy, macro F1, per-class precision/recall và calibration.
- [ ] Backtest baseline bằng cùng cost model.
- [ ] Lưu config, seed, data version và artifact.
- [ ] Chọn baseline chính để model phức tạp phải vượt qua.
- [ ] **Hoàn tất I — baseline report được khóa.**

**Exit Gate I:** kết quả reproduce được từ script; không báo cáo chỉ một metric thuận lợi.  
**Bằng chứng:** `reports/baseline-v1.md`, `models/baselines/`

### J — Xây backtest đáng tin cậy

- [ ] Viết event timeline: decision → latency → entry → manage → exit.
- [ ] Không fill tại giá close lý tưởng nếu thực tế không thể biết/khớp.
- [ ] Mô phỏng spread, slippage, fee, funding và partial/unfilled rule.
- [ ] Áp dụng tick size, step size và minimum constraints cần thiết.
- [ ] Unit test no-lookahead và giá trị PnL tính tay.
- [ ] Báo cáo gross/net PnL, expectancy, PF, drawdown, Sharpe/Sortino.
- [ ] Stress cost ×1, ×1.5, ×2 và latency tăng.
- [ ] Phân tích theo symbol, long/short, tháng, regime và confidence bucket.
- [ ] **Hoàn tất J — backtest engine v1 được nghiệm thu.**

**Exit Gate J:** thay chi phí/latency làm kết quả biến đổi hợp lý; audit không phát hiện future data.  
**Bằng chứng:** `tests/backtest/`, `reports/backtest-validation.md`

### K — Đặc tả ảnh đầu vào

- [ ] Chốt PNG/JPEG/WebP, 10 MB, 800–4096 px hoặc điều chỉnh theo benchmark.
- [ ] Định nghĩa số nến/vùng chart tối thiểu.
- [ ] Tạo rubric pass/reject cho blur, crop, che chart và sai theme.
- [ ] Tạo golden set ảnh hợp lệ và lỗi.
- [ ] Quy định symbol/timeframe/timestamp do user khai báo và OCR đối chiếu.
- [ ] Quy định stale threshold và tolerance giá cuối ảnh.
- [ ] Quy định mismatch 1H/15m phải reject hoặc `NO_TRADE`.
- [ ] Viết hướng dẫn chụp ảnh cho người dùng.
- [ ] **Hoàn tất K — image input specification v1 được khóa.**

**Exit Gate K:** hai người hoặc hai lượt review độc lập cho cùng golden set cho kết quả rubric nhất quán chấp nhận được.  
**Bằng chứng:** `docs/IMAGE_SPEC.md`, `tests/fixtures/images/`, `reports/image-rubric.md`

### L — Xây upload ảnh an toàn

- [ ] Giới hạn request bytes trước khi đọc toàn bộ file.
- [ ] Kiểm tra magic bytes/MIME và decode thật.
- [ ] Giới hạn tổng pixel để chống decompression bomb.
- [ ] Re-encode, loại metadata/EXIF và đặt tên bằng UUID/hash.
- [ ] Lưu ngoài web root; chặn path traversal.
- [ ] Kiểm tra quyền đọc/xóa theo user/session.
- [ ] Rate limit local và cleanup upload hết hạn.
- [ ] Test ảnh giả MIME, file hỏng, quá lớn, trùng và malicious filename.
- [ ] **Hoàn tất L — secure upload tests pass.**

**Exit Gate L:** không thể đọc file người khác hoặc ghi file ra ngoài storage root qua API.  
**Bằng chứng:** `tests/security_upload/`, `reports/upload-security.md`

### M — Xử lý và hiểu ảnh

- [ ] Phát hiện/crop vùng chart và giữ aspect ratio.
- [ ] Đo blur/quality/layout bằng pipeline local.
- [ ] OCR symbol, timeframe, timestamp/price khi nhìn thấy.
- [ ] Cross-check OCR với input user và market data.
- [ ] Render synthetic chart từ OHLCV mà không chứa tương lai.
- [ ] Augment chỉ trong train; không lật ngang/thay đổi ý nghĩa thời gian.
- [ ] Đo performance theo theme sáng/tối, độ phân giải và nguồn ảnh.
- [ ] Fail-safe về reject/`NO_TRADE` khi OOD hoặc quality thấp.
- [ ] **Hoàn tất M — image pipeline đạt tiêu chí golden set.**

**Exit Gate M:** lỗi mismatch/stale/ảnh không phải chart được bắt theo ngưỡng đã khóa; không tune bằng final test.  
**Bằng chứng:** `reports/image-pipeline.md`, `tests/image_pipeline/`

### N — Xây numeric features

- [ ] Implement returns, volatility, ATR, range và wick/body.
- [ ] Implement trend 1H và trigger 15m.
- [ ] Implement volume/taker/trade-count features có coverage đủ.
- [ ] Thêm funding/OI/basis chỉ khi point-in-time coverage đạt.
- [ ] Định nghĩa missing-value rule cho từng feature.
- [ ] Viết feature registry: công thức, window, timestamp, version.
- [ ] Point-in-time correctness test cho mọi feature.
- [ ] Ablation loại feature không ổn định/không có giá trị.
- [ ] **Hoàn tất N — feature set v1 bị khóa.**

**Exit Gate N:** tạo feature tại thời điểm T không truy cập record có event_time > T.  
**Bằng chứng:** `docs/FEATURE_REGISTRY.md`, `tests/features/`, `reports/feature-ablation.md`

### O — Huấn luyện và chọn mô hình hybrid

- [ ] Train numeric-only champion candidate.
- [ ] Train image-only benchmark để đo giá trị thật của ảnh.
- [ ] Train fusion candidate 1H + 15m + numeric + quality.
- [ ] Cố định seed/config/data/model version.
- [ ] So sánh chất lượng, latency, RAM và kích thước artifact.
- [ ] Chỉ tune trên train/validation.
- [ ] Chạy ablation numeric-only/image-only/hybrid.
- [ ] Chọn model đơn giản nhất đạt cải thiện có ý nghĩa.
- [ ] **Hoàn tất O — champion candidate được chọn.**

**Exit Gate O:** candidate vượt baseline trên validation và phù hợp resource budget; nếu vision không tăng giá trị thì dùng numeric model + image quality validation.  
**Bằng chứng:** `reports/model-selection.md`, `models/candidates/`

### P — Calibration, uncertainty và `NO_TRADE`

- [ ] Calibrate xác suất trên validation bằng phương pháp đã chọn.
- [ ] Đo Brier score, reliability diagram và ECE.
- [ ] Chọn confidence/expected-return threshold trên validation.
- [ ] Implement quality gate, OOD/stale/mismatch gate.
- [ ] Đo coverage so với precision/expectancy.
- [ ] Kiểm thử confidence bucket có đủ sample.
- [ ] Khóa threshold trước final holdout.
- [ ] Bảo đảm hệ thống không bao giờ buộc Long/Short.
- [ ] **Hoàn tất P — policy `NO_TRADE` v1 được khóa.**

**Exit Gate P:** xác suất calibration tốt hơn bản raw hoặc có giải thích rõ; case thiếu tin cậy luôn abstain.  
**Bằng chứng:** `reports/calibration.md`, `configs/signal-policy-v1.*`

### Q — Risk engine

- [ ] Tách risk engine khỏi model inference.
- [ ] Implement hard reject cho stale, gap, OOD và volatility cực đoan.
- [ ] Định nghĩa entry/invalidation/SL/TP từ rule có version.
- [ ] Giới hạn rủi ro tham khảo 0,25–0,5%/tín hiệu.
- [ ] Implement daily loss/drawdown circuit breaker cho paper ledger.
- [ ] Không martingale và không tự tăng leverage.
- [ ] Implement model/data kill switch.
- [ ] Unit test mọi hard limit và thứ tự rule.
- [ ] **Hoàn tất Q — risk policy v1 pass test.**

**Exit Gate Q:** không model output nào có thể bypass hard risk rule.  
**Bằng chứng:** `docs/RISK_POLICY.md`, `tests/risk_engine/`

### R — Backend API và job lifecycle

- [ ] Implement upload, create/get/list prediction và feedback endpoints.
- [ ] Validate schema và giới hạn input bằng Pydantic.
- [ ] Implement state machine prediction đầy đủ.
- [ ] Implement idempotency key và chống prediction trùng.
- [ ] Implement timeout, retry hữu hạn và failed-job handling trong SQLite.
- [ ] Lưu audit record, model version, feature version và request ID.
- [ ] Không trả stack trace/path nội bộ/secret.
- [ ] Xuất OpenAPI và chạy contract tests.
- [ ] **Hoàn tất R — API integration tests pass.**

**Exit Gate R:** request hợp lệ đi hết state machine; retry không nhân đôi kết quả.  
**Bằng chứng:** `docs/openapi.*`, `tests/api/`, `reports/api-test.md`

### S — Giao diện web local

- [ ] Xây chọn symbol và hai vùng upload 1H/15m.
- [ ] Hiển thị preview, quality/mismatch errors và cách sửa.
- [ ] Hiển thị trạng thái job và retry an toàn.
- [ ] Hiển thị signal, confidence, validity, risk levels và lý do.
- [ ] Luôn hiển thị disclaimer; không dùng “chắc thắng”.
- [ ] Xây history, filter và outcome tách khỏi prediction.
- [ ] Test responsive desktop/mobile cơ bản và keyboard accessibility.
- [ ] Không tải asset/font/script runtime từ CDN bắt buộc.
- [ ] **Hoàn tất S — E2E user journey chạy local.**

**Exit Gate S:** người dùng mới làm được upload → kết quả → history mà không cần terminal.  
**Bằng chứng:** `tests/e2e/`, screenshots/video local, `reports/usability.md`

### T — Kiểm thử toàn hệ thống

- [ ] Unit tests cho label, feature, backtest, risk và image validation.
- [ ] Integration tests cho Binance adapter, DB, filesystem, worker và model.
- [ ] E2E happy path và các input lỗi bắt buộc.
- [ ] Property tests cho no-future-data, OHLC invariant và idempotency.
- [ ] Load test theo resource budget của máy.
- [ ] Failure tests: API 429/5xx, disconnect, worker crash, disk gần đầy.
- [ ] Regression golden set cho ảnh và predictions cố định.
- [ ] Ghi coverage và danh sách test còn thiếu.
- [ ] **Hoàn tất T — test suite release pass.**

**Exit Gate T:** Critical/High functional defect = 0; test chạy lại được bằng lệnh tài liệu hóa.  
**Bằng chứng:** `reports/test-report.md`, test logs, coverage report

### U — Logging, monitoring và cảnh báo local

- [ ] Structured log có timestamp UTC, level, request ID; không chứa ảnh/secret.
- [ ] Metrics data freshness, queue age, latency, error và class distribution.
- [ ] Dashboard/report local cho CPU, RAM, disk và resource thresholds.
- [ ] Alert local cho stale data, inference fail, disk 70/85/95%.
- [ ] Log rotation và retention để không đầy ổ.
- [ ] Health live/ready phản ánh dependency thật.
- [ ] Viết runbook reconnect, bad data, rollback và disk full.
- [ ] Diễn tập ít nhất hai incident giả lập.
- [ ] **Hoàn tất U — observability/runbook hoạt động.**

**Exit Gate U:** lỗi giả lập được phát hiện, chẩn đoán và recovery theo runbook.  
**Bằng chứng:** `docs/runbooks/`, `reports/incident-drills.md`

### V — Versioning, model registry và reproducibility

- [ ] Version data, split, label, feature, model, calibration và risk policy.
- [ ] Lưu Git SHA, config, seed, package lock và hardware info.
- [ ] Lưu checksum model/artifact và manifest.
- [ ] Viết model card: mục đích, dữ liệu, metrics, hạn chế, rủi ro.
- [ ] Script reproduce training/evaluation từ manifest.
- [ ] Implement active/challenger/retired status trong local registry.
- [ ] Implement atomic model switch và rollback.
- [ ] Thử reproduce một run từ đầu và so sánh dung sai.
- [ ] **Hoàn tất V — model registry/reproduce gate pass.**

**Exit Gate V:** có thể xác định chính xác model/config/data đã tạo mọi prediction.  
**Bằng chứng:** `models/registry/`, `docs/MODEL_CARD.md`, `reports/reproducibility.md`

### W — Walk-forward và paper trading

- [ ] Chạy purged walk-forward trên các fold đã định nghĩa.
- [ ] Mở final holdout đúng một lần sau khi khóa pipeline.
- [ ] Ghi final report không tune lại theo test.
- [ ] Freeze model/policy cho forward paper cohort.
- [ ] Chạy paper trading 8–12 tuần hoặc đến ≥ 300 signal độc lập theo điều kiện chặt hơn.
- [ ] Reconcile prediction, intended fill, cost và realized outcome.
- [ ] Theo dõi expectancy, PF, drawdown, calibration, coverage và drift.
- [ ] So sánh backtest/paper; điều tra mọi chênh lệch lớn.
- [ ] **Hoàn tất W — Gate C/Paper có kết luận pass hoặc no-go.**

**Exit Gate W:** chỉ pass nếu expectancy net dương, risk limit không bị vi phạm và kết quả không phụ thuộc vài outlier; nếu không thì ghi No-Go.  
**Bằng chứng:** `reports/final-holdout.md`, `reports/paper-trading.md`

### X — Rà soát bảo mật, riêng tư và pháp lý

- [ ] Chạy secret, dependency và license scan local.
- [ ] Chạy OWASP ZAP Community với local app.
- [ ] Test authz/IDOR, path traversal, file bomb, malformed image và rate limit.
- [ ] Kiểm tra retention/deletion và quyền truy cập upload.
- [ ] Xác nhận upload không được dùng train khi chưa opt-in.
- [ ] Xác nhận không public, không thu tiền, không giữ tài sản, không auto-trade.
- [ ] Rà lại điều khoản Binance/API và nguồn ảnh tại ngày release.
- [ ] Ghi rõ giới hạn self-review, không tuyên bố đã được audit độc lập.
- [ ] **Hoàn tất X — self-review không còn Critical/High đã biết.**

**Exit Gate X:** Critical/High = 0; mọi Medium có owner, biện pháp và hạn xử lý.  
**Bằng chứng:** `reports/security-self-review.md`, `docs/PRIVACY.md`, `docs/TERMS_NOTES.md`

### Y — Nghiệm thu Go/No-Go

- [ ] Đối chiếu Gate A/Data, B/Research, C/Paper và D/Private beta.
- [ ] Đối chiếu từng KPI với report gốc; không chép metric thiếu context.
- [ ] Xác nhận latency/RAM/disk đạt resource budget.
- [ ] Xác nhận tổng chi mới vẫn 0 VNĐ.
- [ ] Xác nhận backup/restore thật hoặc công khai “không có backup an toàn”.
- [ ] Liệt kê known limitations và residual risks.
- [ ] Ghi quyết định `GO`, `CONDITIONAL GO` hoặc `NO-GO` cùng lý do.
- [ ] Nếu No-Go, tạo corrective backlog; không chuyển sang Z như đã pass.
- [ ] **Hoàn tất Y — biên bản nghiệm thu được khóa.**

**Exit Gate Y:** chỉ `GO` mới được đóng gói release; `CONDITIONAL GO` chỉ cho nhóm nội bộ với điều kiện ghi rõ.  
**Bằng chứng:** `reports/GO_NO_GO.md`, `docs/KNOWN_LIMITATIONS.md`

### Z — Đóng gói local release và bàn giao

- [ ] Tạo script setup/start/stop/backup/restore cho Windows local.
- [ ] Test cài mới trong môi trường/thư mục sạch.
- [ ] Pin dependency và tạo checksum release artifacts.
- [ ] Viết user guide, admin guide, troubleshooting và uninstall guide.
- [ ] Đóng gói model/data sample hợp lệ, không chứa secret/upload cá nhân.
- [ ] Chạy smoke, regression và security checklist lần cuối.
- [ ] Gắn version/tag local release và tạo release notes.
- [ ] Cập nhật progress `26/26 = 100%` chỉ khi tất cả Gate pass.
- [ ] **Hoàn tất Z — local/private MVP được bàn giao.**

**Exit Gate Z:** một máy Windows phù hợp có thể setup và hoàn thành user journey theo tài liệu, không phát sinh khoản thanh toán mới.  
**Bằng chứng:** `docs/RELEASE_CHECKLIST.md`, `docs/USER_GUIDE.md`, `reports/release-smoke.md`

---

## 1. Tóm tắt điều hành

Sản phẩm cho phép người dùng tải lên hai ảnh biểu đồ nến của cùng một cặp giao dịch:

- Ảnh khung **1 giờ (1H)** để nhận diện xu hướng và chế độ thị trường.
- Ảnh khung **15 phút (15m)** để xác định thời điểm vào lệnh.

Hệ thống kiểm tra ảnh, nhận diện symbol/thời gian nếu có thể, đồng bộ với dữ liệu thị trường Binance, sau đó trả về:

- Kết quả: `LONG`, `SHORT` hoặc `NO_TRADE`.
- Độ tin cậy đã hiệu chỉnh xác suất, không phải “tỷ lệ chắc thắng”.
- Vùng entry tham khảo, điểm vô hiệu, stop-loss, take-profit và tỷ lệ risk/reward.
- Thời hạn hiệu lực của tín hiệu.
- Lý do chính, cảnh báo dữ liệu và điều kiện khiến tín hiệu mất hiệu lực.

### Kết luận thiết kế quan trọng

1. **Không nên dự đoán chỉ từ pixel của ảnh.** Ảnh có thể bị crop, đổi theme, thay scale, chứa nến đang chạy hoặc thiếu symbol/thời gian. Thiết kế chính phải là **mô hình hybrid**: ảnh + dữ liệu OHLCV chuẩn từ Binance + dữ liệu phái sinh.
2. **Không ép mô hình chọn Long hoặc Short.** Lớp `NO_TRADE` là bắt buộc khi tín hiệu yếu, ảnh lỗi, thị trường bất thường hoặc kỳ vọng sau chi phí không dương.
3. **Không tối ưu theo accuracy đơn thuần.** Tiêu chí chính là expectancy/PnL sau phí, funding và slippage; kèm drawdown, Sharpe/Sortino, calibration và độ ổn định out-of-sample.
4. **MVP chỉ phát tín hiệu.** Paper trading phải chạy ổn định trước; tự động giao dịch tiền thật là phase riêng, cần kiểm tra pháp lý, bảo mật và phê duyệt rủi ro.
5. **Không cam kết lợi nhuận.** Đây là hệ thống xác suất cho thị trường đòn bẩy, có thể sai và có thể mất toàn bộ vốn nếu quản trị rủi ro kém.

---

## 2. Phạm vi và giả định

### 2.1. Phạm vi MVP đề xuất

- Thị trường: Binance USDⓈ-M Perpetual.
- Symbol ban đầu: `BTCUSDT`, `ETHUSDT`; chỉ mở rộng khi từng symbol vượt cổng đánh giá.
- Input bắt buộc:
  - 01 ảnh 1H.
  - 01 ảnh 15m.
  - Symbol do người dùng chọn rõ ràng.
  - Thời điểm chụp hoặc lựa chọn “ảnh vừa chụp”.
- Output: `LONG / SHORT / NO_TRADE`, confidence, entry/invalidation/SL/TP, thời hạn tín hiệu và giải thích.
- Nền tảng: web responsive; desktop ưu tiên cho MVP.
- Ngôn ngữ: tiếng Việt trước, kiến trúc sẵn sàng i18n.
- Chưa có trong MVP: copy trading, giữ tiền người dùng, auto-order, social feed, app mobile native, hàng trăm symbol.

### 2.2. Giả định nguồn ảnh

- Ảnh có thể đến từ Binance hoặc TradingView.
- Hai ảnh phải cùng symbol và thời điểm gần nhau.
- Hỗ trợ PNG/JPEG/WebP; không nhận SVG/PDF trong MVP.
- Hạn mức đề xuất: tối đa 10 MB/ảnh, cạnh 800–4096 px.
- Không tin metadata từ client; server phải kiểm tra MIME thực, kích thước, decode và loại bỏ metadata.

### 2.3. Các quyết định sản phẩm đã chốt tại Giai đoạn A

| Mã | Quyết định | Giá trị đã khóa | Trạng thái |
|---|---|---|---|
| D01 | Chỉ báo tín hiệu hay tự đặt lệnh? | Chỉ báo tín hiệu ở MVP | Accepted |
| D02 | Chân trời dự đoán | 4 nến 15m tiếp theo (60 phút); 2 và 8 nến là phân tích phụ | Accepted |
| D03 | Thị trường đầu tiên | BTCUSDT và ETHUSDT USDⓈ-M perpetual | Accepted |
| D04 | Nguồn ảnh | Binance + TradingView, template được kiểm định | Accepted |
| D05 | Người dùng | Nhóm nội bộ/private beta | Accepted |
| D06 | Ngân sách hạ tầng | 0 VNĐ; CPU/RAM/ổ đĩa của máy hiện có, GPU local nếu máy đã có | Accepted |
| D07 | Khu vực pháp lý | Việt Nam; MVP local/private, không public và không nhận tiền/giao dịch thật | Accepted |
| D08 | Mức rủi ro mặc định | Rủi ro tham khảo tối đa 0,25–0,5% tài khoản/tín hiệu; không khuyến nghị đòn bẩy cao | Accepted |

Bằng chứng khóa quyết định: [`docs/PRD.md`](docs/PRD.md) và [`docs/decisions/0001-mvp-product-decisions.md`](docs/decisions/0001-mvp-product-decisions.md).

---

## 3. Mục tiêu, KPI và tiêu chí thành công

### 3.1. Mục tiêu sản phẩm

- Mục tiêu ban đầu **≤ 5 giây p95** trên máy hiện có; Sprint 0 phải benchmark. Nếu không đạt, công bố SLO thực đo (tối đa đề xuất 15 giây) hoặc dùng model nhẹ hơn, không thuê compute.
- Kết quả có thể truy vết về model version, data snapshot và logic risk tương ứng.
- Hệ thống từ chối hoặc trả `NO_TRADE` thay vì suy đoán khi ảnh không đạt chất lượng.
- Không để secret/API key xuất hiện trong frontend, log hoặc model artifact.

### 3.2. KPI mô hình — phải đo trên tập test khóa theo thời gian

Không đặt ngưỡng “thắng chắc”. Các ngưỡng dưới đây là **cổng thử nghiệm**, sẽ hiệu chỉnh bằng baseline thực tế:

| Nhóm | Chỉ số | Cổng ban đầu |
|---|---|---|
| Phân loại | Macro F1 cho 3 lớp | Tốt hơn baseline đơn giản ≥ 10% tương đối |
| Xác suất | Brier score / ECE | Tốt hơn model chưa calibrate; ECE ≤ 0,05 nếu khả thi |
| Giao dịch | Expectancy sau mọi chi phí | > 0 trên test và ≥ 3 regime chính |
| Giao dịch | Profit factor | ≥ 1,20 out-of-sample, không dựa vào vài outlier |
| Rủi ro | Max drawdown | Trong risk budget đã duyệt; mục tiêu nghiên cứu ≤ 15% |
| Ổn định | Walk-forward folds có expectancy dương | ≥ 70% folds |
| Coverage | Tỷ lệ có tín hiệu | Theo dõi, không ép cao; `NO_TRADE` được chấp nhận |
| Drift | PSI/feature drift | Alert theo baseline; định nghĩa riêng cho mỗi feature group |

### 3.3. KPI hệ thống

- Local beta hoạt động ổn định trong phiên sử dụng; không đặt SLA 24/7 vì không có server/đội trực trả phí.
- API error rate < 1%; upload/predict success ≥ 99% với ảnh hợp lệ.
- Không có lỗ hổng Critical/High đã biết trước khi cho người khác truy cập trong LAN/private beta.
- 100% prediction có `request_id`, `model_version`, `feature_version`, timestamp UTC.
- Nếu có sẵn ổ backup thứ hai: mục tiêu local RPO 24h, RTO 4h. Nếu không có, ghi rõ “không có bảo đảm khôi phục sau hỏng ổ”; không đặt RPO/RTO giả tạo.

### 3.4. Cổng Go/No-Go

- **Gate A – Data:** dữ liệu đủ, đúng và không leakage.
- **Gate B – Research:** model vượt baseline trên test khóa.
- **Gate C – Paper:** paper trading dương sau chi phí trong thời gian và số mẫu tối thiểu.
- **Gate D – Beta:** an toàn, quan sát được, UX rõ ràng.
- **Gate E – Live:** nằm ngoài phạm vi 0 đồng; chỉ xem xét bằng một kế hoạch mới sau pháp lý + bảo mật + paper gate.

---

## 4. Định nghĩa bài toán dự đoán

### 4.1. Thời điểm ra quyết định

- Chỉ dự đoán sau khi nến 15m đã **đóng hoàn toàn**.
- Nến 1H dùng gần nhất đã đóng; không dùng giá đóng tương lai hoặc nến đang chạy vào feature train.
- `decision_time` theo UTC; UI chuyển sang múi giờ người dùng.
- Ảnh quá cũ so với thị trường hiện tại phải báo stale và không phát tín hiệu live.

### 4.2. Nhãn mục tiêu khuyến nghị

Dùng **triple-barrier labeling** thay vì chỉ lấy dấu của future return:

- Giá tham chiếu tại thời điểm quyết định: mark price hoặc mức fill mô phỏng đã định nghĩa nhất quán.
- Upper barrier: `+k × ATR`.
- Lower barrier: `-k × ATR`.
- Vertical barrier: sau `H = 4` nến 15m (nghiên cứu thêm H = 2, 8).
- `LONG`: upper barrier chạm trước và lợi nhuận ròng sau chi phí > ngưỡng.
- `SHORT`: lower barrier chạm trước và lợi nhuận ròng sau chi phí > ngưỡng.
- `NO_TRADE`: không barrier nào tạo lợi thế ròng, hai barrier mơ hồ, hoặc chất lượng dữ liệu kém.

Phải có quy tắc rõ khi cả hai barrier bị chạm trong cùng một OHLC bar. Cách an toàn: dùng dữ liệu độ phân giải thấp hơn để xác định thứ tự; nếu không có thì chọn giả định bảo thủ hoặc loại mẫu.

### 4.3. Chi phí phải đưa vào nhãn/backtest

- Maker/taker fee theo tier giả định và cấu hình, không hard-code một con số vĩnh viễn.
- Bid–ask spread.
- Slippage phụ thuộc thanh khoản/volatility/size.
- Funding rate nếu vị thế đi qua kỳ funding.
- Latency từ lúc nến đóng → inference → order giả lập.
- Partial fill, reject, tick size, step size và minimum notional nếu về sau có execution.

### 4.4. Quy tắc sinh tín hiệu

Ví dụ ban đầu, chỉ để nghiên cứu:

```text
Nếu quality_pass = false                         => NO_TRADE
Nếu data_stale hoặc symbol/timeframe mismatch    => NO_TRADE
Nếu max(P_long, P_short) < threshold             => NO_TRADE
Nếu expected_net_return <= 0                     => NO_TRADE
Nếu risk filters fail                            => NO_TRADE
Ngược lại chọn lớp có expected utility cao nhất.
```

Threshold không chọn trên test; chỉ chọn bằng validation và khóa trước final test.

---

## 5. Chiến lược dữ liệu

### 5.1. Nguồn dữ liệu chuẩn

Ưu tiên dữ liệu Binance chính thức cho USDⓈ-M:

- Kline/OHLCV 1m hoặc 5m để tự resample 15m và 1H nhất quán.
- Mark price và index price.
- Funding rate và premium index.
- Open interest.
- Taker buy/sell volume, trade count.
- Long/short ratios chỉ dùng nếu hiểu rõ giới hạn lịch sử và ý nghĩa.
- Order book/aggregate trades ở phase nâng cao; dữ liệu này phải được thu real-time vì lịch sử đầy đủ thường không sẵn.
- `exchangeInfo` để lấy trạng thái symbol, tick size, lot size và rate limits động.

Không scrape giao diện Binance. REST dùng cho backfill/reconciliation; WebSocket dùng cho dữ liệu live, có reconnect, heartbeat, resubscribe và gap recovery.

Không giả định mọi feature phái sinh có lịch sử dài như OHLCV. Binance có thể chỉ cung cấp một cửa sổ lịch sử ngắn cho một số endpoint thống kê và có thể thay đổi giới hạn. Collector phải lưu append-only ngay từ ngày đầu; model v1 không được phụ thuộc vào funding/OI/ratio nếu coverage theo thời gian chưa đủ. Public market-data endpoint hiện không đòi signed trading credential khi tài liệu ghi security type `NONE`/không ghi security type, nhưng connector phải kiểm tra tài liệu hiện hành, rate limit và khả dụng theo khu vực; tuyệt đối không nhúng API secret để lấy dữ liệu công khai.

### 5.2. Kiến trúc lưu trữ dữ liệu

- **Raw/bronze:** payload gốc append-only, partition theo source/symbol/date.
- **Clean/silver:** schema chuẩn, UTC, deduplicate, gap flags, adjusted quality flags.
- **Features/gold:** feature theo `event_time`, versioned, chỉ dùng dữ liệu đã tồn tại tại thời điểm dự đoán.
- Filesystem local theo thư mục versioned cho ảnh, raw data và model artifacts; hash + manifest để truy vết.
- DuckDB + Parquet cho dữ liệu nghiên cứu/time-series; SQLite cho user, request, prediction và audit của single-node MVP.
- Queue in-process hoặc bảng job trong SQLite; không cần Redis ở MVP một máy.

PostgreSQL/TimescaleDB, MinIO và Redis đều có thể tự host miễn phí nhưng làm tăng RAM, độ phức tạp và công vận hành. Chỉ chuyển sang chúng khi máy hiện có đủ tài nguyên và benchmark chứng minh SQLite/DuckDB không đáp ứng; việc chuyển đổi vẫn không được tạo chi phí tiền mặt.

### 5.3. Schema tối thiểu

```text
market_bars(symbol, interval, open_time, close_time, o, h, l, c, volume,
            quote_volume, trades, taker_buy_volume, source, ingested_at,
            is_closed, quality_flags)
derivatives_features(symbol, event_time, mark_price, index_price, funding_rate,
                     open_interest, premium, source, ingested_at)
uploads(id, user_id, storage_ref, sha256, mime, width, height, created_at,
        detected_symbol, detected_interval, quality_status, expires_at)
prediction_requests(id, user_id, symbol, decision_time, image_1h_id,
                    image_15m_id, status, created_at)
predictions(id, request_id, model_version, feature_version, signal,
            p_long, p_short, p_no_trade, expected_return, risk_payload,
            explanation_payload, latency_ms, created_at)
outcomes(prediction_id, horizon, realized_return_gross, fees, funding,
         slippage, realized_return_net, label, evaluated_at)
model_registry(version, artifact_uri, data_version, git_sha, metrics_json,
               status, approved_by, created_at)
audit_logs(actor_id, action, object_type, object_id, metadata, created_at)
```

### 5.4. Kiểm tra chất lượng dữ liệu

- Unique key theo symbol/interval/open_time.
- OHLC invariant: `low ≤ min(open, close) ≤ max(open, close) ≤ high`.
- Volume không âm; timestamp đúng interval; nến closed mới dùng.
- Phát hiện gap, duplicate, outlier, clock skew và schema drift.
- Reconcile định kỳ giữa stream và REST.
- Hash/checksum raw file; lineage từ prediction về raw partitions.
- Báo cáo coverage theo ngày/symbol/feature.

### 5.5. Chia tập chống leakage

- Split theo thời gian, tuyệt đối không random split từng dòng.
- Train → validation → test theo các giai đoạn liên tiếp.
- Purged walk-forward cross-validation + embargo ít nhất bằng prediction horizon.
- Giữ một **final holdout** chưa nhìn tới khi khóa pipeline và hyperparameter.
- Samples có window chồng lấn không được nằm hai phía split nếu gây rò rỉ nhãn.
- Scaler/feature selector/calibration chỉ fit trên train/validation đúng quy trình.

---

## 6. Pipeline xử lý ảnh

### 6.1. Kiểm tra upload

1. Kiểm tra content length và rate limit trước upload.
2. Magic-byte/MIME sniffing, decode ảnh trong sandbox.
3. Loại EXIF/metadata, re-encode về định dạng nội bộ.
4. Quét bằng Microsoft Defender có sẵn trên Windows nếu khả dụng; dù có quét vẫn phải decode/re-encode và giới hạn pixel để chống decompression bomb.
5. Tính SHA-256 để deduplicate và audit.
6. Kiểm tra độ phân giải, blur, vùng chart, tỷ lệ crop và chữ có đọc được không.
7. Không public thư mục upload; backend đọc bằng ID nội bộ, không nhận đường dẫn tùy ý từ client.

### 6.2. Hiểu ảnh

- OCR: symbol, timeframe, timestamp, giá trục, tên indicator nếu hiển thị.
- Layout detector: vùng price chart, volume, indicator panels, watermark/UI.
- Quality classifier: đúng chart nến hay không, đủ số nến không, quá mờ/crop/che không.
- Cross-check:
  - Symbol user chọn so với OCR.
  - 1H/15m user gán so với OCR.
  - Timestamp/giá cuối ảnh so với Binance trong dung sai.
  - Hai ảnh có cùng symbol và thời điểm logic hay không.
- Nếu không xác minh được, yêu cầu người dùng sửa input hoặc trả `NO_TRADE`; không đoán ngầm.

### 6.3. Chuẩn hóa ảnh

- Crop vùng chart đã phát hiện; giữ lại bản gốc cho audit theo retention policy.
- Resize có padding, không kéo méo nến.
- Chuẩn hóa màu có kiểm soát; augment theme sáng/tối, scale, font, compression, crop nhẹ.
- Không augment làm thay đổi ý nghĩa giá/thời gian, ví dụ lật ngang chart.
- Mask thông tin có thể gây shortcut learning như PnL/order marker nếu dataset không nhất quán.

### 6.4. Tạo dataset ảnh đúng cách

Phương án ưu tiên là **render ảnh chuẩn từ OHLCV lịch sử** bằng nhiều theme/layout, sau đó gắn nhãn bằng cùng labeling pipeline. Ảnh người dùng đã consent chỉ dùng để đánh giá domain shift và fine-tune có kiểm soát.

- Render 1H và 15m tại cùng decision_time.
- Số nến nhìn lại cố định hoặc lưu metadata số nến.
- Tuyệt đối không render bất kỳ nến tương lai nào.
- Nhóm hai ảnh thành một sample, có `sample_id` và label chung.
- Split theo time trước khi tạo augmentation để biến thể cùng sample không lọt sang test.

---

## 7. Chiến lược mô hình

### 7.1. Baseline bắt buộc

Xây từ đơn giản đến phức tạp:

1. **Baseline ngẫu nhiên/majority/no-trade** để biết mức sàn.
2. **Rule-based:** trend 1H + momentum/pullback 15m + ATR filter.
3. **Tabular model:** Logistic Regression, LightGBM/XGBoost trên numeric features.
4. **Sequence model:** TCN/LSTM/Transformer nhỏ trên chuỗi OHLCV nếu baseline chứng minh cần thiết.
5. **Vision model:** CNN/ViT hai nhánh cho ảnh 1H và 15m.
6. **Hybrid fusion:** numeric branch + 1H image branch + 15m image branch + quality metadata.

Chỉ chọn model phức tạp hơn nếu cải thiện có ý nghĩa, ổn định và xứng đáng với latency/chi phí/khả năng vận hành.

### 7.2. Feature numeric đề xuất

- Returns/log returns nhiều horizon.
- ATR, realized volatility, range, wick/body ratios.
- EMA slopes/crosses, RSI, MACD — chỉ giữ khi ablation chứng minh giá trị.
- Volume z-score, taker imbalance, trade count.
- Trend/regime 1H; trigger 15m.
- Mark–index basis, premium, funding, open-interest change.
- Time features theo UTC; tránh diễn giải tùy tiện.
- Liquidity/spread/order-book imbalance ở phase sau.

Mọi feature phải có công thức, window, missing rule, timestamp semantics và owner trong feature registry.

### 7.3. Fusion và output

```text
Encoder_1H(image_1H) ─┐
Encoder_15m(image_15m) ├─> fusion/gating ─> logits 3 lớp + expected return
Tabular(sequence/data) ─┤
Quality/context ────────┘
```

- Multi-task output: xác suất 3 lớp + expected net return + uncertainty.
- Dùng quality/context làm gating; không để ảnh kém vẫn sinh confidence cao.
- Calibrate xác suất bằng temperature scaling/isotonic trên validation phù hợp.
- Có OOD detector/embedding-distance hoặc ít nhất quality threshold để abstain.

### 7.4. Loss và mất cân bằng lớp

- Class-weighted cross-entropy hoặc focal loss nếu cần.
- Utility-aware sample weighting phải kiểm tra kỹ để không overfit PnL.
- Theo dõi precision/recall từng lớp và confusion matrix theo regime/symbol.
- Không oversample trước time split; augmentation chỉ trong train.

### 7.5. Explainability

- Numeric: SHAP/top feature contributions ở mức tổng quát.
- Vision: attention/Grad-CAM chỉ là công cụ chẩn đoán, không diễn giải như bằng chứng nhân quả.
- UI dùng câu có cấu trúc: xu hướng 1H, động lượng 15m, volatility, funding/OI, risk filter.
- Không dùng LLM tự bịa lý do; nếu dùng LLM để diễn đạt, input phải là facts có cấu trúc và output có validation.

### 7.6. Model registry và reproducibility

Mỗi model version lưu:

- Git SHA, image/container digest.
- Data snapshot/version và query window.
- Feature/label version.
- Seed, config, hyperparameters.
- Metrics theo overall/symbol/regime/month.
- Calibration artifact và thresholds.
- Model card: mục đích, hạn chế, dữ liệu, rủi ro, người phê duyệt.

---

## 8. Backtest, validation và paper trading

### 8.1. Backtest engine

- Event-driven hoặc vectorized có unit test để ngăn look-ahead.
- Entry chỉ sau decision_time cộng latency mô phỏng.
- Fill theo bid/ask hoặc slippage model, không mặc định fill tại close lý tưởng.
- Có fee/funding, liquidation constraint, tick/step size và position sizing.
- Một vị thế/symbol trong MVP để tránh quy tắc chồng lấn mơ hồ.
- Log mọi event: signal, intended order, fill, fee, exit reason.

### 8.2. Báo cáo bắt buộc

- Gross/net PnL, CAGR nếu horizon đủ dài.
- Win rate, average win/loss, expectancy, profit factor.
- Sharpe, Sortino, Calmar; nêu rõ sampling/annualization.
- Max drawdown và duration.
- Turnover, fees/funding/slippage contribution.
- Coverage và `NO_TRADE` rate.
- Phân tích theo symbol, long/short, volatility regime, trend regime, tháng và confidence bucket.
- Bootstrap confidence interval; sensitivity với chi phí x1, x1.5, x2.

### 8.3. Kiểm thử chiến lược

- Walk-forward: train quá khứ → validate đoạn kế → test đoạn sau.
- Stress: flash move, gap dữ liệu, WebSocket disconnect, stale image, API 429/5xx.
- Placebo/permutation test để phát hiện edge giả.
- Ablation: image-only vs numeric-only vs hybrid.
- Benchmark: buy-and-hold không đủ cho chiến lược ngắn hạn; thêm random, always-long/short và rule baseline.

### 8.4. Paper trading gate

Trước closed beta cần tối thiểu:

- 8–12 tuần chạy forward hoặc đủ **≥ 300 tín hiệu độc lập**; dùng điều kiện nào lâu hơn tùy tốc độ signal.
- PnL/expectancy dương sau chi phí giả định bảo thủ.
- Không vi phạm hard risk limits.
- Data/inference uptime đạt mục tiêu.
- Không có chênh lệch không giải thích được giữa backtest và paper engine.

Không thay model liên tục trong giai đoạn đo; mỗi thay đổi tạo một cohort/version riêng.

---

## 9. Kiến trúc hệ thống đề xuất

### 9.1. Stack MVP 0 đồng

- Frontend: React/Vite + TypeScript hoặc giao diện server-rendered bằng FastAPI/Jinja; chọn phương án nhẹ nhất sau spike. Tailwind CSS là tùy chọn miễn phí.
- API: FastAPI/Python, OpenAPI-first, Pydantic validation.
- ML: scikit-learn, LightGBM/XGBoost và PyTorch bản miễn phí; ưu tiên model chạy CPU.
- Image/OCR candidates: Pillow, OpenCV, Tesseract OCR và thư viện render chart mã nguồn mở; chỉ chốt sau kiểm tra license/version và benchmark local.
- Experiment/model registry: file JSON/CSV + thư mục artifact có checksum; có thể chạy MLflow local nếu máy đủ RAM.
- Jobs: `asyncio`/`concurrent.futures` hoặc worker Python local + SQLite job table; không cần broker ở MVP.
- Data: DuckDB + Parquet cho market/research; SQLite cho application metadata.
- File storage: filesystem local ngoài web root, cấu trúc content-addressed bằng SHA-256.
- Infra: Python virtual environment; Docker Desktop chỉ dùng nếu đã cài và license phù hợp. Không Kubernetes, không cloud.
- Observability: Python structured logs + SQLite/JSONL metrics; Prometheus/Grafana local là tùy chọn, không phải dependency bắt buộc.
- CI: chạy local bằng pre-commit/tox/pytest. GitHub Actions chỉ là tùy chọn nếu repo và quota miễn phí phù hợp; pipeline local vẫn phải đủ để không phụ thuộc dịch vụ.

Tất cả dependency phải được khóa phiên bản và lập `THIRD_PARTY_LICENSES.md`. Không dùng gói có license hạn chế mục đích thương mại nếu mục tiêu tương lai có thể thương mại hóa.

### 9.2. Luồng request

```text
Browser
  -> Local auth/session + upload
  -> Private local filesystem
  -> API creates prediction request
  -> Image validation/OCR/quality
  -> Market-data lookup at decision_time
  -> Feature service
  -> Model inference
  -> Risk/policy engine
  -> Persist prediction + audit
  -> Return result / WebSocket-SSE job update
```

### 9.3. Tách service theo giai đoạn

MVP 0 đồng là **modular monolith + worker local**, không microservice hóa sớm:

- `web`
- `api`
- `worker-image`
- `worker-ml`
- `market-ingestor`
- SQLite/DuckDB/Parquet/private filesystem

Chỉ tách service khi benchmark cho thấy nhu cầu rõ ràng và vẫn đáp ứng ngân sách 0 VNĐ; public scale nằm ngoài MVP.

### 9.4. API contract sơ bộ

```text
POST   /v1/uploads
POST   /v1/predictions
GET    /v1/predictions/{id}
GET    /v1/predictions?cursor=...
POST   /v1/predictions/{id}/feedback
GET    /v1/symbols
GET    /health/live
GET    /health/ready
```

`POST /v1/predictions` phải idempotent theo `Idempotency-Key`; response không lộ đường dẫn file nội bộ hay stack trace.

### 9.5. State machine prediction

```text
UPLOADING -> VALIDATING -> ENRICHING -> INFERENCING -> RISK_CHECK
          -> COMPLETED | REJECTED_INPUT | NO_TRADE | FAILED_RETRYABLE | FAILED
```

Timeout/retry có giới hạn; job phải idempotent và có dead-letter queue.

---

## 10. Thiết kế giao diện web

### 10.1. Trang chính

- Chọn symbol trước khi upload.
- Hai dropzone tách biệt: `1H` và `15m`, có thumbnail và checklist chất lượng.
- Hướng dẫn ảnh mẫu: số nến tối thiểu, không che chart, hiển thị timeframe/symbol nếu có.
- Checkbox xác nhận hai ảnh cùng symbol và gần cùng thời điểm.
- Nút “Phân tích” chỉ mở khi input hợp lệ.

### 10.2. Kết quả

- Badge lớn: LONG/SHORT/NO_TRADE.
- Confidence dưới dạng xác suất đã calibration, kèm câu “không phải xác suất lợi nhuận được đảm bảo”.
- Timestamp, symbol, model version, thời hạn hiệu lực.
- Entry zone, invalidation, SL/TP và R:R nếu policy cho phép.
- Lý do có cấu trúc và cảnh báo ảnh/data.
- CTA: lưu, phản hồi, xem outcome khi horizon kết thúc.
- Disclaimer rủi ro luôn nhìn thấy, không dùng dark pattern.

### 10.3. Lịch sử và dashboard

- Lọc theo symbol, signal, model version, ngày.
- Hiển thị prediction tại thời điểm đó, không rewrite lịch sử sau khi outcome có.
- Outcome tách riêng khỏi prediction.
- Calibration chart và thống kê chỉ hiển thị khi sample size đủ; ghi rõ số mẫu.

### 10.4. Admin/MLOps

- Data freshness, queue lag, error rate, inference latency.
- Model active/challenger, rollback.
- Drift, confidence distribution, class distribution.
- Upload rejection reasons.
- Audit trail và quyền truy cập theo role.

---

## 11. Quản trị rủi ro giao dịch

Risk engine phải tách khỏi model; model không có quyền tự bỏ qua giới hạn.

### 11.1. Hard rules ban đầu

- `NO_TRADE` khi dữ liệu stale, gap, OOD, confidence thấp hoặc volatility cực đoan.
- Không đề xuất risk > 0,5% equity/tín hiệu ở mặc định.
- Giới hạn tổng exposure, số vị thế và correlated exposure nếu mở rộng nhiều symbol.
- Stop-loss bắt buộc cho mọi signal có kế hoạch giao dịch.
- Daily loss limit, drawdown circuit breaker và model kill switch.
- Không martingale, không tự tăng size để gỡ lỗ.
- Đòn bẩy là input rủi ro, không phải cách làm tăng edge.

### 11.2. Nếu bổ sung auto-trading sau này

- Chỉ API key riêng, quyền tối thiểu, **không bật withdrawal**.
- Testnet/demo trước; canary bằng size tối thiểu sau khi được duyệt.
- Reconcile order/position qua user data stream và REST fallback.
- One-way/Hedge Mode, isolated/cross margin phải được nhận diện rõ.
- Reduce-only cho exit phù hợp; idempotent client order ID.
- Xử lý trạng thái order `UNKNOWN`, partial fill, disconnect và retry không tạo lệnh trùng.
- Emergency stop phía server, không phụ thuộc UI.

---

## 12. Bảo mật, riêng tư và tuân thủ

### 12.1. Threat model chính

- File độc hại/decompression bomb.
- Prompt/visual injection trong ảnh nếu pipeline có VLM/LLM.
- SSRF từ URL upload; MVP chỉ nhận direct upload, không fetch URL tùy ý.
- API abuse, credential stuffing, scraping, DDoS.
- Model extraction/inversion, data poisoning qua feedback/upload.
- Secret leakage trong frontend/log/notebook/model artifact.
- IDOR/path traversal trên lịch sử prediction và private filesystem.
- Supply-chain risk từ package/container/model weights.

### 12.2. Controls

- TLS, encryption at rest, KMS/secret manager, key rotation.
- RBAC, MFA cho admin, session security, CSRF/CORS đúng origin.
- Rate limit local theo IP/session; không dùng CAPTCHA trả phí. Nếu public sau này mới đánh giá giải pháp phù hợp.
- File nằm ngoài web root; chỉ truy cập qua ID đã kiểm tra quyền; canonicalize path, retention và deletion job.
- Dependency pinning, SAST/DAST, secret scan, container scan, SBOM.
- Audit log append-oriented; log redaction; không log ảnh/base64/token.
- Backup restore test; incident response runbook; vulnerability disclosure.
- Chạy OWASP ZAP Community, dependency/secret scan và checklist thủ công miễn phí trước private beta. Pentest độc lập là điều kiện nên có nếu public/auto-trade, nhưng nằm ngoài cam kết 0 đồng.

### 12.3. Quyền riêng tư

- Privacy notice mô tả ảnh được lưu bao lâu và có dùng train hay không.
- Mặc định **không dùng upload của người dùng để train** nếu chưa opt-in rõ ràng.
- Cho phép xóa tài khoản/dữ liệu theo policy; tách dữ liệu audit bắt buộc nếu luật yêu cầu.
- Không yêu cầu API key Binance khi MVP chỉ phát tín hiệu.

### 12.4. Pháp lý

- Không gọi crypto futures là “chứng khoán” trong nội dung sản phẩm nếu chưa có cơ sở pháp lý; dùng “hợp đồng tương lai/perpetual tài sản mã hóa”.
- Trong MVP 0 đồng, chỉ dùng nội bộ/private research, không bán dịch vụ, không nhận tiền, không quản lý tài sản và không auto-trade. Nếu muốn public hoặc thương mại hóa tại Việt Nam, cần một cổng pháp lý riêng; tư vấn luật chuyên nghiệp có thể phát sinh phí và vì vậy nằm ngoài phạm vi hiện tại.
- Việt Nam đang có khuôn khổ thí điểm thị trường tài sản mã hóa; quy định có thể thay đổi. Compliance review không phải việc làm một lần.
- Điều khoản sử dụng phải nêu rủi ro đòn bẩy, không bảo đảm lợi nhuận, giới hạn trách nhiệm hợp lý và eligibility/geofencing nếu cần.

---

## 13. Kiểm thử phần mềm

### 13.1. Test pyramid

- Unit: label, feature, indicators, cost, position sizing, image validation.
- Property tests: OHLC invariants, no-future-data, idempotency.
- Integration: Binance adapter, SQLite/DuckDB, private filesystem, local job worker và model runtime.
- Contract: OpenAPI, event schemas, model input/output schema.
- E2E: upload 2 ảnh → kết quả → history → outcome.
- Golden dataset: bộ ảnh chuẩn/ảnh lỗi cố định để regression test OCR/quality/model.
- Load: concurrent upload/inference, queue backlog, large file rejection.
- Chaos: WebSocket disconnect, rate limit, DB failover, worker death, stale cache.
- Security: authz/IDOR, file upload, injection, SSRF, rate-limit bypass.

### 13.2. Test cases bắt buộc

- Hai ảnh khác symbol/timeframe.
- Ảnh 15m mới hơn hoặc cũ bất hợp lý so với 1H.
- Ảnh không phải biểu đồ, ảnh mờ, crop mất trục, theme lạ.
- Nến cuối đang chạy.
- Market data có gap/stale.
- Confidence sát threshold.
- Binance 429/418/5xx; reconnect 24h; out-of-order/duplicate event.
- Model timeout/crash; retry không tạo prediction trùng.
- User A không đọc được ảnh/prediction của User B.

### 13.3. Definition of Done chung

- Code review, lint/type/unit tests pass.
- Có metrics/log/traces và error handling.
- Migration forward/backward plan.
- Tài liệu API/runbook cập nhật.
- Security/privacy impact đã xét.
- Acceptance criteria có bằng chứng; chạy local test profile và smoke test pass.

---

## 14. Observability và vận hành

### 14.1. Metrics

- Data: event lag, gap count, REST reconciliation diff.
- API: RPS, p50/p95/p99, status codes, rate-limit hits.
- Queue: depth, oldest job age, retry/DLQ.
- ML: latency, class/confidence distribution, abstain rate, OOD, drift.
- Product: upload completion, rejection reason, prediction completion, retention.
- Strategy: delayed outcome, expectancy, cost breakdown, drawdown theo model version.

### 14.2. Alerts

- Không có closed kline sau 2 interval mong đợi.
- Inference error/latency vượt SLO.
- Distribution thay đổi mạnh hoặc signal chỉ còn một lớp.
- PnL/drawdown paper vượt risk budget.
- Unauthorized/admin anomalies, secret/access failure.
- Storage/DB/queue capacity.

### 14.3. Runbooks

- Binance stream disconnect/gap recovery.
- REST 429/418 và exponential backoff + jitter.
- Model rollback.
- Bad data partition quarantine/reprocess.
- Credential compromise.
- Incident communication và postmortem không đổ lỗi.

---

## 15. Lộ trình triển khai và tiến độ

### 15.1. Ước lượng nhân sự chuẩn

- Các vai trò cần có: Product/Domain, ML/Data, Backend/Data Engineering, Frontend, QA/Security/Operations.
- Với ngân sách 0 VNĐ, một chủ dự án tự đảm nhiệm toàn bộ hoặc cộng tác viên tự nguyện dùng thiết bị sẵn có; kế hoạch không giả định thuê nhân sự.

Với nhóm 3–4 người tự nguyện: **16 tuần đến local closed beta**, sau đó 8–12 tuần paper validation. Một người làm bán thời gian và chỉ dùng CPU nên dự trù thực tế **28–40 tuần** cho local closed beta, chưa tính paper gate; training vision có thể lâu hơn. Public/live không thuộc lộ trình 0 đồng.

### 15.2. Timeline 16 tuần

| Phase | Tuần | % dự án | Công việc chính | Deliverable / Gate |
|---|---:|---:|---|---|
| 0. Discovery | 1 | 0–5% | Chốt D01–D08, PRD, risk/legal scope | PRD + decision log |
| 1. Foundation | 2 | 5–12% | Repo, CI/CD, env, schema, auth skeleton, observability | Staging skeleton |
| 2. Data platform | 3–4 | 12–25% | Backfill/stream, raw-clean-feature, DQ/reconciliation | **Gate A** |
| 3. Label & backtest | 5–6 | 25–37% | Triple barrier, costs, baseline rules/tabular, walk-forward | Baseline report |
| 4. Image pipeline | 7–8 | 37–49% | Upload security, OCR/layout/quality, synthetic renderer | Golden image tests |
| 5. ML research | 9–10 | 49–62% | Vision/hybrid, calibration, OOD, ablation | **Gate B** |
| 6. Product MVP | 11–12 | 62–74% | Prediction API, UI upload/result/history, risk engine | E2E staging |
| 7. Hardening | 13–14 | 74–86% | Security, load, failure handling, monitoring, runbooks | Release candidate |
| 8. Paper beta | 15–16 | 86–95% | Internal paper trading, bug fixes, model freeze | Closed beta |
| 9. Validation | +8–12 tuần | 95–99% | Forward sample, drift, calibration, risk review | **Gate C/D** |
| 10. Local release | Sau duyệt | 99–100% | Self-review, đóng gói, hướng dẫn chạy local/backup | Local/private signal product |

### 15.3. Chi tiết theo sprint

#### Sprint 0 — Discovery (Tuần 1)

- Viết PRD, user journey, non-goals.
- Chốt horizon, symbol, label, risk budget, success metrics.
- Tự kiểm tra điều khoản API, quyền sử dụng dữ liệu/branding và ghi decision memo; không thuê tư vấn trong MVP.
- Tạo threat model, data retention, consent strategy.
- Đầu ra: PRD v1, ADR-001 architecture, risk register, backlog ưu tiên.

#### Sprint 1 — Foundation (Tuần 2)

- Monorepo hoặc repo rõ module; profile local-dev/local-test/local-release.
- CI: format/lint/type/test/scan.
- Script bootstrap local, DB migration, thư mục dữ liệu private và cấu hình đường dẫn qua `.env` không commit. Secret session được sinh local, giới hạn ACL; MVP market-data không cần Binance API key.
- Auth và audit skeleton; OpenAPI skeleton.
- Đầu ra: script cài/chạy local lặp lại được, test profile, health checks và telemetry local.

#### Sprint 2–3 — Data platform (Tuần 3–4)

- Binance adapter REST + WebSocket.
- Backfill BTC/ETH; raw/clean tables; gap recovery.
- DQ tests và daily report.
- Feature store offline tối giản; point-in-time correctness test.
- Gate A: ≥ 99,9% expected bars trong khoảng nghiên cứu hoặc mọi gap được flag/loại có chủ đích.

#### Sprint 4–5 — Label/backtest/baseline (Tuần 5–6)

- Triple-barrier variants; fee/funding/slippage model.
- Purged walk-forward splits; final holdout khóa.
- Rule baseline + logistic + LightGBM.
- Báo cáo theo regime và sensitivity cost.
- Không tiếp tục deep vision nếu tabular pipeline còn leakage/không ổn định.

#### Sprint 6–7 — Image pipeline (Tuần 7–8)

- Secure upload, storage lifecycle.
- Chart detector/OCR/quality/mismatch logic.
- Synthetic chart renderer và augmentations hợp lệ.
- Golden set gồm ảnh hợp lệ, lỗi, theme/layout khác nhau.
- Đạt recall cao cho input nguy hiểm/sai; ưu tiên false reject hơn phát signal sai.

#### Sprint 8–9 — ML hybrid (Tuần 9–10)

- Image-only benchmark, numeric-only benchmark, fusion.
- Hyperparameter search chỉ trên train/validation.
- Calibration, OOD, threshold/no-trade optimization.
- Ablation và model card.
- Gate B: vượt baseline và pass risk/robustness; nếu không, ship numeric model + image validation thay vì ép dùng vision.

#### Sprint 10–11 — Web MVP (Tuần 11–12)

- Upload UX, job progress, error correction.
- Result/history/outcome, disclaimer và feedback.
- Admin health/model dashboard tối thiểu.
- Prediction API idempotency, audit, caching hợp lý.
- E2E và accessibility cơ bản WCAG 2.1 AA.

#### Sprint 12–13 — Hardening (Tuần 13–14)

- Load/chaos/security tests, dependency/container scan.
- Backup restore, rollback, incident runbooks.
- Privacy deletion/retention jobs.
- Performance tuning; SLO alerts.
- Self-review bằng công cụ miễn phí; không public exposure trong MVP.

#### Sprint 14–15 — Closed beta (Tuần 15–16)

- Model freeze; internal users; paper ledger.
- Theo dõi lỗi input, latency, calibration và drift.
- Sửa bug hệ thống; thay model phải thành version/cohort mới.
- Release notes, support workflow, known limitations.

#### Forward validation (8–12 tuần tiếp theo)

- Thu đủ ≥ 300 signals độc lập và nhiều regime.
- Weekly report nhưng không tune theo từng tuần.
- Chạy champion/challenger shadow.
- Checklist Go/No-Go bao phủ product, ML, engineering, security/compliance; nếu chỉ có một người phải ghi bằng chứng cho từng vai trò để tự kiểm tra chéo sau một khoảng nghỉ.

---

## 16. Backlog ưu tiên

### P0 — Bắt buộc trước closed beta

- [ ] PRD + D01–D08 + legal scope.
- [ ] Binance data ingestion, reconciliation, DQ.
- [ ] Point-in-time features và leakage tests.
- [ ] Label/cost/backtest được review.
- [ ] Baselines và final holdout protocol.
- [ ] Secure two-image upload + quality/mismatch validation.
- [ ] 3-class model + calibration + no-trade policy.
- [ ] Risk engine độc lập.
- [ ] Prediction API, UI result/history.
- [ ] Audit/model registry/rollback.
- [ ] Observability, alert, backup/restore, incident runbooks.
- [ ] Security/privacy review và disclaimer.

### P1 — Nên có trước khi mở rộng private beta

- [ ] Outcome dashboard và confidence calibration chart.
- [ ] Model drift dashboard.
- [ ] Admin review queue cho ảnh/input bất thường.
- [ ] Feedback chống poisoning.
- [ ] Accessibility/i18n.
- [ ] OWASP ZAP Community + dependency/secret/license scan local.
- [ ] Resource dashboard: CPU, RAM, disk, thời gian train/inference; xác nhận tiền mặt vẫn 0 VNĐ.

### P2 — Sau khi chứng minh edge

- [ ] Thêm symbol theo từng gate độc lập.
- [ ] Order-book/agg-trade features.
- [ ] Mobile/PWA notification.
- [ ] Personalization theo risk profile, không fine-tune mù theo người dùng.
- [ ] Binance testnet execution.
- [ ] Live execution canary nếu pháp lý và risk committee duyệt.

---

## 17. RACI tối giản

| Hạng mục | Product/Domain | ML/Data | Backend/Data Eng | Frontend | Security/Compliance |
|---|---|---|---|---|---|
| PRD/metric/risk | A/R | C | C | C | C |
| Data/feature/label | C | A/R | R | I | I |
| Model/backtest | C | A/R | C | I | I |
| API/infra | I | C | A/R | C | C |
| UX | A | C | C | R | C |
| Security/privacy/legal | C | I | R | C | A/R |
| Go/No-Go | A | R | R | C | R |

`A`: accountable, `R`: responsible, `C`: consulted, `I`: informed.

---

## 18. Risk register

| Rủi ro | Xác suất | Tác động | Giảm thiểu | Trigger/Kill condition |
|---|---|---|---|---|
| Ảnh không đủ thông tin | Cao | Cao | Hybrid data, OCR, quality gate, no-trade | Mismatch/OOD vượt ngưỡng |
| Data leakage | Trung | Rất cao | Point-in-time, purged split, independent review | Metric bất thường, test audit fail |
| Backtest overfit | Cao | Rất cao | Baseline, holdout, walk-forward, paper | Paper lệch lớn kéo dài |
| Regime drift | Cao | Cao | Drift monitor, retrain policy, kill switch | PSI/performance breach |
| Chi phí xóa edge | Cao | Cao | Net label/backtest, stress x2 cost | Expectancy net ≤ 0 |
| API/data outage | Trung | Cao | WS+REST recovery, stale guard | Data freshness breach |
| Model confidence sai | Trung | Cao | Calibration, abstain, bucket monitor | ECE/calibration breach |
| Upload/security abuse | Trung | Cao | Validate/re-encode/scan/rate limit | Incident/critical finding |
| Pháp lý thay đổi | Trung | Rất cao | Counsel review, feature flag, geo policy | Counsel says stop |
| Người dùng hiểu là bảo đảm | Cao | Cao | UX/disclaimer/no dark pattern | Complaint/marketing breach |
| Key/order lỗi nếu auto trade | Trung | Rất cao | Not in MVP; least privilege/testnet/circuit breaker | Reconciliation mismatch |

---

## 19. Quy trình retrain và phát hành model

1. Trigger theo lịch hoặc drift/performance, không tự thay model đang active trong local release.
2. Snapshot data; DQ; tạo train/validation/test theo policy.
3. Train reproducible; compare baseline/champion.
4. Backtest net cost + robustness + fairness theo symbol/regime.
5. Model card và review chéo nếu có cộng tác viên; nếu làm một mình, dùng checklist cố định và review lại sau thời gian “cool-down”, ghi rõ đây không phải independent review.
6. Deploy challenger shadow.
7. Canary nhỏ; theo dõi latency/distribution/calibration/outcome trễ.
8. Promote hoặc rollback; mọi threshold/version audit được.

Không promote chỉ vì accuracy cao hơn nếu expectancy/risk/calibration xấu hơn.

---

## 20. Hạ tầng 0 đồng và giới hạn tài nguyên

### 20.1. Kiến trúc vật lý

- Một máy Windows hiện có chạy frontend, API, worker, database và model.
- Chỉ bind `127.0.0.1` theo mặc định. Nếu dùng LAN, bind IP nội bộ và cấu hình Windows Firewall chỉ cho subnet/thiết bị tin cậy.
- Dữ liệu lưu trong một thư mục cấu hình rõ ràng, không nằm lẫn source code.
- Backup sang ổ đĩa khác **chỉ khi ổ đó đã có sẵn**. Nếu chỉ có một ổ, kế hoạch phải ghi nhận rủi ro mất dữ liệu; không tuyên bố đã có backup an toàn.
- Không yêu cầu máy chạy 24/7; ingestion có cơ chế backfill khi khởi động lại.

### 20.2. Ngân sách tiền mặt

| Hạng mục | Giải pháp MVP | Chi mới |
|---|---|---:|
| Dữ liệu thị trường | Binance public market-data API | 0 VNĐ |
| Backend/ML/frontend | Phần mềm mã nguồn mở | 0 VNĐ |
| Compute | CPU/GPU máy hiện có | 0 VNĐ |
| Database/storage | SQLite, DuckDB, Parquet, filesystem local | 0 VNĐ |
| Domain/hosting/SSL | Không sử dụng; localhost/LAN | 0 VNĐ |
| Monitoring/security scan | Log local + công cụ community/free | 0 VNĐ |
| Nhân sự/tư vấn | Chủ dự án tự thực hiện/cộng tác tự nguyện | 0 VNĐ |
| Trading capital | Không dùng; paper ledger | 0 VNĐ |
| **Tổng tiền mặt tăng thêm** |  | **0 VNĐ** |

Mức 0 VNĐ dựa trên tài liệu/API hiện hành và tài nguyên đã có, không phải cam kết rằng Binance hay các dự án mã nguồn mở sẽ giữ nguyên điều khoản vĩnh viễn. Mỗi lần nâng phiên bản hoặc thay nguồn dữ liệu phải kiểm tra lại license, rate limit và điều khoản sử dụng; nếu phát sinh phí thì không nâng/chuyển trong MVP.

### 20.3. Resource budget thay cho money budget

Ở Sprint 0 phải đo cấu hình máy và đặt trần, ví dụ sau khi benchmark thực tế:

- Disk dataset/artifact: trần cấu hình, cảnh báo ở 70/85/95%.
- RAM: worker/model không được làm hệ thống swap kéo dài.
- CPU: giới hạn concurrency để UI vẫn phản hồi.
- Training: checkpoint/resume; chạy ngoài giờ sử dụng máy.
- Inference: ưu tiên model nhỏ/quantization nếu vẫn giữ chất lượng.
- Retention: tự xóa upload hết hạn; nén/partition Parquet; không lưu timeframe có thể resample nếu không cần audit.

Nếu máy không đủ tài nguyên, thứ tự giảm phạm vi là: giảm số symbol → giảm lịch sử/độ phân giải → dùng tabular model → giảm kích thước ảnh/model. **Không tự chuyển sang dịch vụ trả phí.**

### 20.4. Những điều 0 đồng không thể bảo đảm

- Public uptime/SLA, băng thông và chống DDoS.
- Scale cho 1.000–10.000 MAU.
- Email/SMS/push delivery bảo đảm.
- GPU training nhanh hoặc lưu trữ vô hạn.
- Pentest/chứng nhận/audit pháp lý độc lập.
- High availability hoặc disaster recovery khi chỉ có một máy/ổ đĩa.

Muốn có bất kỳ mục nào trên phải lập phase mới và được chủ dự án đồng ý thay đổi ngân sách; không được âm thầm đưa vào MVP.

---

## 21. Tài liệu phải bàn giao

- PRD và decision log/ADR.
- Data dictionary, lineage, DQ policy.
- Label specification và backtest methodology.
- Feature registry.
- Model card + experiment report + limitations.
- API OpenAPI spec và event schemas.
- Threat model, privacy/retention policy, security checklist.
- Deployment/rollback/backup/incident runbooks.
- User guide và ảnh mẫu đúng/sai.
- Weekly paper report template và Go/No-Go dossier.

---

## 22. Tiêu chí nghiệm thu cuối

### Closed beta được phép khi

- Gate A và B pass; E2E staging pass.
- Model không có leakage đã biết; final holdout report được ký duyệt.
- Upload/mismatch/stale/OOD đều fail-safe về reject/no-trade.
- Security High/Critical = 0; backup restore đã diễn tập.
- Risk engine, kill switch và model rollback hoạt động.
- Legal/privacy copy có phê duyệt sơ bộ.
- Báo cáo chi phí xác nhận không có hóa đơn, subscription, cloud resource hoặc trading capital nào được kích hoạt; tổng chi mới = 0 VNĐ.

### Mở rộng ra public Internet (ngoài phạm vi 0 đồng) chỉ được xem xét khi

- Paper gate đủ thời gian/số mẫu và expectancy net dương.
- Calibration/coverage/latency/SLO đạt mục tiêu.
- Security/compliance review phù hợp hoàn thành; pentest/tư vấn độc lập có thể phát sinh phí.
- Support/on-call/incident workflow sẵn sàng.

### Auto-trading (ngoài phạm vi 0 đồng và ngoài MVP) chỉ được xem xét khi

- Có dự án/PRD riêng; không xem là toggle nhỏ của MVP.
- Testnet ổn định, reconciliation và failure injection pass.
- Bảo mật API key, pháp lý, limit, circuit breaker được duyệt.
- Canary vốn rất nhỏ và khả năng dừng từ server đã kiểm chứng.

---

## 23. Nguồn chính thức cần theo dõi

Các tài liệu có thể thay đổi; connector phải đọc giới hạn động và nhóm vận hành cần kiểm tra changelog định kỳ.

- [Binance Developer Documentation](https://developers.binance.com/en/docs/introduction)
- [Binance API Catalog – USDⓈ-M Futures](https://developers.binance.com/en/docs/catalog)
- [USDⓈ-M Futures WebSocket stream subscription](https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/websocket-market-streams/Live-Subscribing-Unsubscribing-to-streams)
- [USDⓈ-M Futures user data streams](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-api/user-data-streams)
- [Thông tin Nghị quyết 05/2025/NQ-CP về thí điểm thị trường tài sản mã hóa tại Việt Nam](https://xaydungchinhsach.chinhphu.vn/thi-diem-thi-truong-tai-san-ma-hoa-lua-chon-toi-da-05-to-chuc-cung-cap-dich-vu-tai-san-ma-hoa-119250910090649061.htm)
- [Hệ thống văn bản Chính phủ](https://vanban.chinhphu.vn/)

---

## 24. Việc cần làm ngay trong 5 ngày đầu

### Ngày 1

- Chốt D01–D08; viết một trang product brief.
- Chọn 2 symbol và horizon chính.
- Ghi cấu hình CPU/RAM/GPU/disk hiện có và đặt resource budget; xác nhận không nhập thông tin thanh toán vào bất kỳ dịch vụ nào.

### Ngày 2

- Tạo repo/module layout, CI và môi trường dev.
- Viết label spec v0.1 và cost assumptions.

### Ngày 3

- Tạo Binance data spike: tải và validate BTCUSDT 1m/15m/1H.
- Thiết kế SQLite/DuckDB/private filesystem và data retention.

### Ngày 4

- Tạo backtest skeleton + unit test no-lookahead.
- Tạo 20–50 ảnh mẫu nhiều theme để định nghĩa quality rubric.

### Ngày 5

- Review spike, cập nhật estimate/risk register.
- Chốt Sprint 1 backlog và Definition of Done.

---

## 25. Ghi chú cuối

Edge dự đoán trong crypto futures thường nhỏ, thay đổi theo regime và dễ biến mất sau chi phí giao dịch mô phỏng. Thành công của dự án không phải là tạo một màn hình luôn nói Long/Short, mà là xây một hệ thống biết **khi nào không nên giao dịch**, có số liệu out-of-sample đáng tin, quản trị rủi ro cứng và có thể giải thích/truy vết toàn bộ vòng đời của mỗi tín hiệu. Với ràng buộc 0 VNĐ, đích đến hợp lý và trung thực là một hệ thống nghiên cứu/local private beta tốt; public scale và giao dịch thật không được giả định là miễn phí.

