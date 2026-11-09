# ZERO-COST POLICY VÀ LEDGER

> Document ID: `COST-BFS-001`  
> Version: `1.0`  
> Status: `ENFORCED FOR MVP`  
> Effective date: `09/11/2026`  
> Currency: VND  
> Budget owner: Chủ dự án

## 1. Định nghĩa 0 VNĐ

“0 VNĐ” trong MVP nghĩa là **không phát sinh khoản thanh toán tiền mặt mới** cho dự án:

- Không mua phần mềm/license/data/domain.
- Không thuê cloud/server/GPU/database/storage/CDN.
- Không mua API quota, proxy, VPN hoặc CAPTCHA.
- Không trả subscription/SaaS/email/SMS/push.
- Không thuê nhân sự, luật sư, pentest hoặc audit.
- Không nạp trading capital và không giao dịch thật.

Máy tính, điện, Internet, ổ đĩa và thời gian lao động đã có là tài nguyên sẵn có. Chúng có chi phí kinh tế nhưng không phải khoản chi mới của project. Tài liệu không tuyên bố “không tiêu hao điện/thời gian”.

## 2. Tuyên bố của chủ dự án

Yêu cầu đã được chủ dự án nêu rõ: không tốn bất kỳ khoản phí nào từ dự án. Theo đó:

- Không thiết kế workflow yêu cầu nhập thẻ hoặc phương thức thanh toán.
- Không tạo cloud resource hoặc paid account.
- Không kích hoạt trial có auto-convert sang trả phí.
- Không phụ thuộc free tier từ bên thứ ba.
- Nếu một dependency/service thay đổi thành trả phí, pin/replace/remove; không tự chấp nhận điều khoản trả phí.

## 3. Money budget ledger ban đầu

| Hạng mục | Giải pháp MVP | Chi mới đã duyệt | Trạng thái |
|---|---|---:|---|
| Máy tính | Máy Windows hiện có | 0 VNĐ | Available |
| CPU/GPU/RAM | Phần cứng hiện có | 0 VNĐ | Available |
| Dữ liệu thị trường | Binance public market-data endpoints theo điều khoản/rate limit hiện hành | 0 VNĐ | Planned |
| Source control | Git local | 0 VNĐ | Available |
| Backend/data/ML | Open-source/free local packages sau license review | 0 VNĐ | Planned |
| Database/storage | SQLite, DuckDB, Parquet, private filesystem | 0 VNĐ | Planned |
| Frontend | Open-source local build | 0 VNĐ | Planned |
| Monitoring | Structured log/metrics local | 0 VNĐ | Planned |
| Security scan | Community/open-source/local tools | 0 VNĐ | Planned |
| Hosting/domain/SSL | Không dùng; localhost/LAN | 0 VNĐ | Excluded |
| Cloud/GPU rental | Không dùng | 0 VNĐ | Excluded |
| Email/SMS/push | Không dùng | 0 VNĐ | Excluded |
| Nhân sự/tư vấn/audit | Chủ dự án tự làm/self-review | 0 VNĐ | No external purchase |
| Trading capital/fees thật | Không giao dịch thật | 0 VNĐ | Excluded |
| **Tổng chi tiền mặt tăng thêm** |  | **0 VNĐ** | **PASS** |

## 4. Allowed

- Tải package mã nguồn mở/miễn phí từ nguồn chính thức sau license review.
- Dùng máy/GPU/Internet hiện có.
- Dùng Binance public endpoints trong rate limit/điều khoản hiện hành.
- Chạy localhost hoặc LAN riêng.
- Lưu local vào quota đã khóa trong `HARDWARE.md`.
- Paper trading hoàn toàn mô phỏng.
- Dùng công cụ community edition nếu không yêu cầu payment method và không là dependency dịch vụ.

## 5. Prohibited

- Nhập credit/debit card hoặc billing account cho project.
- Cloud resource kể cả “free trial” có nguy cơ tính phí.
- Public tunnel/hosting/domain/CDN là runtime dependency.
- Paid dataset, premium chart API hoặc mua lịch sử order book.
- Thuê GPU/Colab paid/notebook paid.
- Proxy/VPN trả phí để vượt hạn chế vùng/API.
- SaaS monitoring/error tracking/email/SMS trả phí.
- Package/library có license bắt buộc mua cho intended use.
- Trading key, trading deposit hoặc live order.
- “Chi trước, hoàn lại sau” hoặc khoản nhỏ không ghi ledger.

## 6. Free-tier policy

Free tier không được coi là dependency bắt buộc vì:

- Quota/điều khoản có thể thay đổi.
- Có thể yêu cầu payment method.
- Có thể tự chuyển sang billable usage.
- Có thể bị suspend, mất dữ liệu hoặc giới hạn vùng.

Nếu dùng một free service tùy chọn để thử nghiệm, local path vẫn phải hoạt động đầy đủ khi service biến mất; không lưu secret/payment method và phải có ADR riêng. MVP hiện không phê duyệt service nào như vậy.

## 7. Cost controls trong code/repository

Stage C trở đi phải áp dụng:

- Không có Terraform/cloud deployment/billing config trong đường chạy MVP.
- `.env.example` không chứa cloud/API trading variables bắt buộc.
- Dependency lockfile và license inventory.
- Config mặc định bind `127.0.0.1`.
- Feature flag khóa public/live/paid integration.
- Không có code tự tạo resource external có phí.
- Release checklist tìm các từ khóa billing/payment/cloud endpoint/trading key.

## 8. Resource budget thay money budget

Các giới hạn chính từ `HARDWARE.md`:

- Project disk quota: 60 GiB.
- Stop write khi project ≥ 57 GiB hoặc volume `D:` free < 40 GiB.
- Runtime target RAM ≤ 2,5 GiB; một inference worker.
- Training target ≤ 8 GiB RAM; hard guard 10 GiB.
- GPU target ≤ 4,5 GiB VRAM; hard guard 5,2 GiB.
- Training tuần tự/time-box; không thuê compute nếu chậm.

## 9. Monthly/release cost verification template

Điền ở mỗi release hoặc ít nhất hàng tháng trong thời gian phát triển:

| Câu hỏi | Kết quả hiện tại |
|---|---|
| Có hóa đơn/subscription mới? | Không |
| Có cloud resource đang chạy? | Không |
| Có payment method gắn với dependency dự án? | Không theo thiết kế/phạm vi đã duyệt |
| Có domain/hosting/CDN trả phí? | Không |
| Có paid API/data/proxy/VPN? | Không |
| Có trading deposit/live order? | Không |
| Có dependency đổi license/giá? | Chưa; phải kiểm tra lại khi pin version |
| Tổng chi mới | 0 VNĐ |

Lưu ý trung thực: repository không thể tự xác minh mọi tài khoản cá nhân bên ngoài. Kết quả dựa trên kiến trúc project, workspace và tuyên bố ngân sách của chủ dự án; trước release chủ dự án phải xác nhận ledger.

## 10. Exception/change process

Không có “ngoại lệ nhỏ”. Mọi đề xuất phát sinh phí phải:

1. Dừng triển khai mục đó.
2. Tạo ADR nêu chi phí một lần/định kỳ/worst case và lựa chọn 0 VNĐ.
3. Chỉ tiếp tục khi chủ dự án chủ động thay đổi yêu cầu ngân sách bằng văn bản.
4. Cập nhật PRD, plan, ledger và acceptance criteria.

Nếu không có chấp thuận mới, phương án mặc định là giảm scope, thay dependency hoặc bỏ tính năng.

## 11. Gate conclusion

**PASS — Kiến trúc MVP không có dependency bắt buộc trả phí; money budget được khóa ở 0 VNĐ.**
