# PRODUCT REQUIREMENTS DOCUMENT — BINANCE FUTURES SIGNAL MVP

> Document ID: `PRD-BFS-001`  
> Version: `1.0`  
> Status: `LOCKED FOR MVP`  
> Effective date: `09/11/2026`  
> Owner: Chủ dự án  
> Scope: Local/private research MVP, ngân sách tiền mặt tăng thêm 0 VNĐ  
> Related plan: [`../plan.md`](../plan.md)  
> Decision record: [`decisions/0001-mvp-product-decisions.md`](decisions/0001-mvp-product-decisions.md)

## 1. Mục đích tài liệu

Tài liệu này khóa yêu cầu sản phẩm cho MVP của hệ thống phân tích Binance USDⓈ-M perpetual từ hai ảnh biểu đồ nến 1H và 15m, kết hợp dữ liệu thị trường Binance để trả về một trong ba trạng thái `LONG`, `SHORT` hoặc `NO_TRADE`.

PRD trả lời chính xác:

- Sản phẩm giải quyết vấn đề gì và cho ai.
- Input nào được chấp nhận và output nào phải trả về.
- Điều gì thuộc và không thuộc MVP.
- Quy tắc sản phẩm nào không được mô hình tự ý vượt qua.
- Điều kiện nghiệm thu có thể đo được.
- Khi nào MVP phải từ chối phân tích hoặc trả `NO_TRADE`.

PRD không mô tả chi tiết thuật toán triển khai. Label, feature, model, backtest và risk engine sẽ có đặc tả riêng ở các giai đoạn sau nhưng không được mâu thuẫn với tài liệu này.

## 2. Bối cảnh và vấn đề

Người dùng thường xem đồng thời biểu đồ 1H và 15m để đánh giá xu hướng lớn và điểm kích hoạt ngắn hạn. Quy trình thủ công có các vấn đề:

- Nhận định dễ thiếu nhất quán và chịu ảnh hưởng cảm xúc.
- Ảnh biểu đồ có thể thiếu symbol, timeframe, timestamp hoặc chứa nến chưa đóng.
- Chỉ nhìn hình ảnh không phản ánh đầy đủ funding, mark price, volume và trạng thái dữ liệu.
- Một hệ thống luôn buộc chọn Long/Short sẽ tạo tín hiệu ngay cả khi không có lợi thế.
- Accuracy cao không đồng nghĩa có lợi nhuận sau fee, spread, funding và slippage.

MVP cần chuẩn hóa quy trình phân tích, có khả năng từ chối input không đáng tin và lưu đầy đủ bằng chứng để đánh giá bằng paper trading. MVP không hứa hẹn lợi nhuận và không thay người dùng thực hiện giao dịch.

## 3. Product statement

Đối với người nghiên cứu giao dịch crypto futures cần đánh giá nhất quán hai khung 1H/15m, sản phẩm là một web app chạy local cho phép tải hai ảnh chart, kiểm tra chất lượng và đối chiếu dữ liệu Binance, sau đó trả tín hiệu xác suất `LONG / SHORT / NO_TRADE` cùng lý do và giới hạn rủi ro. Khác với công cụ chỉ phân loại ảnh, sản phẩm ưu tiên từ chối khi dữ liệu không đủ và đánh giá kết quả sau chi phí giao dịch mô phỏng.

## 4. Người dùng mục tiêu

### 4.1. Primary user

Chủ dự án hoặc thành viên beta nội bộ có hiểu biết cơ bản về:

- Nến OHLCV và timeframe.
- Binance USDⓈ-M perpetual.
- Stop-loss, take-profit và rủi ro đòn bẩy.
- Khác biệt giữa tín hiệu xác suất và bảo đảm lợi nhuận.

### 4.2. Không phải người dùng mục tiêu của MVP

- Công chúng trên Internet.
- Người muốn hệ thống tự quản lý tiền hoặc tự đặt lệnh.
- Người cần SLA 24/7, tín hiệu tần suất cao hoặc độ trễ cấp mili-giây.
- Người coi kết quả là tư vấn tài chính hoặc cam kết sinh lời.
- Người không thể tự chịu trách nhiệm về quyết định giao dịch của mình.

### 4.3. Môi trường sử dụng

- Một máy Windows hiện có.
- Truy cập qua `localhost`; LAN riêng chỉ khi được cấu hình rõ ràng.
- Có Internet để lấy market data công khai từ Binance.
- Không public hosting, domain, cloud hoặc dịch vụ trả phí.

## 5. Mục tiêu sản phẩm

### G01 — Chuẩn hóa input

Nhận đúng một cặp ảnh 1H + 15m, symbol và thời điểm tham chiếu; phát hiện ảnh sai, mờ, stale hoặc không khớp.

### G02 — Phát tín hiệu có quyền abstain

Trả đúng một trong ba trạng thái `LONG`, `SHORT`, `NO_TRADE`; `NO_TRADE` là kết quả hợp lệ, không phải lỗi.

### G03 — Kết hợp ảnh và dữ liệu chuẩn

Ảnh là một nguồn tín hiệu/kiểm tra ngữ cảnh. Dữ liệu Binance theo thời điểm là nguồn bổ sung bắt buộc khi khả dụng; hệ thống không giả vờ có dữ liệu nếu nguồn bị stale hoặc thiếu.

### G04 — Kết quả có thể truy vết

Mỗi prediction phải truy được request, input hash, symbol, decision time, model/feature/policy version và outcome sau này.

### G05 — Đánh giá thực tế

Đo hiệu năng bằng final holdout và paper trading sau fee, spread, funding, slippage và latency mô phỏng; không dùng accuracy đơn lẻ để tuyên bố thành công.

### G06 — Chi phí tiền mặt bằng 0

Không phát sinh thanh toán mới để xây hoặc chạy local MVP. Khi tài nguyên máy không đủ, giảm phạm vi/model thay vì tự chuyển sang dịch vụ trả phí.

## 6. Non-goals — không thuộc MVP

- Không tự động đặt, sửa hoặc hủy lệnh Binance.
- Không kết nối API key có quyền `TRADE`, `USER_DATA` hoặc withdrawal.
- Không nạp tiền, giữ tài sản, copy trading hoặc quản lý danh mục thật.
- Không public Internet, không domain, không mobile app native.
- Không bán subscription, nhận thanh toán hoặc quảng cáo lợi nhuận.
- Không hỗ trợ Spot, COIN-M, Options hoặc sàn khác.
- Không hỗ trợ ngoài `BTCUSDT`, `ETHUSDT` trong MVP.
- Không buộc model phải dùng deep learning/vision nếu không vượt baseline.
- Không cam kết win rate, lợi nhuận, SLA hoặc dự đoán đúng mọi regime.
- Không cá nhân hóa theo tài khoản thật hoặc leverage của người dùng.
- Không dùng upload của người dùng để train nếu chưa có opt-in rõ ràng.
- Không dùng free tier làm dependency bắt buộc.

Mọi yêu cầu thuộc non-goals cần change request và phiên bản PRD mới; không được lén thêm vào MVP.

## 7. Quyết định sản phẩm đã khóa

| ID | Quyết định đã chốt | Trạng thái |
|---|---|---|
| D01 | MVP chỉ phát tín hiệu, không tự đặt lệnh | Accepted |
| D02 | Horizon chính: 4 nến 15m = 60 phút; 2 và 8 nến là phân tích phụ | Accepted |
| D03 | `BTCUSDT`, `ETHUSDT`, Binance USDⓈ-M perpetual | Accepted |
| D04 | Ảnh từ Binance/TradingView theo template được kiểm định | Accepted |
| D05 | Người dùng nội bộ/private beta | Accepted |
| D06 | Tổng chi tiền mặt tăng thêm = 0 VNĐ | Accepted |
| D07 | Local/private tại Việt Nam; không public, thu tiền hoặc giao dịch thật | Accepted |
| D08 | Mức rủi ro tham khảo tối đa 0,25–0,5% tài khoản/tín hiệu | Accepted |

Chi tiết lý do và hệ quả nằm trong decision record liên kết ở đầu tài liệu.

## 8. Phạm vi chức năng

### 8.1. Input contract

Mỗi prediction request phải có:

| Trường | Bắt buộc | Quy tắc MVP |
|---|---:|---|
| `symbol` | Có | Chỉ `BTCUSDT` hoặc `ETHUSDT` |
| `image_1h` | Có | Ảnh chart khung 1H |
| `image_15m` | Có | Ảnh chart khung 15m |
| `captured_at` | Có | Timestamp user khai báo; lưu UTC |
| `source` | Có | `BINANCE`, `TRADINGVIEW` hoặc `UNKNOWN` |
| `user_confirmation` | Có | Xác nhận hai ảnh cùng symbol và gần cùng thời điểm |

Quy tắc ảnh sơ bộ, được khóa chi tiết ở Giai đoạn K:

- Định dạng: PNG, JPEG hoặc WebP.
- Giới hạn ban đầu: 10 MB/ảnh; cạnh 800–4096 px, có thể siết sau benchmark nhưng không được nới thiếu kiểm soát.
- Hai ảnh phải cùng symbol.
- Ảnh 1H và 15m phải đại diện cùng ngữ cảnh thời gian hợp lý.
- Không tin extension, filename, EXIF hoặc metadata do client cung cấp.
- Nến dùng cho quyết định phải là nến đã đóng; nếu không xác minh được thì từ chối hoặc `NO_TRADE`.

### 8.2. Input rejection và abstention

Phân biệt:

- `REJECTED_INPUT`: request không thể xử lý vì file hỏng, thiếu ảnh, sai format, symbol ngoài scope hoặc mismatch chắc chắn.
- `NO_TRADE`: input có thể xử lý nhưng chất lượng/tín hiệu/rủi ro không đủ để khuyến nghị hướng.
- `FAILED_RETRYABLE`: lỗi tạm thời như Binance/worker timeout; có thể retry idempotent.
- `FAILED`: lỗi nội bộ không retry tự động tiếp.

Hệ thống phải reject hoặc `NO_TRADE` khi:

- Hai ảnh khác symbol hoặc sai timeframe.
- Ảnh stale vượt threshold đã version hóa.
- Ảnh mờ/crop/che chart dưới quality threshold.
- Không đủ dữ liệu market tại decision time.
- Nến cuối chưa đóng và không thể loại bỏ đáng tin cậy.
- Input ngoài phân phối hoặc model uncertainty cao.
- Hard risk rule không đạt.

### 8.3. Output contract

Prediction hoàn tất phải có:

| Trường | Ý nghĩa |
|---|---|
| `prediction_id` | ID duy nhất, không đổi |
| `request_id` | ID truy vết toàn pipeline |
| `symbol` | `BTCUSDT` hoặc `ETHUSDT` |
| `decision_time` | Thời điểm quyết định UTC |
| `signal` | `LONG`, `SHORT` hoặc `NO_TRADE` |
| `p_long` | Xác suất đã calibration |
| `p_short` | Xác suất đã calibration |
| `p_no_trade` | Xác suất đã calibration |
| `confidence` | Giá trị theo policy, không gọi là tỷ lệ chắc thắng |
| `valid_until` | Thời hạn hiệu lực của tín hiệu |
| `entry_zone` | Vùng tham khảo hoặc null với `NO_TRADE` |
| `invalidation` | Điều kiện vô hiệu hoặc null |
| `stop_loss` | Mức tham khảo hoặc null |
| `take_profit` | Một/nhiều mức tham khảo hoặc null |
| `risk_reward` | R:R dự kiến sau rule hoặc null |
| `reason_codes` | Danh sách lý do có cấu trúc |
| `warnings` | Stale/quality/coverage/uncertainty warnings |
| `model_version` | Phiên bản model |
| `feature_version` | Phiên bản feature set |
| `policy_version` | Phiên bản calibration/risk/signal policy |
| `created_at` | Timestamp UTC |

Invariant bắt buộc:

- `p_long + p_short + p_no_trade` xấp xỉ 1 trong dung sai số học đã định nghĩa.
- `NO_TRADE` không được hiển thị entry/SL/TP như một lệnh hành động.
- `LONG/SHORT` không được phát nếu hard risk rule fail.
- UI luôn ghi rõ confidence không phải xác suất lợi nhuận được bảo đảm.
- Prediction đã phát không bị sửa lại sau khi biết outcome; outcome là record riêng.

### 8.4. Lý do kết quả

Lý do phải sinh từ facts có cấu trúc, ví dụ:

- `TREND_1H_BULLISH`
- `TREND_1H_BEARISH`
- `MOMENTUM_15M_CONFIRM`
- `VOLATILITY_TOO_HIGH`
- `IMAGE_QUALITY_LOW`
- `TIMEFRAME_MISMATCH`
- `MARKET_DATA_STALE`
- `CONFIDENCE_BELOW_THRESHOLD`
- `EXPECTED_RETURN_NOT_POSITIVE`
- `RISK_GATE_BLOCKED`

Không dùng một mô hình ngôn ngữ để tự bịa lý do không có trong feature/risk facts.

## 9. User journeys

### UJ01 — Prediction hợp lệ

1. User mở web app local.
2. Chọn `BTCUSDT` hoặc `ETHUSDT`.
3. Upload ảnh 1H và 15m.
4. Nhập/xác nhận thời điểm chụp và nguồn ảnh.
5. Hệ thống validate ảnh, đối chiếu market data và hiển thị tiến trình.
6. Hệ thống chạy feature/model/risk policy.
7. UI hiển thị `LONG`, `SHORT` hoặc `NO_TRADE`, lý do, warning và version.
8. Prediction xuất hiện trong lịch sử; outcome được bổ sung sau horizon, không sửa prediction.

### UJ02 — Input sai

1. User upload thiếu ảnh, sai định dạng hoặc hai timeframe không khớp.
2. Hệ thống không chạy inference không cần thiết.
3. UI nêu lỗi cụ thể và hướng dẫn sửa.
4. Không tạo signal hành động.

### UJ03 — Data Binance tạm thời lỗi

1. Ảnh hợp lệ nhưng nguồn market data timeout/stale.
2. Hệ thống retry hữu hạn, không tạo duplicate request.
3. Nếu không phục hồi, trả trạng thái retryable hoặc `NO_TRADE` theo policy.
4. Không dùng dữ liệu cũ mà không cảnh báo.

### UJ04 — Xem lịch sử

1. User mở lịch sử local.
2. Lọc theo symbol, signal, ngày và model version.
3. Xem prediction nguyên bản và outcome tách biệt.
4. Có thể truy model/feature/policy version và warning tại thời điểm phát.

## 10. Functional requirements

### FR-01 — Symbol scope

Hệ thống chỉ chấp nhận `BTCUSDT` và `ETHUSDT` USDⓈ-M perpetual. Symbol khác phải bị reject bằng lỗi có cấu trúc.

### FR-02 — Dual-image requirement

Không được tạo prediction nếu thiếu một trong hai ảnh 1H hoặc 15m.

### FR-03 — Image validation

Server phải kiểm tra MIME thực, decode, kích thước byte/pixel, loại metadata và lưu ngoài web root.

### FR-04 — Context validation

Hệ thống phải đối chiếu symbol, timeframe, thời gian và giá cuối ảnh ở mức khả thi; mismatch rõ ràng phải fail-safe.

### FR-05 — Closed-candle policy

Chỉ dữ liệu đã đóng tại `decision_time` được dùng làm feature. Nến đang chạy không được coi là close đã biết.

### FR-06 — Three-class output

Hệ thống phải hỗ trợ ba trạng thái và không có code path buộc chọn nhị phân Long/Short.

### FR-07 — Prediction traceability

Mỗi prediction lưu input hashes, timestamps, data/feature/model/policy versions và latency.

### FR-08 — Idempotency

Retry cùng idempotency key không được tạo nhiều prediction độc lập.

### FR-09 — History immutability

Prediction record không được cập nhật theo outcome; correction phải tạo audit event/version rõ ràng.

### FR-10 — Paper outcome

Sau horizon, hệ thống có thể tính gross/net outcome bằng cost assumptions đã version hóa.

### FR-11 — Local-only operation

Default bind là `127.0.0.1`. LAN phải là cấu hình chủ động; không có public deployment script trong MVP.

### FR-12 — Zero-cost enforcement

Không có dependency runtime bắt buộc yêu cầu subscription, credit card hoặc paid API.

## 11. Non-functional requirements

### NFR-01 — Performance

Mục tiêu p95 từ khi upload hoàn tất đến kết quả là ≤ 5 giây trên máy hiện có. Giai đoạn B phải benchmark. Nếu không đạt, công bố SLO thực đo tối đa đề xuất 15 giây hoặc giảm độ phức tạp; không thuê compute.

### NFR-02 — Reliability

Local beta phải ổn định trong phiên sử dụng. Không cam kết SLA 24/7. Ingestion phải backfill/reconcile được sau khi ứng dụng tắt.

### NFR-03 — Security

Không có Critical/High đã biết trước private beta. File upload, authz, path traversal, secret leakage và dependency risk phải có test/self-review.

### NFR-04 — Privacy

Ảnh private, lưu ngoài web root và có retention/deletion. Mặc định không dùng upload để train.

### NFR-05 — Reproducibility

Prediction phải map được đến model, feature, label, policy và code version. Training run quan trọng phải có config/seed/data manifest/checksum.

### NFR-06 — Accessibility

Luồng chính dùng được bằng keyboard; trạng thái không chỉ biểu đạt bằng màu; lỗi có text rõ ràng.

### NFR-07 — Resource safety

Ứng dụng phải tôn trọng trần RAM/disk/CPU sau benchmark và fail rõ ràng khi disk gần đầy.

### NFR-08 — Maintainability

Core business rules có unit test; schema/API được version hóa; setup/run/test có tài liệu.

## 12. Acceptance criteria MVP

### Nhóm A — Scope và input

- **AC-001:** Given symbol ngoài `BTCUSDT/ETHUSDT`, when tạo request, then API trả validation error và không chạy model.
- **AC-002:** Given thiếu ảnh 1H hoặc 15m, when submit, then request bị reject và không có signal.
- **AC-003:** Given file giả extension/MIME hoặc không decode được, when upload, then file bị reject và không lưu như ảnh hợp lệ.
- **AC-004:** Given hai ảnh mismatch symbol/timeframe rõ ràng, when validate, then trả `REJECTED_INPUT` hoặc `NO_TRADE` theo reason code đã khóa, không trả Long/Short.
- **AC-005:** Given ảnh/data stale, when phân tích, then không trả signal hành động không cảnh báo.

### Nhóm B — Prediction contract

- **AC-006:** Mọi prediction hoàn tất có đúng một `signal` trong `LONG/SHORT/NO_TRADE`.
- **AC-007:** Tổng ba xác suất nằm trong dung sai `|sum - 1| ≤ 1e-6` sau serialization hoặc dung sai được đặc tả chính thức.
- **AC-008:** `NO_TRADE` không có CTA mang nghĩa đặt lệnh và không hiển thị entry/SL/TP như khuyến nghị hành động.
- **AC-009:** Hard risk gate fail luôn chặn `LONG/SHORT` trong 100% unit/integration cases.
- **AC-010:** Mọi prediction có request ID, decision time, input hashes và model/feature/policy version.

### Nhóm C — Data integrity

- **AC-011:** Automated test chứng minh feature tại T không đọc record có `event_time > T`.
- **AC-012:** Nến chưa đóng không được dùng như nến đóng trong 100% boundary tests.
- **AC-013:** Duplicate/gap/out-of-order được phát hiện và gắn quality flag hoặc quarantine.
- **AC-014:** Retry ingest/reprocess không tạo duplicate theo unique key.

### Nhóm D — Model/research

- **AC-015:** Final split theo thời gian, purged/embargo và manifest được khóa trước khi mở final holdout.
- **AC-016:** Model candidate phải được so với majority/random/rule/tabular baseline bằng cùng dataset/cost model.
- **AC-017:** Báo cáo có macro F1, per-class metrics, Brier/ECE, coverage và confusion matrix; không chỉ accuracy.
- **AC-018:** Backtest báo net PnL/expectancy sau fee, spread, slippage, funding và latency giả định.
- **AC-019:** Paper gate chỉ pass sau 8–12 tuần hoặc ≥ 300 signal độc lập theo điều kiện chặt hơn, với risk limits không bị vi phạm.

### Nhóm E — API/UI

- **AC-020:** Retry cùng idempotency key tạo tối đa một prediction logic.
- **AC-021:** User hoàn thành upload → validation → result → history bằng UI local mà không dùng terminal.
- **AC-022:** UI luôn hiển thị symbol, decision time, signal, confidence disclaimer, validity và warnings.
- **AC-023:** Prediction cũ giữ nguyên sau outcome; outcome hiển thị tách biệt.
- **AC-024:** p95 đạt mục tiêu đã benchmark hoặc UI/tài liệu công bố SLO local thực tế; không che giấu kết quả không đạt 5 giây.

### Nhóm F — Security/privacy/zero cost

- **AC-025:** File không thể ghi ra ngoài storage root bằng filename/path payload trong security tests.
- **AC-026:** Session/user A không đọc hoặc xóa upload/prediction của B trong authz tests nếu private beta có nhiều user.
- **AC-027:** Log không chứa base64 ảnh, secret, token hoặc full sensitive path.
- **AC-028:** Retention/deletion job xóa upload hết hạn theo policy và ghi audit phù hợp.
- **AC-029:** Secret/dependency/license/self-security scan không còn Critical/High đã biết trước release.
- **AC-030:** Báo cáo release xác nhận không có cloud, paid API, subscription, domain, trading capital hoặc hóa đơn mới; tổng chi tiền mặt tăng thêm bằng 0 VNĐ.

## 13. Product success metrics

### 13.1. Product/system metrics

- Upload/prediction completion rate trên input hợp lệ.
- Rejection rate theo reason code.
- p50/p95 latency theo hardware/config.
- Job retry/failure rate.
- Data freshness và gap count.
- Tỷ lệ prediction truy vết đủ version/hash.

### 13.2. Model/strategy metrics

- Macro F1 và per-class precision/recall.
- Brier score, ECE và reliability theo confidence bucket.
- Coverage/abstain rate.
- Expectancy net, profit factor, max drawdown.
- Walk-forward fold stability.
- Paper/backtest divergence.

### 13.3. Không dùng làm success claim độc lập

- Accuracy tổng thể.
- Win rate không kèm average win/loss và costs.
- Một tháng tốt hoặc vài giao dịch outlier.
- Training metric.
- Confidence chưa calibration.

## 14. Product rules không được phá vỡ

1. Không có dữ liệu đáng tin → không có signal hành động.
2. Không đủ edge sau cost → `NO_TRADE`.
3. Hard risk rule luôn ưu tiên model output.
4. Prediction không bị rewrite sau outcome.
5. Test/final holdout không được dùng để tune.
6. Không mở rộng symbol/source/user trước gate tương ứng.
7. Không tự chuyển sang dịch vụ trả phí.
8. Không gọi confidence là cam kết thắng/lợi nhuận.
9. Không đặt lệnh thật trong MVP.
10. Không public app trong MVP.

## 15. Dependencies và giả định

- Binance public market-data API khả dụng theo khu vực và rate limit hiện hành.
- Máy hiện có đủ chạy ít nhất baseline numeric và web app local.
- User cung cấp đúng hai ảnh và metadata trung thực; hệ thống vẫn phải verify trong khả năng.
- Một số derivative features có lịch sử ngắn; model v1 không phụ thuộc feature thiếu coverage.
- Điện, Internet, máy và thời gian lao động được xem là tài nguyên đã có, không phải chi mới.
- Nếu Binance/API không khả dụng, hệ thống dừng/live-degrade hoặc dùng cache đúng policy; không mua proxy/VPN/data.

## 16. Rủi ro sản phẩm chính

| Rủi ro | Tác động | Product response |
|---|---|---|
| Ảnh không đủ thông tin | Signal sai | Validate, cross-check, reject/no-trade |
| Model học artifact của chart renderer | Không generalize ảnh thật | Domain test, ablation, numeric champion fallback |
| Leakage/overfit | Backtest ảo | Time split, purge/embargo, holdout, paper gate |
| Cost xóa edge | Không có lợi nhuận ròng | Net labeling/backtest, stress cost |
| Regime drift | Performance giảm | Drift monitor, abstain, freeze/rollback |
| Máy local thiếu tài nguyên | Chậm/crash | Giảm scope/model, resource budget |
| Binance outage/rate limit | Data stale | Backoff, reconcile, fail-safe |
| Người dùng hiểu sai confidence | Rủi ro tài chính | Disclaimer, `NO_TRADE`, không ngôn ngữ bảo đảm |
| Pháp lý/điều khoản thay đổi | Không được public/use | Local research, review trước mở rộng |

## 17. Release boundary

MVP được coi là hoàn thành sản phẩm chỉ khi:

- Checklist A–Z và các Exit Gate bắt buộc đã pass.
- Go/No-Go record là `GO` hoặc `CONDITIONAL GO` chỉ cho nhóm private được nêu rõ.
- Không còn Critical/High đã biết.
- Paper report và known limitations được bàn giao.
- Tổng chi tiền mặt tăng thêm vẫn là 0 VNĐ.

Public hosting, thương mại hóa hoặc auto-trading không phải “bản cập nhật nhỏ”; mỗi mục cần PRD, risk assessment và quyết định ngân sách/pháp lý riêng.

## 18. Change control

PRD v1.0 đang ở trạng thái `LOCKED FOR MVP`.

Mọi thay đổi D01–D08, symbol, horizon chính, output classes, public/private boundary, auto-trading hoặc zero-cost constraint phải:

1. Tạo decision record mới trong `docs/decisions/`.
2. Nêu lý do, lựa chọn thay thế, tác động data/model/test/security/timeline.
3. Tăng phiên bản PRD.
4. Cập nhật `plan.md` và acceptance criteria liên quan.
5. Không hồi tố sửa prediction/report cũ.

## 19. Approval record

| Vai trò | Trạng thái | Ngày | Ghi chú |
|---|---|---|---|
| Product owner | Approved by project instruction | 09/11/2026 | Thực hiện Giai đoạn A theo `plan.md` |
| Engineering | Self-reviewed | 09/11/2026 | Local-first, zero-cost, implementable |
| ML/Data | Self-reviewed | 09/11/2026 | Ba lớp, time split, costs, paper gate |
| Security/Compliance | Scope-reviewed | 09/11/2026 | Private research only; không phải independent legal/security audit |

Giới hạn: đây là self-review trong dự án 0 VNĐ, không phải chứng nhận chuyên môn độc lập.
