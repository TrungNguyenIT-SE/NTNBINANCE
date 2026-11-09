# THIRD-PARTY LICENSE REGISTER

> Version: `0.2 — Stage C locked environment`  
> Date: `09/11/2026`  
> Policy: Chưa có package nào được phê duyệt cho release chỉ dựa trên tên/license trong bảng này. Version pin ở Stage C phải được scan và lưu license text thực tế.

## 1. Quy tắc phê duyệt dependency

Mỗi dependency trước khi đưa vào runtime/release phải có:

1. Tên chính xác và version pin.
2. Nguồn chính thức/package registry.
3. License identifier và license text đi kèm artifact đã cài.
4. Kiểm tra transitive dependencies.
5. Xác nhận intended use không yêu cầu phí/license thương mại.
6. Ghi attribution/notice/source obligations nếu có.
7. Security/advisory scan.
8. Quyết định `APPROVED`, `CONDITIONAL` hoặc `REJECTED`.

License upstream có thể thay đổi theo version. Không suy ra license version mới từ version cũ.

## 2. Công cụ/runtime hiện có trên máy

| Thành phần | Version phát hiện | License dự kiến/cần kiểm tra | Dùng trong release | Trạng thái |
|---|---:|---|---:|---|
| Python | 3.14.2 | Python Software Foundation License; kiểm tra distribution | Có thể | CONDITIONAL |
| Git for Windows | 2.52.0 | GPL-2.0 family; tool development, không bundle mặc định | Không bundle | CONDITIONAL |
| Node.js | 24.13.0 | MIT + bundled third-party notices; kiểm tra distribution | Có thể, build tool | CONDITIONAL |
| npm | 11.6.2 | Artistic-2.0; kiểm tra distribution/transitives | Build tool | CONDITIONAL |
| Docker Desktop/CLI | 29.6.2 | Có điều khoản sử dụng riêng; không giả định luôn miễn phí cho mọi đối tượng | Không bắt buộc | NOT REQUIRED |
| NVIDIA driver/`nvidia-smi` | 591.44 | Proprietary driver terms; đã có sẵn trên máy | Không bundle | SYSTEM COMPONENT |
| Microsoft Defender | System | Windows component terms | Không bundle | SYSTEM COMPONENT |

Docker không là dependency bắt buộc của MVP. Đường chạy chuẩn là Python environment local để tránh license/overhead/daemon không cần thiết.

## 3. Python packages đã phát hiện

| Package | Version | License family dự kiến từ artifact/upstream | Vai trò dự kiến | Stage B status |
|---|---:|---|---|---|
| NumPy | 2.4.2 | BSD-3-Clause; artifact có `LICENSE.txt` và third-party license directory | Numeric compute | CONDITIONAL |
| scikit-learn | 1.9.0 | BSD-3-Clause; artifact có `COPYING` | Baseline/model | CONDITIONAL |
| pandas | 3.0.3 | BSD-3-Clause; metadata/artifact có license | Data inspection | CONDITIONAL |
| Pillow | 12.1.1 | HPND/PIL-style; artifact có `LICENSE` | Image decode/re-encode | CONDITIONAL |

`CONDITIONAL` nghĩa là package có vẻ phù hợp cho spike nhưng Stage C vẫn phải pin version, copy/record license text, scan transitives và chạy compatibility tests trong project environment.

## 4. Dependency đã pin và kiểm tra ở Stage C

### Python direct/runtime/development

| Package | Version | License từ installed artifact metadata | Vai trò | Trạng thái |
|---|---:|---|---|---|
| FastAPI | 0.162.2 | MIT | API | APPROVED |
| Uvicorn | 0.54.0 | BSD-3-Clause | Local ASGI server | APPROVED |
| httpx2 | 2.16.0 | BSD-3-Clause | Starlette/FastAPI TestClient | APPROVED |
| pytest | 9.2.0 | MIT | Tests | APPROVED |
| pytest-cov | 7.0.0 | MIT | Coverage gate | APPROVED |
| Ruff | 0.17.4 | MIT | Lint/format | APPROVED |
| mypy | 2.4.1 | MIT | Strict type check | APPROVED |
| pre-commit | 4.7.0 | MIT | Local hooks | APPROVED |

Python lock có 41 third-party distributions ngoài local package và pip; license metadata không có mục `UNKNOWN`. Chi tiết audit được lưu tại `reports/stage-c-license-audit.md`. `requirements.lock` là nguồn version đầy đủ.

### Frontend direct dependencies

| Package | Version | License từ npm registry/lock | Vai trò | Trạng thái |
|---|---:|---|---|---|
| React | 19.3.1 | MIT | UI runtime | APPROVED |
| React DOM | 19.3.1 | MIT | UI runtime | APPROVED |
| Vite | 8.3.7 | MIT | Build/dev server | APPROVED |
| TypeScript | 6.0.3 | Apache-2.0 | Type checking | APPROVED |
| `@vitejs/plugin-react` | 6.3.0 | MIT | React build integration | APPROVED |
| Vitest | 5.1.0 | MIT | Frontend tests | APPROVED |
| ESLint | 10.14.0 | MIT | Frontend lint | APPROVED |
| `@eslint/js` | 10.0.1 | MIT | ESLint rules | APPROVED |
| `typescript-eslint` | 8.72.1 | MIT | TypeScript lint | APPROVED |
| Prettier | 3.9.10 | MIT | Frontend format | APPROVED |
| `@types/react` | 19.3.0 | MIT | Type declarations | APPROVED |
| `@types/react-dom` | 19.3.0 | MIT | Type declarations | APPROVED |

Frontend lock chứa 161 package entries tại thời điểm audit cuối Stage C; 0 entry thiếu license metadata. License families gồm MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MPL-2.0 và BlueOak-1.0.0. Lock có thể chứa optional package metadata không được cài sau `npm prune`; release audit phải dựa trên cả lock và installed tree.

## 5. Candidate dependencies chưa cài/chưa phê duyệt

| Candidate | Vai trò | License cần xác minh khi pin | Trạng thái |
|---|---|---|---|
| DuckDB | Analytics/storage | Verify pinned artifact | PENDING |
| PyArrow | Parquet interchange nếu cần | Verify pinned artifact và bundled components | PENDING |
| PyTorch | Vision/sequence candidate | Verify pinned artifact + CUDA bundled notices | PENDING |
| LightGBM | Tabular candidate | Verify pinned artifact | PENDING |
| XGBoost | Tabular candidate | Verify pinned artifact | PENDING |
| OpenCV | Image processing | Verify pinned artifact + bundled codecs | PENDING |
| Tesseract OCR | OCR candidate | Verify installed distribution/language data | PENDING |
| Tailwind CSS | Styling candidate | Verify pinned package | PENDING |
| OWASP ZAP Community | Security self-test | Verify distribution terms | PENDING |

Không cài toàn bộ candidates mặc định. Chỉ cài package tối thiểu khi stage tương ứng cần và sau khi kiểm tra Python 3.14 compatibility; nếu không tương thích, chọn Python environment phù hợp miễn phí.

## 6. Không được phê duyệt mặc định

- Package không có license rõ ràng (`NOASSERTION`) hoặc license text thiếu.
- Package source không chính thức/typosquat.
- Package có điều khoản hạn chế commercial use nếu định hướng tương lai có thể thương mại hóa, trừ khi có ADR và phạm vi rõ.
- Package yêu cầu paid key/subscription/runtime service.
- Model weights/dataset không có quyền sử dụng rõ ràng.
- Chart/icon/font/assets tải ngẫu nhiên từ Internet.
- GPL/AGPL/server-side package được bundle hoặc network-deploy mà chưa review nghĩa vụ cụ thể.

Đây không phải tuyên bố rằng GPL/AGPL “xấu”; chỉ là trigger cần review nghĩa vụ trước khi chọn kiến trúc/phân phối.

## 7. Stage C actions bắt buộc

- [x] Tạo project environment riêng, không dựa vào global/user site-packages.
- [x] Chọn Python 3.14.2 sau compatibility spike Stage C.
- [x] Pin direct và transitive dependencies bằng `requirements.lock` và `package-lock.json`.
- [x] Lưu license report từ environment thực.
- [ ] Copy/retain notices cần thiết vào release artifacts — thực hiện tại Stage Z khi có artifact phân phối.
- [ ] Scan vulnerabilities chuyên sâu — thực hiện lại tại Stage X; Stage C đã kiểm tra dependency resolution/license metadata.
- [x] Cập nhật package thực dùng sang `APPROVED`.

## 8. Zero-cost conclusion

Không có dependency runtime trả phí nào được phê duyệt hoặc yêu cầu tại Stage B. Các candidate chỉ được chấp nhận nếu artifact/version cụ thể đáp ứng license, compatibility, security và 0 VNĐ.
