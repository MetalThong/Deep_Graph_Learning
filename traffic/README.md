# Traffic Graph Lab

Đề tài: dự báo tốc độ giao thông METR-LA trước 15 phút bằng GCN + GRU.
Nhóm 4 người, 26 slide, 37 phút trình bày và 3 phút hỏi đáp.

## Mở demo trong một phút

Trên Windows có Python, nhấp đúp `RUN_DEMO.cmd`; hoặc chạy `python run_demo.py`.
Launcher tự mở trình duyệt, chỉ lắng nghe trên máy này. Giữ terminal mở trong khi demo.

Từ thư mục `traffic`, chạy:

```powershell
python -m http.server 8766 --bind 127.0.0.1 --directory dist
```

Mở http://127.0.0.1:8766. Không mở trực tiếp `index.html` bằng file:// vì trình duyệt chặn fetch dữ liệu.
Demo không cần thư viện JavaScript, API key, dịch vụ AI hay Internet sau khi có đủ thư mục dist.
Python chỉ dùng làm máy chủ file. Các phép tính GCN và GRU chạy thật trong trình duyệt.

**Demo v2 đã triển khai ngày 14/10/2026:** https://traffic-graph-lab-v2.fitdace1.chatgpt.site
Website mới nằm trong tài khoản hiện tại, giữ chế độ riêng tư; đăng nhập đúng tài khoản này để xem.
Người dùng đã đổi tài khoản nên website cũ không được cập nhật. Chỉ dùng URL v2 ở trên.
Mã nguồn dành riêng cho website mới nằm ở `../traffic-site-v2/`; thư mục này chứa manifest
và Git repository của site mới. Manifest trong thư mục `traffic` vẫn thuộc site cũ.
Biên nhận triển khai: `results/deployment-v2.json`. Bản local dùng cùng 12 file trong `dist`.

Trên máy đã thực hiện thí nghiệm này, có thể dùng Python sẵn có:

```powershell
& '..\demo\.venv\Scripts\python.exe' -m http.server 8766 --bind 127.0.0.1 --directory dist
```

## Kịch bản demo 5 phút

1. Chọn **Phục hồi tốc độ** (717458, 06/06/2012 18:35). Hiện tại 14,5 km/h.
2. Đọc dự báo trước khi mở đáp án: GRU 20,9; GCN + GRU 21,3 km/h. Mở đáp án: thực tế 24,7 km/h.
3. Chọn **Tình huống khó** (717573, 15/06/2012 14:50). GCN + GRU dự báo 97,8, thực tế 42,8 km/h. Hàng xóm đã có tín hiệu giảm trước đó; mô hình chưa khai thác đủ tốt.
4. Chọn **Dữ liệu quá cũ** (774067, 09/06/2012 13:45). Lần đo thật cuối lúc 04:00, cách **9 giờ 45 phút**. 12/12 mốc của cảm biến thiếu. GCN + GRU dự báo 108,7, thực tế +15 phút 5,6 km/h.
5. Quay về tình huống phục hồi. Mở kiểm tra độ nhạy, bật **Chỉ giữ thông tin của chính cảm biến**. Đây là thay A bằng I với trọng số cố định, không mô phỏng đóng đường.
6. Xem bảng thực nghiệm toàn test. Nếu còn thời gian, đổi cảm biến/thời điểm, thử phát và dừng.

Ba tình huống đã cố định từ phân tích v1, trước huấn luyện v2. Không tìm ví dụ mới có lợi hơn sau khi có kết quả.
Cảnh báo hiển thị tuổi dữ liệu từ toàn bộ lịch sử, số quan sát thiếu và tình trạng hàng xóm. Ngưỡng 60 phút là quy tắc minh họa, chưa phải ngưỡng vận hành đã được kiểm chứng. Nó **không thay đổi mô hình, không loại mẫu test và không phải độ tin cậy dự báo**.

## Kết quả đã chạy

| Phương pháp | MAE km/h | RMSE km/h | MAE khi thực tế +15 phút <30 km/h |
|---|---:|---:|---:|
| Giữ nguyên | 5,629 | 10,324 | 11,084 |
| GRU | 4,875 ± 0,002 | 9,613 | 12,284 |
| GCN + GRU | 4,844 ± 0,009 | 9,449 | 12,217 |

Bản **v2_160epochs_fullval**: graph giảm MAE 0,64% so với GRU trong cấu hình này.
± là SD mẫu của ba seed trên cùng test, không phải khoảng tin cậy. Đọc cả sai số tốc độ thấp và ngoại lệ trong `output/Phan_Tich_Ket_Qua_Va_Ngoai_Le_v2.pdf`.

**Phạm vi:** v2 là vòng cải tiến sau khi đã xem test của v1, chưa phải một benchmark mới với test chưa từng được kiểm tra. Checkpoint và seed vẫn chọn bằng validation. Cần giai đoạn dữ liệu mới để xác nhận.

So sánh v1–v2 trong `results/audit_v2/diagnostics.json` dùng đúng cùng 1,246,840 mục tiêu. Bản lưu v1 ở `history/v1_35epochs/` trên máy gốc. Budget, scheduler, validation stride và ranh giới đều thay đổi cùng lúc; không gán toàn bộ cải thiện cho riêng số epoch.

| Lần chạy | Epoch đã chạy | Epoch chọn | Lý do dừng | MAE validation |
|---|---:|---:|---|---:|
| GRU / 42 | 160 | 157 | epoch_budget | 4,453 |
| GRU / 43 | 160 | 140 | patience | 4,454 |
| GRU / 44 | 160 | 156 | epoch_budget | 4,456 |
| GCN + GRU / 42 | 160 | 160 | epoch_budget | 4,422 |
| GCN + GRU / 43 | 160 | 159 | epoch_budget | 4,417 |
| GCN + GRU / 44 | 160 | 153 | epoch_budget | 4,431 |

## Tái lập huấn luyện

Python 3.11+ được khuyến nghị; lần chạy đã thực hiện với Python 3.13, PyTorch CPU 2.14.1.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe prepare_data.py
.venv\Scripts\python.exe train.py
.venv\Scripts\python.exe export_demo.py
.venv\Scripts\python.exe test_pipeline.py
node test_inference.mjs
node test_freshness.mjs
.venv\Scripts\python.exe audit_results.py
```

`prepare_data.py` tải khoảng 57 MB h5 và các file graph từ nguồn tác giả nếu chưa có.
Raw dataset và cache chuẩn bị không nằm trong gói ZIP gọn; downloader tạo lại chúng.
Checkpoint của 6 lần chạy đã nằm trong `results/`, nên không bắt buộc huấn luyện lại để demo.
Không thay checkpoint chọn bằng validation bằng checkpoint có test tốt nhất.

Nếu đã có checkpoint và chỉ muốn chấm/xuất lại: chạy `train.py --evaluate-only`, rồi `export_demo.py` và `audit_results.py`. Khi không có bản lưu v1, script audit chỉ tính chẩn đoán v2; bảng so sánh v1 đã công bố trong gói là kết quả lưu từ máy gốc.

## Quy trình thực nghiệm chính xác

- 207 cảm biến, 34.272 mốc, cách nhau 5 phút; 01/03–27/06/2012, Los Angeles.
- Dữ liệu gốc mph; báo cáo và giao diện đổi sang km/h bằng 1,609344.
- 0 hoặc không hữu hạn coi là thiếu theo quy ước benchmark. Forward fill chỉ dùng quá khứ; khi chưa từng có quan sát, fallback trung vị mỗi nút chỉ từ train. Không backward fill.
- Scaler trung bình và độ lệch chuẩn toàn cục chỉ từ train hợp lệ. Input có mask. Tuổi dữ liệu được lưu riêng cho cảnh báo, **chưa đưa vào mạng neural**.
- Đầu vào t−11..t (12 mốc, hai đầu cách 55 phút), dự báo trực tiếp t+3.
- Chia theo timestamp mục tiêu: train 23.976; validation 3.425; test 6.853 cửa sổ.
- Mục tiêu train kết thúc 23/05/2012 07:05. Validation 23/05 07:20–04/06 04:40. Test 04/06 04:55–27/06 23:55.
- Bỏ hai timestamp mục tiêu ở đầu validation và test, để origin đầu mỗi tập không sớm hơn nhãn cuối tập trước. Lịch sử đi qua ranh giới được phép vì đã quan sát trước lúc dự báo. Rolling evaluation dùng quan sát test đã xảy ra làm lịch sử cho dự báo sau.
- Graph gốc có hướng, 1.515 cạnh ngoài đường chéo. Lấy max(A,A.T) còn 1.313 cặp không hướng, thêm self-loop, chuẩn hóa đối xứng D^-1/2 A D^-1/2.
- Lớp không gian: ReLU(Linear(concat(x, A_norm x))), x gồm tốc độ và mask, đầu ra 8 chiều. Ghép sin/cos giờ và thứ; GRU hidden=16; đầu ra delta cộng tốc độ cuối. Tổng 1.497 tham số.
- GRU đối chứng dùng cùng kiến trúc nhưng A_norm=I, được huấn luyện riêng từ đầu. Cùng số tham số và ngân sách.
- Adam lr=0,003, weight decay=1e-5, gradient clip=5, masked MAE chuẩn hóa, batch512. Mỗi epoch lấy 32.768 cặp với hoàn lại, không phải duyệt toàn train.
- Tối đa160 epoch, early stopping patience20 (cải thiện >1e-5 km/h). ReduceLROnPlateau factor0,5, patience6 (giảm sau7 lượt xấu), ngưỡng cải thiện tuyệt đối1e-4 km/h, min_lr1e-5.
- Validation và test chấm mọi origin. Test có 1,246,840 mục tiêu hợp lệ, 35,523 mục tiêu dưới30 km/h.
- Seeds42/43/44, CPU2threads mỗi tiến trình. Demo chọn GRU seed42, GCN + GRU seed43 bằng validation, không chọn theo test.
- Đã xem test v1 trước vòng cải tiến v2. Không tuyên bố test v2 là độc lập với quá trình phát triển.

## Các file cần đọc

| File | Vai trò |
|---|---|
| prepare_data.py | Tải nguồn, kiểm tra thứ tự sensor, chuẩn bị graph, split, imputation và scaler |
| train.py | ForecastNet, lấy batch, huấn luyện, chọn checkpoint, đánh giá |
| export_demo.py | Xuất trọng số, test replay, ví dụ và dữ liệu đối chiếu |
| dist/inference.mjs | Phép tính GCN + GRU tương thích PyTorch bằng JavaScript |
| dist/app.mjs | Chọn cảm biến, thời gian, mở đáp án và kiểm tra độ nhạy |
| results/data_manifest.json | Số lượng, ngày, quy tắc chuẩn bị và SHA256 nguồn |
| results/metrics.json | Số liệu thực nghiệm và lịch sử học |
| test_pipeline.py | Ranh giới thời gian, scaler, forward fill, masking, graph |
| dist/freshness.mjs / test_freshness.mjs | Tuổi dữ liệu, cảnh báo, kiểm tra ranh giới ngày và trạng thái thiếu |
| test_inference.mjs | So sánh 3.105 đầu ra JavaScript và PyTorch, kể cả A=I |

## Những điều cần nói chính xác

- Đây là **phát lại dữ liệu lịch sử**, chưa tích hợp nguồn giao thông trực tiếp.
- Nét nối trên giao diện là cạnh graph giữa tọa độ cảm biến, không phải bản đồ tuyến đường.
- Mô hình dự báo tốc độ trung bình tại cảm biến, không nhận dạng xe bằng camera.
- Kiến trúc gọn lấy cảm hứng từ GCN và T-GCN, **không phải tái lập đầy đủ T-GCN/DCRNN**.
- Bỏ hàng xóm với trọng số cố định là thử độ nhạy, không phải can thiệp giao thông có quan hệ nhân quả.
- Chưa có bằng chứng hiệu quả ở Việt Nam hoặc đáp ứng vận hành điều hành giao thông.
- Không quy đổi MAE thành phần trăm “độ chính xác”.

## Nguồn

- Dữ liệu, graph, tọa độ và quy ước benchmark: https://github.com/liyaguang/DCRNN
- DCRNN: https://arxiv.org/abs/1707.01926
- T-GCN: https://arxiv.org/abs/1811.05320
- GCN: https://arxiv.org/abs/1609.02907
- GRU: https://arxiv.org/abs/1406.1078

Mã pipeline và ứng dụng của nhóm được viết cho bài này. File LICENSE của kho DCRNN được giữ trong data.
Các hình bìa mang tính minh họa khái niệm; graph, biểu đồ và số liệu thực nghiệm sử dụng dữ liệu thật.
