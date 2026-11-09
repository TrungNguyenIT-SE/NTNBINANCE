# Decision Log

Thư mục này lưu các quyết định đã được chấp nhận của dự án. Decision record là append-only: không âm thầm sửa lý do/hệ quả của quyết định cũ sau khi triển khai.

## Quy ước trạng thái

- `PROPOSED`: đang xem xét, chưa được dùng làm yêu cầu khóa.
- `ACCEPTED`: đã chốt và có hiệu lực.
- `SUPERSEDED`: được thay bằng decision record mới; giữ file cũ để audit.
- `REJECTED`: đã xem xét nhưng không chọn.

## Danh mục

| ID | Tiêu đề | Trạng thái | Ngày |
|---|---|---|---|
| ADR-0001 | Quyết định sản phẩm MVP D01–D08 | ACCEPTED | 09/11/2026 |

## Quy tắc thay đổi

Một thay đổi ảnh hưởng D01–D08 phải có ADR mới, nêu tác động đến PRD, dữ liệu, model, kiểm thử, bảo mật, timeline và ngân sách. Không sửa lịch sử để làm thay đổi trông như đã được chấp nhận từ đầu.
