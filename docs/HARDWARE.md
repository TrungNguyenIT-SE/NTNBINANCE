# HARDWARE INVENTORY VÀ RESOURCE BUDGET

> Document ID: `HW-BFS-001`  
> Version: `1.0`  
> Status: `BASELINE LOCKED`  
> Captured: `09/11/2026 22:41–22:43, Asia/Saigon`  
> Machine: `TRNGUYNNLAPTOP`  
> Scope: Máy local dùng cho development, training, inference và private beta

## 1. Mục đích

Tài liệu ghi cấu hình thật của máy, benchmark baseline và resource budget bắt buộc cho MVP 0 VNĐ. Các con số không phải quảng cáo hiệu năng và không được suy rộng sang model chưa được benchmark.

## 2. Cấu hình hệ thống ghi nhận

| Thành phần | Giá trị |
|---|---|
| Máy | `TRNGUYNNLAPTOP` |
| Hệ điều hành | Microsoft Windows 11 Home Single Language, 64-bit |
| OS version/build | `10.0.26200`, build `26200` |
| PowerShell | `5.1.26100.9711` |
| CPU | 12th Gen Intel Core i5-12450HX |
| CPU topology | 8 cores / 12 logical processors |
| WMI max clock | 2400 MHz; turbo thực tế do hệ thống điện/nhiệt quản lý |
| RAM vật lý | 15,78 GiB |
| RAM trống trước benchmark | 4,80 GiB |
| RAM trống sau benchmark | 5,01 GiB |
| GPU | NVIDIA GeForce RTX 3050 6GB Laptop GPU |
| VRAM theo `nvidia-smi` | 6144 MiB |
| Compute capability | 8.6 |
| NVIDIA driver | 591.44 |
| Workspace volume | `D:` / NTFS / Healthy |
| `D:` capacity | 250,00 GiB |
| `D:` free lúc đo | 161,41 GiB |
| Physical disk chứa `D:` | Micron MTFDKCD512QFM-1BD1AABLA, NVMe SSD, Healthy |
| Physical disk khác | KIOXIA-EXCERIA G2, NVMe SSD, Healthy |

### Ghi chú về GPU

WMI báo AdapterRAM không chính xác do giới hạn/biểu diễn thuộc tính; `nvidia-smi` nhận đúng 6144 MiB. Resource budget dùng số từ `nvidia-smi`. Chưa có PyTorch trong môi trường tại thời điểm Stage B nên **chưa benchmark inference GPU**; không được suy diễn GPU latency từ tên card.

## 3. Công cụ có sẵn

| Công cụ | Version/trạng thái | Vai trò | Bắt buộc cho MVP? |
|---|---|---|---:|
| Python | 3.14.2 | Backend, data, ML | Có, nhưng Stage C phải kiểm tra compatibility và có thể tạo env bằng version phù hợp đã có/cài miễn phí |
| NumPy | 2.4.2 | Numeric compute | Candidate/đã có |
| scikit-learn | 1.9.0 | Baseline/inference | Candidate/đã có |
| pandas | 3.0.3 | Data inspection | Candidate/đã có |
| Pillow | 12.1.1 | Image decode/re-encode | Candidate/đã có |
| Git | 2.52.0.windows.1 | Version control | Có |
| Node.js | 24.13.0 | Frontend toolchain nếu chọn React/Vite | Chưa bắt buộc đến khi Stage C chốt frontend |
| npm | 11.6.2 | Frontend packages | Chưa bắt buộc |
| Docker CLI/Desktop | 29.6.2 | Container tùy chọn | Không; không dùng làm đường chạy chuẩn |
| `nvidia-smi` | Có | GPU inventory/monitoring | Tùy chọn |
| Tesseract | Chưa có | OCR candidate | Không ở Stage B; chỉ cài miễn phí nếu Stage M chọn |
| PyTorch | Chưa có | Vision/GPU candidate | Không ở Stage B |
| LightGBM/XGBoost | Chưa có | Tabular candidates | Không ở Stage B |
| DuckDB/FastAPI/OpenCV | Chưa có | Data/API/image candidates | Không ở Stage B |

Python 3.14 là phiên bản rất mới. Stage C không được cài hàng loạt dependency trước khi xác minh wheel compatibility. Nếu một dependency quan trọng chưa hỗ trợ, dùng một Python version phù hợp được cài local miễn phí và khóa trong tài liệu; không build toolchain phức tạp hoặc thuê môi trường cloud chỉ để né compatibility.

## 4. Phương pháp benchmark

### 4.1. Disk

- Tạo file tạm 256 MiB trực tiếp tại `D:\BINANCE` bằng .NET `FileStream` để đo đúng volume workspace `D:`.
- Chunk 4 MiB, sequential read/write, flush dữ liệu.
- `DeleteOnClose`; xác nhận file tạm đã xóa sau khi đóng stream.
- Đây là micro-benchmark tuần tự, có ảnh hưởng cache/OS; không đại diện random I/O hoặc workload DuckDB đầy đủ.

### 4.2. CPU

- NumPy float32 matrix multiplication `1024 × 1024`.
- Warm-up một lần, đo 5 lần, báo median.
- GFLOPS là ước lượng phép toán, không phải benchmark chuẩn hóa toàn hệ thống.

### 4.3. RAM

- Copy NumPy float32 array 128 MiB trong memory.
- Báo throughput quan sát một lần; chỉ dùng làm sanity check.

### 4.4. Inference mẫu

- scikit-learn Logistic Regression đã gán coefficients cho 3 classes, 64 numeric features.
- Warm-up 20 lần.
- Batch 1: 5.000 calls; batch 32: 2.000 calls; batch 1.000: 200 calls.
- Chỉ chứng minh baseline numeric nhẹ chạy tốt; không đại diện OCR, vision hoặc full request latency.

## 5. Kết quả benchmark baseline

### 5.1. Disk/RAM/CPU

| Benchmark | Kết quả |
|---|---:|
| Sequential write 256 MiB | 839,1 MiB/s |
| Sequential read 256 MiB | 2.684,7 MiB/s |
| Temp benchmark cleanup | Pass |
| RAM copy 128 MiB | 2.856,1 MiB/s |
| NumPy matmul 1024 float32, median 5 runs | 0,008011 s |
| Matmul estimated throughput | 268,08 GFLOPS |

### 5.2. Numeric inference mẫu

| Batch | Calls | Mean/call | Samples/s |
|---:|---:|---:|---:|
| 1 | 5.000 | 0,114478 ms | 8.735,3 |
| 32 | 2.000 | 0,140571 ms | 227.643,3 |
| 1.000 | 200 | 0,479537 ms | 2.085.344,8 |

Benchmark environment: Python 3.14.2, NumPy 2.4.2, scikit-learn 1.9.0.

## 6. Diễn giải

### Đã chứng minh

- CPU/disk đủ cho spike ingestion, DuckDB/Parquet, baseline scikit-learn và web app local.
- Numeric inference không phải bottleneck ở quy mô một user local.
- 161 GiB free cho phép dành quota 60 GiB cho project mà vẫn giữ safety margin đáng kể.

### Chưa chứng minh

- Full image validation/OCR latency.
- PyTorch CPU/GPU vision inference.
- Training hybrid model lớn.
- Concurrent multi-user performance.
- 24/7 stability, thermal throttling và battery-mode performance.
- Random I/O/large DuckDB query dưới dataset thật.

Các hạng mục chưa chứng minh phải benchmark lại tại Stage M/O/T. Không dùng kết quả Logistic Regression để tuyên bố full prediction đạt 5 giây.

## 7. Resource budget bắt buộc

### 7.1. Disk budget

Project quota tổng trên `D:`: **60 GiB**.

| Nhóm | Soft allocation |
|---|---:|
| Raw + clean + feature data | 25 GiB |
| Upload/golden images | 5 GiB |
| Model/checkpoint/artifact | 10 GiB |
| Reports/logs/databases | 5 GiB |
| Cache/temp/headroom nội bộ | 15 GiB |
| **Tổng** | **60 GiB** |

Threshold theo project quota:

- 42 GiB (70%): warning; chạy cleanup/retention review.
- 51 GiB (85%): không bắt đầu training/backfill lớn mới.
- 57 GiB (95%): dừng write job không thiết yếu; chỉ cho cleanup/backup/recovery.
- Bất kể project usage: nếu volume `D:` còn < 40 GiB thì dừng ingestion/training write và cảnh báo Critical.

Không tự động xóa raw/model quan trọng. Cleanup phải theo retention manifest; upload tạm/log/cache có thứ tự ưu tiên xóa rõ ràng.

### 7.2. RAM budget

Do RAM trống đo được chỉ khoảng 5 GiB khi máy đang sử dụng:

- Local runtime bình thường (API + UI + one worker + DB): target working set ≤ 2,5 GiB.
- Một inference worker; không nhân worker theo 12 logical processors.
- Không nhận job mới nếu available RAM < 2 GiB.
- Training chạy tuần tự khi đóng ứng dụng nặng khác; target project RAM ≤ 8 GiB.
- Training hard guard: project process tree ≤ 10 GiB; vượt ngưỡng thì checkpoint/cancel an toàn.
- Không dùng dataset copy toàn bộ vào RAM nếu streaming/memmap/Parquet scan được.

### 7.3. CPU budget

- Interactive runtime: tối đa 4 compute threads; giữ UI/OS responsive.
- Background ingestion: tối đa 2 workers.
- Training: tối đa 8 logical threads mặc định; 10 chỉ sau thermal/stability test.
- Không chạy training và bulk backfill đồng thời.
- Nếu CPU duy trì cao làm UI p95 > SLO hoặc máy thermal throttle, giảm threads/batch.

### 7.4. GPU budget

- GPU là tùy chọn; pipeline phải có CPU fallback cho model được chọn hoặc fail rõ ràng.
- Target allocated VRAM ≤ 4,5 GiB.
- Hard guard ≤ 5,2 GiB để giữ headroom cho display/driver.
- Mixed precision/gradient accumulation/checkpointing chỉ dùng sau correctness test.
- OOM: giảm batch/image/model; không thuê GPU.

### 7.5. Time/latency budget

- Numeric experiment đơn: target ≤ 2 giờ.
- Vision/hybrid experiment đơn: target ≤ 6 giờ; hard time box 10 giờ.
- Không chạy hyperparameter search không giới hạn; dùng coarse/manual hoặc bounded trials.
- Full request p95 target ≤ 5 giây; nếu không đạt, công bố SLO thực đo tối đa đề xuất 15 giây hoặc giảm model.
- Prediction timeout ban đầu không được dùng để che job treo; giá trị chi tiết khóa tại Stage R/T.

## 8. Minimum viable hardware gate

Máy hiện tại được coi là pass spike nếu:

| Điều kiện | Mức tối thiểu | Đo được | Kết quả |
|---|---:|---:|---|
| Logical processors | 4 | 12 | Pass |
| RAM vật lý | 8 GiB | 15,78 GiB | Pass |
| Free workspace disk | 40 GiB | 161,41 GiB | Pass |
| Sequential read | 100 MiB/s | 2.684,7 MiB/s | Pass |
| Sequential write | 75 MiB/s | 839,1 MiB/s | Pass |
| Numeric batch-1 inference | < 10 ms/call | 0,114478 ms/call | Pass |
| GPU | Không bắt buộc | RTX 3050 6 GiB | Bonus, chưa benchmark model |

## 9. Re-benchmark triggers

Chạy lại inventory/benchmark khi:

- Thay máy, ổ đĩa, RAM, GPU hoặc OS lớn.
- Thay Python/runtime chính.
- Chốt image/OCR model ở Stage M.
- Chốt champion model ở Stage O.
- Latency tăng > 25% so với baseline tương đương.
- Free disk/RAM thay đổi đáng kể hoặc phát hiện thermal throttling.

Kết quả mới phải append/report version mới, không xóa baseline này.

## 10. Kết luận Gate B về hardware

**PASS cho spike/MVP local** với điều kiện tuân thủ quota và concurrency ở mục 7.

Máy đủ cho baseline numeric và pipeline local. Vision/hybrid chỉ được kết luận sau benchmark thực tế; nếu không đạt resource budget thì fallback là numeric champion + image quality/context validation, không phát sinh chi phí thuê compute.
