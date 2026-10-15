"""Write the current experiment's reproducibility and presentation guide."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent

def main():
 m=json.loads((R/'results/metrics.json').read_text(encoding='utf-8'));r=json.loads((R/'optimization/report.json').read_text(encoding='utf-8'));d=r['selection'];name=d['selected_config'];cfg=d['config']
 rows='\n'.join(f"| {x['model']} | {100*x['f1']:.1f}% | {100*x['f1_std']:.1f} | {100*x['ap']:.1f}% |" for x in m['summary'])
 old=r['summary'][0];new=r['summary'][1]
 text=f'''# Elliptic: phát hiện giao dịch Bitcoin đáng ngờ

Bản 2 cập nhật sau kiểm tra GCN. F1 illicit trung bình tăng từ {100*old['f1']:.1f}% lên {100*new['f1']:.1f}%. Code, checkpoint, demo, slide và tài liệu đã dùng cùng bộ kết quả mới.

## Mở kết quả hiện hành

- Demo: https://elliptic-transaction-lab.pinkwand512.chatgpt.site
- Báo cáo tối ưu và cách trả lời phản biện: https://elliptic-transaction-lab.pinkwand512.chatgpt.site/optimization.html
- `output/V2/Elliptic_Deep_Graph_26_Slides.pptx`: 26 slide có speaker notes.
- `output/V2/Elliptic_Loi_Thuyet_Trinh_Va_Demo.pdf`: lời nói theo slide và kịch bản demo.
- `output/V2/Elliptic_Tai_Lieu_Hoc_3_Ngay.pdf`: lộ trình học, bài tập, đáp án, phần phản biện đã cập nhật.
- `output/V2/Elliptic_Code_Demo_TaiLieu.zip`: code, mô hình, toàn bộ báo cáo, demo offline và tài liệu hiện hành.

Các file nằm trực tiếp trong `output/` là bản ban đầu. Dùng `output/V2/` khi thuyết trình. Site giữ quyền riêng tư như trước; trình chiếu bằng tài khoản có quyền hoặc dùng bản local.

## Những gì đã kiểm tra và thay đổi

1. Kiểm tra nhãn, split, cạnh, scaler và cách tính F1. Unknown là -1; không tham gia loss hoặc chỉ số có nhãn. Không có cạnh nối các tập.
2. Bản GCN đầu dừng ở 180 epoch, cả ba seed chọn epoch 179. Đối chứng tăng ngân sách và patience giữ nguyên kiến trúc, loss và đầu vào. 180 epoch đầu tái hiện AP validation đúng như baseline.
3. Thử thêm trọng số dương 7/3, cấu hình hidden 100/lr .001, chặn đặc trưng ở ±5, và QuantileTransformer fit trên mọi nút train. Chi tiết trong `optimization/protocol.json`, `audit.json` và các file run.
4. Đưa hai cấu hình có AP validation cao nhất ở seed 0 vào vòng xác nhận. Lặp ứng viên đầu ở seed 1 và 2; chốt theo AP validation trung bình. Dừng ứng viên còn lại nếu ngay cả AP=1 ở mọi seed thiếu cũng không thể vượt trung bình đã đạt (chi tiết trong selection.json và protocol.json). Cấu hình được chọn là `{name}`. MLP được huấn luyện lại bằng đúng thiết lập này, với A=I.
5. Lưu `optimization/selection.json` trước bước đánh giá test mới. Chỉ sau đó mới tạo test predictions, kiểm tra lại chỉ số và đồng bộ demo.

**Giới hạn:** tập test từng được xem ở bản đầu. Đây là đánh giá hồi cứu trên test cũ, chưa phải xác nhận trên một holdout mới. Không dùng test để chọn cấu hình, checkpoint hay ngưỡng trong lượt tối ưu. Giai đoạn validation chỉ có năm snapshot; một lần chia thời gian và ba seed chưa chứng minh khả năng tổng quát cho mọi giai đoạn.

## Kết quả hiện hành

| Mô hình | F1 illicit trung bình | SD (điểm phần trăm) | AP trung bình |
|---|---:|---:|---:|
{rows}

RF giữ nguyên kết quả. MLP trong bảng là đối chứng mới có cùng thiết lập với GCN, không phải baseline MLP 180 epoch và cũng chưa phải MLP được tối ưu riêng. Bản gốc của cả 12 run được giữ tại `optimization/baseline/results/`. SD qua seed không phải khoảng tin cậy.

RF all dùng 93 đặc trưng local và 72 đặc trưng tổng hợp hàng xóm có sẵn. GCN và MLP dùng 93 cột local. Vì thế RF all đã có một dạng thông tin graph; không gọi nó là đối chứng hoàn toàn không có thông tin quan hệ.

## Chạy demo offline

Chỉ cần Python 3 để phục vụ file tĩnh; không cần Torch để mở demo.

```powershell
python -m http.server 8767 --bind 127.0.0.1 --directory site/dist
```

Mở http://127.0.0.1:8767. Dừng bằng Ctrl+C, hoặc dùng `start_demo.ps1`. Không mở HTML bằng nhấp đôi vì fetch qua file:// có thể bị chặn.

## Huấn luyện và tái tạo bản 2

Dùng Python 3.11+ và các package trong `requirements.txt`. Môi trường thực nghiệm dùng Torch CPU; phiên bản đã ghi trong `requirements-lock.txt`. Archive không chứa CSV gốc hoặc prepared.npz; `prepare_data.py` tải lại từ nguồn công khai.

```powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe prepare_data.py
.\\.venv\\Scripts\\python.exe optimize_gcn.py --configs long moderate_weight paper_inspired clipped quantile --seeds 0
.\\.venv\\Scripts\\python.exe finalize_experiment.py
.\\.venv\\Scripts\\python.exe promote_optimized.py
.\\.venv\\Scripts\\python.exe export_demo.py
.\\.venv\\Scripts\\python.exe verify_results.py
node verify_inference.mjs
```

Các lệnh tối ưu dùng lại run đã có. Muốn huấn luyện thật từ đầu, dùng `--force` với `optimize_gcn.py` trên một bản sao thư mục; giữ lại thí nghiệm đã công bố. `finalize_experiment.py` cố ý từ chối đổi một lựa chọn đã đóng băng nếu các checkpoint/tiêu chí không còn khớp. Tạo thư mục thí nghiệm mới khi đổi giao thức.

Huấn luyện lại riêng cấu hình hiện hành:

```powershell
python optimize_gcn.py --configs {name} --seeds 0 1 2
python optimize_gcn.py --configs {name} --seeds 0 1 2 --mlp
```

`train.py` vẫn giữ triển khai baseline để kiểm chứng lịch sử; không chạy `train.py --force` vào bộ kết quả V2 đang dùng vì lệnh đó ghi kết quả baseline lên `results/`. Các hàm tính chỉ số và tạo adjacency trong file này được quy trình mới dùng lại.

## Giao thức chính xác

- Train: timestep 1-29. Validation: 30-34. Test: 35-49; 16.670 nút có nhãn, 50.834 unknown.
- Không đưa ID, timestep hoặc nhãn vào feature. StandardScaler chỉ fit trên mọi nút train.
- GCN dùng cạnh nhị phân đối xứng, self-loop và D^-1/2 A D^-1/2. Giao diện giữ mũi tên gốc.
- Cấu hình neural cuối: `{json.dumps(cfg)}`. Chặn giá trị hoặc biến đổi theo phân vị (nếu có) sau scaler và trước phép tổng hợp. QuantileTransformer học từ train; feature nhị phân cung cấp cho web đã qua phép biến đổi này. RF không dùng bước chặn.
- Chọn checkpoint bằng AP validation, ngưỡng tối đa hóa F1 validation theo từng seed. Làm tròn điểm sáu chữ số trước chọn ngưỡng và báo cáo.
- RF: 200 cây, min_samples_leaf=2, max_features=sqrt, class_weight=balanced_subsample.
- MLP có cùng lớp, số tham số, nhánh skip, loss và preprocessing với GCN nhưng bỏ tổng hợp hàng xóm.
- Đây là phân loại snapshot lịch sử, có thể chứa giao dịch xuất hiện sau nút đang xét trong cùng snapshot. Chưa kiểm chứng cho cảnh báo trước khi giao dịch mới xuất hiện.

## Demo và kiểm chứng

GCN/MLP seed 0 tính trực tiếp trong JavaScript trên toàn snapshot từ feature đã xử lý bằng phép biến đổi học trên train. Bước chặn, nếu được chọn, được thực hiện thêm trong JavaScript. RF dùng điểm tính trước bằng Python. Graph hiển thị tối đa 50 nút để dễ đọc; cắt hình không cắt graph suy luận. Thanh ngưỡng chỉ minh họa đánh đổi, không thay bảng kết quả đã báo cáo. Các case chọn sau đánh giá và có cả đúng, sai, bỏ sót, bất đồng, unknown.

- `optimization/report.json`: kết quả mọi đối chứng đã đánh giá, so sánh cũ/mới, xác minh chỉ số.
- `optimization/selection.json`: tiêu chí, finalist, điểm validation trung bình, thời điểm chốt và hash checkpoint GCN.
- `optimization/by_timestep.json`: kết quả từng snapshot test.
- `qa/metrics-integrity.json`: tính lại chỉ số từ các điểm dự đoán.
- `qa/inference-parity.json`: đối chiếu toàn bộ 135.008 đầu ra neural và quyết định ở ngưỡng mặc định giữa web/Python.
- `qa/browser-report.json`: kiểm tra tình huống, nhãn, số đếm ngưỡng, chuyển mô hình/snapshot, màn hình nhỏ và các file tải.

`materials_v2.py`, `build_documents.py`, `build_optimization_page.py` tạo nội dung cập nhật. PPTX dùng `presentation/.build/build.mjs` và `finalize.mjs` với bundled @oai/artifact-tool. PDF dùng reportlab và Arial. Template nội dung ban đầu ở `materials.py`; dùng `materials_v2.py` cho kết quả hiện hành. Các file output gốc là bản trình bày cũ.

## Nguồn

- Elliptic dataset: https://www.kaggle.com/datasets/ellipticco/elliptic-data-set
- Weber et al. (2019): https://arxiv.org/abs/1908.02591
- GCN: https://arxiv.org/abs/1609.02907

Bài báo gốc cũng cho thấy RF mạnh hơn GCN; những số trong bài báo không phải kết quả do nhóm chạy. Nhóm dùng validation riêng và loại timestep khỏi feature, nên không tuyên bố tái lập nguyên vẹn giao thức của bài báo.
'''
 (R/'README.md').write_text(text,encoding='utf-8');print('Updated README.md for revision 2')

if __name__=='__main__':main()
