# Deep Graph Learning: từ biểu diễn quan hệ đến GCN, GraphSAGE và GAT

Đề xuất thuyết trình cho nhóm 4 người, môn **Phát triển hệ thống thông minh**, giảng viên **Trần Đình Quế**. Thời lượng mục tiêu: **37 phút nội dung + khoảng 5 phút hỏi đáp**; có thể rút còn 30 phút hoặc mở rộng tới 45 phút.

Ở đây, “Deep Graph” được hiểu là **Deep Learning on Graphs / Graph Neural Networks**. Đây là đề xuất phạm vi chuyên đề, không phải khẳng định thầy đã yêu cầu chính xác danh mục này.

## 1. Vì sao đề tài này phù hợp với những gì đã học?

Đã đối chiếu các tài liệu trong `D:\School\PT HTTM`: Slide1, Assignment1, Assignment2, Slide3, Assignment3, Slide4, Assignment4, Slide5, Assignment5. Thư mục Chương2 không có Slide2, nên nội dung chương đó được đối chiếu qua Assignment2. Hai sách trong Base là tài liệu tham khảo, không được coi là bằng chứng nhóm đã học hết sách.

| Kiến thức đã có | Bước tiếp theo khi học Deep Graph | Vị trí đối chiếu (trang PDF, tính từ 1) |
|---|---|---|
| Hệ thống thông minh gồm dữ liệu, biểu diễn, học, đánh giá, ứng dụng | Xây một hệ thống có input X/A, GNN, dự đoán và giao diện | Chương1/Slide1.pdf: 23, 25, 34, 36, 60 |
| Biểu diễn số, tiền xử lý, train/validation/test, triển khai | Biểu diễn X, A/edge_index; mask nhãn; protocol transductive | Chương2/Assignment2.pdf: 2, 7–10, 13–14 |
| MLP, ReLU, loss, backpropagation, optimizer, learned representation | Giữ quy trình học nhưng đưa quan hệ hàng xóm vào từng lớp | Chương3/Slide3.pdf: 4–24, 30, 34–36 |
| CNN, locality, weight sharing; kiến trúc phải phù hợp dữ liệu | Từ lưới đều sang lân cận đồ thị có số hàng xóm khác nhau | Chương4/Slide4.pdf: 3–6, 8, 28, 33 |
| Knowledge Graph, embeddings, retrieval, RAG | Phân biệt biểu diễn tri thức, học trên đồ thị và truy xuất bằng đồ thị | Chương5/Slide5.pdf: 4, 10–14, 36, 46–47, 51 |

Điểm nối nên nói rõ: **dữ liệu đổi cấu trúc → cách biểu diễn thay đổi → phép xử lý trong mô hình phải thay đổi**. Một mô hình dự đoán tốt chưa phải toàn bộ hệ thống; phải có quy trình dùng mô hình và bằng chứng đánh giá.

## 2. Câu hỏi trung tâm và phạm vi

> Khi dự đoán chủ đề một bài báo, thông tin về các bài báo có liên hệ với nó có giúp ích ngoài đặc trưng nội dung không?

Bài toán chính: **node classification** trên Cora. Node là bài báo, edge là quan hệ trích dẫn được đối xứng hóa, feature là vector từ xuất hiện/không xuất hiện. Mô hình dự đoán một trong 7 nhóm chủ đề.

Lý do chọn: dữ liệu nhỏ, chạy CPU, có nhãn, có baseline rõ ràng, dễ minh họa message passing và dễ triển khai. Nhược điểm: Cora cũ và nhỏ, có tính homophily; file dùng ở đây không có tiêu đề và abstract đọc được. Không trình bày demo này như hệ thống phân loại mọi bài báo mới trên Internet.

Các hướng khác nếu sau này muốn đổi ứng dụng:

- **Gợi ý phim bằng graph user–item:** đầu ra gần sản phẩm hơn, nhưng phải giải thích negative sampling, chia dữ liệu tương tác, Recall@K/NDCG@K và tránh leakage.
- **Graph classification cho phân tử:** minh họa rõ một graph là một mẫu và cần pooling/readout, nhưng phải bổ sung ý nghĩa dữ liệu hóa học.
- **Knowledge Graph completion:** dự đoán quan hệ thiếu; phù hợp nối chương 5, nhưng cần typed relations và mô hình/đánh giá khác node classification.

Với 30–45 phút, nên chọn **một bài toán thực nghiệm chính**. Các hướng còn lại chỉ dùng để giới thiệu độ rộng của lĩnh vực.

## 3. Phân công nhóm và mạch chuyển tiếp

| Người | Nội dung trình bày | Thời gian | Phần việc kỹ thuật |
|---|---|---:|---|
| 1 | Bối cảnh, động lực, biểu diễn graph, các bài toán, khác biệt với KG/GraphRAG | 8 phút | Dataset, EDA, sơ đồ X/A/y, nguồn tham khảo |
| 2 | Message passing, GCN, công thức, ví dụ số, học và backpropagation | 10 phút | `train.py`, kiểm tra gradient, giải thích shape |
| 3 | GraphSAGE/GAT, thiết kế thực nghiệm, baseline, nhiều split/seed và độ sâu | 10 phút | `research.py`, chạy thí nghiệm, phân tích bảng kết quả |
| 4 | Demo tương tác, triển khai, lỗi/giới hạn, liên hệ chương 5 | 9 phút | `dist/`, kiểm thử giao diện, deploy, kịch bản demo |

Chuyển tiếp gợi ý:

1. “Ta đã biết dữ liệu gồm cả đặc trưng và quan hệ. Vậy một lớp mạng phải nhận thông tin đó như thế nào?”
2. “GCN cho ta cách học cụ thể. Khi graph lớn hơn hoặc hàng xóm có mức độ quan trọng khác nhau, ta cần thay đổi gì?”
3. “Bây giờ kiểm tra những ý tưởng này bằng cùng một quy trình thực nghiệm, rồi đưa mô hình vào ứng dụng.”

Mỗi người cần hiểu tối thiểu toàn bộ pipeline để trả lời câu hỏi nối các phần, không chỉ đọc phần slide của mình.

## 4. Dàn ý 26 slide cho khoảng 37 phút

### Người 1: đặt vấn đề (slide 1–6, 8 phút)

1. **Tiêu đề + câu hỏi mở đầu.** Hai bài báo có từ khóa gần giống nhau nhưng hàng xóm khác nhau: dự đoán có nên giống nhau?
2. **Từ 5 chương đã học đến graph.** Bảng feature vector → tensor/grid → graph → knowledge/retrieval. Giữ lại quy trình học, đổi biểu diễn.
3. **Động lực phát triển.** Dữ liệu có quan hệ xuất hiện trong citation, social, recommender, molecular networks. Bỏ quan hệ có thể làm mất thông tin; graph sai cũng có thể làm mô hình tệ hơn.
4. **Định nghĩa và thuật ngữ.** G=(V,E), X, A, y; directed/undirected, homogeneous/heterogeneous. Tách rõ GNN, KG và GraphRAG.
5. **Ba cấp độ nhiệm vụ.** Node classification, link prediction, graph classification. Mỗi nhiệm vụ: một input/output và một ví dụ; đánh dấu node classification là demo chính.
6. **Thách thức của graph.** Số hàng xóm biến đổi, không có thứ tự node tự nhiên, locality không còn là cửa sổ cố định như ảnh. Nêu permutation equivariance của đầu ra theo node.

### Người 2: hiểu phép học (slide 7–13, 10 phút)

7. **CNN đến GNN.** Cùng ý tưởng chia sẻ trọng số và dùng lân cận; graph không phải grid. Đây là cầu nối trực giác, không phải bằng chứng GCN bằng CNN thường.
8. **Message passing.** Message → aggregate → update. Tổng/mean/max không phụ thuộc thứ tự hàng xóm; lặp nhiều lớp mở rộng vùng ảnh hưởng.
9. **GCN layer.** H(l+1)=σ(Â H(l) W(l)); giải thích từng đại lượng, không chỉ chiếu công thức.
10. **Tại sao cần self-loop và normalization?** Giữ thông tin bản thân và điều chỉnh ảnh hưởng theo bậc node; so sánh sơ đồ có/không có self-loop.
11. **Ví dụ tính tay.** A—B—C, x=[2,4,6], self-loop, bậc [2,3,2], W=1. h_B=2/√6+4/3+6/√6≈4,599. Đừng gọi đây là mean thông thường.
12. **Hai lớp và shapes.** X:2708×1433 → hidden:2708×32 → logits:2708×7. Softmax để hiển thị; cross-entropy dùng logits trong PyTorch.
13. **Mô hình học gì?** W được học, A cố định trong thí nghiệm này; loss chỉ trên train mask; forward → loss → backward → Adam. Cho xem 10–15 dòng code quan trọng và kết quả gradient check.

### Người 3: các kiến trúc và bằng chứng (slide 14–20, 10 phút)

14. **Từ GCN đến GraphSAGE/GAT theo vấn đề cần giải quyết.** Bảng: GCN tổng hợp với chuẩn hóa; GraphSAGE học hàm tổng hợp và có cơ chế sampling; GAT học trọng số attention giữa hàng xóm.
15. **GraphSAGE.** Học cách tạo embedding từ feature và neighborhood, hỗ trợ thiết kế inductive. Demo hiện tại dùng mean và toàn bộ hàng xóm; không được tuyên bố đã kiểm chứng khả năng inductive.
16. **GAT.** Tính e_ij → softmax theo neighborhood → tổng hợp có trọng số; multi-head. Attention weights không tự động là lời giải thích nhân quả.
17. **Cora và protocol.** Cách xây graph, normalized bag-of-words, 3 split, số nhãn; phân biệt transductive với label leakage.
18. **So sánh công bằng trong phạm vi nào?** Cùng split, feature, budget, optimizer, validation rule; số tham số khác nhau và chưa tune riêng từng mô hình. Đưa cả chất lượng và chi phí.
19. **Kết quả các kiến trúc.** LR, MLP, GCN, GraphSAGE, GAT; mean/std; macro-F1; không kết luận “GAT mới hơn nên phải tốt hơn”. Chỉ dùng kết quả đã chạy trong JSON.
20. **Ablation độ sâu.** GCN 1/2/4/8 lớp. Tách quan sát kết quả khỏi giả thuyết giải thích; accuracy giảm chưa đủ chứng minh riêng oversmoothing.

### Người 4: ứng dụng và thảo luận (slide 21–26, 9 phút)

21. **Kiến trúc hệ thống.** Train offline → lưu weights/metrics → web tải artifacts → suy luận → dự đoán + đồ thị. Dataset/weights/normalization phải cùng phiên bản.
22. **Demo tốt và sai.** Chọn GCN đúng/MLP sai, mở đối chiếu, rồi mở một ví dụ GCN sai. Không đọc nhãn thật trong inference.
23. **Demo thay đổi cạnh.** Bỏ 50%/100% cạnh incident của node, chạy lại. Có thể điểm softmax tăng hoặc giảm; nhãn có thể giữ nguyên.
24. **Deploy và tái lập.** Cho thấy URL đã chạy và cấu trúc source; giải thích tại sao train offline, web chạy CPU. Chuẩn bị bản local nếu mất mạng.
25. **Giới hạn và liên hệ chương 5.** Homophily/heterophily, oversmoothing, scaling, graph quality; graph học biểu diễn và knowledge graph biểu diễn quan hệ bổ sung cho nhau.
26. **Trả lời câu hỏi mở đầu + câu hỏi mở.** Trong protocol đã đo, quan hệ có giúp ích đến đâu? Kết quả còn phụ thuộc dữ liệu và thiết kế nào? Có thể phát triển sang recommender/KG completion như thế nào?

Nếu cần **30 phút**: gộp slide 5–6, 9–10, 14–16; vẫn giữ protocol, kết quả và demo. Nếu có **45 phút**: thêm một ví dụ attention tính tay, phân tích confusion matrix và một câu hỏi phản biện với lớp.

## 5. Những ý toán và code phải hiểu

GCN hai lớp trong demo:

```text
A_tilde = A + I
A_hat   = D_tilde^(-1/2) A_tilde D_tilde^(-1/2)
H       = ReLU(A_hat X W0)
Z       = A_hat H W1
P       = softmax(Z)
L       = cross_entropy(Z[train_mask], y[train_mask])
```

- Hàng i của X là 1.433 đặc trưng nhị phân, sau đó chia cho tổng hàng.
- A có 5.278 cạnh vô hướng; edge_index hai chiều có 10.556 cột, chưa tính self-loop.
- Không tính loss trên toàn bộ y. Nhãn test tồn tại trong file đánh giá nhưng không được dùng tối ưu W.
- `train.py` dùng ma trận sparse SciPy, đạo hàm NumPy, Adam viết tường minh. `research.py` dùng PyTorch autograd và PyG.
- MLP đối chứng trong bản NumPy cùng cấu trúc và huấn luyện, nhưng thay A_hat bằng ma trận đơn vị. Nhờ vậy thấy rõ phần xử lý quan hệ.
- Đồ thị trên web chỉ hiển thị một lân cận tối đa 61 node; suy luận vẫn chạy trên toàn bộ 2.708 node. Vị trí vẽ không phải embedding học được.

## 6. Thực nghiệm đã thiết kế

**E1 – Đóng góp của cấu trúc:** bản NumPy so sánh LR, MLP và GCN trên split 2026. MLP/GCN có seed 42,43,44.

**E2 – Kiến trúc:** bản PyG so sánh LR, MLP-2, GCN-2, GraphSAGE-2, GAT-2 trên split 2026,2027,2028; mỗi mạng 3 seed khởi tạo. LR một lần mỗi split. Mỗi split giữ 20 nhãn/chủ đề cho train, 500 validation và 1.000 test.

**E3 – Độ sâu:** GCN 1/2/4/8 lớp, cùng độ rộng hidden 32 khi có lớp ẩn. Cấu hình optimizer, learning rate, dropout, weight decay và checkpoint rule giữ cố định. Số tham số tăng theo số lớp; đây chưa phải thí nghiệm cố định số tham số.

**E4 – Độ nhạy khi suy luận:** bỏ cạnh incident của node trên web. Cạnh được chọn theo thứ tự đã lưu, không phải lấy mẫu ngẫu nhiên. Tính lại normalization, giữ nguyên weights và X. Đây không phải ablation huấn luyện có/không cạnh; không dùng để đưa kết luận nhân quả.

Các mạng PyG dùng CPU, tối đa 300 epoch, patience 60, Adam lr 0,01, weight decay 0,0005, dropout hidden 0,5; bias tắt. GAT có 4 attention head ở hidden layer, 8 chiều/head, attention dropout 0. Các cấu hình được ấn định trước; chưa tìm siêu tham số riêng cho từng mô hình.

Kết quả đã chạy ngày 13/10/2026, tổng cộng 66 lần fit cho phần PyG/LR (không tính 7 lần của bản NumPy):

| Mô hình | Accuracy mean ± std (%) | Macro-F1 (%) |
|---|---:|---:|
| Logistic Regression | 61,20 ± 0,37 | 59,04 |
| MLP 2 lớp | 60,41 ± 0,61 | 58,25 |
| GCN 2 lớp | 80,32 ± 1,16 | 79,10 |
| GraphSAGE 2 lớp | 78,84 ± 1,65 | 77,36 |
| GAT 2 lớp | 77,12 ± 1,74 | 75,71 |

GCN 1/2/4/8 lớp lần lượt đạt accuracy 72,24 / 80,32 / 74,78 / 19,64%. Với cấu hình này, tăng số lớp không cải thiện kết quả. Cần thêm thí nghiệm trước khi xác định nguyên nhân suy giảm.

Ba split có thể chồng lặp node, nên 9 runs không phải 9 bộ dữ liệu độc lập. Mean/std là mô tả biến động; không gọi đó là khoảng tin cậy 95%. Khi muốn kết luận rộng hơn, thêm dataset khác và tìm hyperparameter bằng validation với ngân sách thống nhất.

Kết quả, confusion matrix, epoch tốt nhất, runtime và parameter count nằm trong:

- `results/metrics.json`: bản NumPy.
- `results/research/metrics.json`: bản nghiên cứu PyG.
- `results/research/*_history.json`: learning curves từng lần chạy.
- `results/research/*.pt`: checkpoint PyG của từng lần chạy.
- `results/research/split_*.json`: danh sách chỉ số node ở từng split.
- `results/research/summary.csv`, `runs.csv`: bảng kết quả để đưa vào báo cáo.
- `results/figures/`: biểu đồ PNG/SVG so sánh kiến trúc và độ sâu, có thể đưa vào slide.

Để xuất lại biểu đồ: cài `requirements-figures.txt`, rồi chạy `python export_figures.py` sau khi nghiên cứu hoàn tất.

## 7. Chạy ứng dụng ngay, không cần huấn luyện lại

Yêu cầu Python có sẵn để mở HTTP server; không cần PyTorch cho web:

```powershell
cd 'D:\School\PT HTTM\DeepGraph\demo'
python -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Mở `http://127.0.0.1:8765`. Không double-click index.html vì trình duyệt có thể chặn fetch từ file://. Web có trọng số đã huấn luyện và chạy GCN thật bằng JavaScript; không cần API key hoặc server Python xử lý inference.

## 8. Huấn luyện lại và kiểm tra

Python 3.13 đã được dùng trên máy này. Khuyến nghị tạo môi trường riêng:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe train.py --epochs 300 --seeds 42 43 44
.\.venv\Scripts\python.exe -m unittest test_math -v
node test_inference.mjs
```

Cho phần PyG, cài thêm PyTorch CPU và PyG theo môi trường đã xác nhận trong `requirements-research.lock.txt`, rồi chạy:

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements-research.lock.txt
.\.venv\Scripts\python.exe research.py --epochs 300 --seeds 42 43 44 --split-seeds 2026 2027 2028
```

Lần đầu tải Cora từ nguồn LINQS. `source_sha256` trong metrics ghi hash file đã dùng. Huấn luyện lại ghi đè các kết quả cùng tên; sao lưu kết quả trước nếu muốn giữ nhiều cấu hình.

Các kiểm tra có ý nghĩa:

1. Gradient NumPy so với sai phân hữu hạn trên graph nhỏ.
2. Split không trùng nhau trong mỗi lần chia, đúng số nhãn mỗi lớp, feature normalization.
3. Logits JavaScript so với NumPy trên toàn graph.
4. Khi bỏ toàn bộ cạnh incident, node chỉ dùng self-loop đúng công thức.
5. Chép weights NumPy vào GCNConv và so logits trước khi chạy nghiên cứu PyG.

## 9. Triển khai

Ứng dụng được đóng gói như static site. Chỉ `dist/` là nội dung cần phục vụ trên web; không cần upload môi trường `.venv`, checkpoint của tất cả model, sách hoặc PDF môn học.

- **Sites:** URL và trạng thái quyền truy cập được ghi trong `DEPLOYMENT.md` sau khi triển khai. Site mới mặc định chỉ chủ tài khoản truy cập; không mặc nhiên là link công khai cho cả nhóm.
- **GitHub Pages:** đưa *nội dung* của `dist/` vào root của repo triển khai, chọn Settings → Pages → Deploy from a branch, rồi chọn branch/root. Giữ tất cả file JSON cùng vị trí với index.html. Các đường dẫn asset tương đối nên dùng được trên project Pages. Xem [hướng dẫn GitHub](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).
- **Tái triển khai:** sau khi chạy train/research lại, xuất bản lại toàn bộ dist để tránh trộn weights và dataset khác phiên bản.

Hai kiến trúc triển khai cần phân biệt khi trình bày:

```text
Huấn luyện: Cora -> preprocessing + split -> train/validation -> checkpoint -> test metrics
Ứng dụng:   Browser -> data.json + weights.json -> GCN inference -> prediction + graph
```

Demo này không có REST prediction API vì inference đủ nhỏ để chạy client. Nếu yêu cầu bài nộp cần API, bước mở rộng phù hợp là FastAPI `/predict/node/{id}` + frontend; đó là một kiến trúc triển khai khác, không phải tính năng đã có.

## 10. Kịch bản demo và câu hỏi phản biện

Demo 3 phút:

1. Mở “GCN đúng, MLP sai”, chỉ node và quan hệ xung quanh.
2. Mở phần nhãn thật/baseline, đọc đúng các nhãn và softmax.
3. Bỏ 100% cạnh của node. Quan sát điểm thay đổi; không hứa nhãn luôn phải đổi hay accuracy luôn giảm.
4. Khôi phục đồ thị, chọn ví dụ GCN sai và giải thích thông tin có thể chưa đủ.
5. Mở bảng nghiên cứu; kết luận dựa trên toàn test set và nhiều runs.

Các câu thầy có thể hỏi:

| Câu hỏi | Hướng trả lời |
|---|---|
| Vì sao không dùng MLP? | MLP là baseline cần thiết; nó không đọc A. Trên dữ liệu hiện tại, đo xem A có thêm thông tin hữu ích không. |
| Vì sao thấy node test khi train mà không leakage? | Đây là protocol transductive: X và A được biết; nhãn test không vào loss/checkpoint selection. Với yêu cầu inductive phải thiết kế split khác. |
| Vì sao có self-loop? | Mỗi node cần giữ đóng góp từ chính đặc trưng của nó khi tổng hợp. |
| Hai lớp nghĩa là gì? | Tối đa 2-hop trong kiến trúc này; nhiều lớp mở rộng receptive field nhưng có thể gặp vấn đề biểu diễn/tối ưu. |
| GraphSAGE có inductive, vậy demo đã chứng minh chưa? | Chưa. Cách chia hiện tại là transductive; muốn kiểm chứng cần giữ node/graph mới ngoài quá trình train. |
| GAT có luôn hơn GCN? | Không; phải xem dữ liệu, hyperparameter, parameter count, seed và protocol. |
| Sâu hơn kém hơn là chắc chắn oversmoothing? | Không. Cần đo thêm độ tương đồng embedding, thử residual/normalization và phân tích tối ưu để kiểm tra giả thuyết. |
| Attention có giải thích nguyên nhân dự đoán không? | Là hệ số tổng hợp đã học, không tự động là giải thích nhân quả. |
| Có nhận một bài báo mới do người dùng gõ không? | Không trong bản này. Cora chỉ có binary features và ID; cần pipeline nội dung/vocabulary cùng cách nối graph để hỗ trợ input mới. |
| Đây có phải GraphRAG không? | Không. GNN tạo dự đoán/embedding; GraphRAG lấy evidence qua graph cho hệ trả lời. Chúng có thể kết hợp nhưng khác nhiệm vụ. |
| Deploy có train lại mỗi lần mở trang không? | Không, chỉ load artifacts và inference. Train được thực hiện offline. |

## 11. Tài liệu đọc ưu tiên

1. [Kipf & Welling – Semi-Supervised Classification with Graph Convolutional Networks](https://arxiv.org/abs/1609.02907): công thức GCN và bài toán semi-supervised node classification.
2. [Hamilton, Ying & Leskovec – Inductive Representation Learning on Large Graphs](https://arxiv.org/abs/1706.02216): GraphSAGE.
3. [Veličković và cộng sự – Graph Attention Networks](https://arxiv.org/abs/1710.10903): attention trên neighborhood.
4. [Li, Han & Wu – Deeper Insights into Graph Convolutional Networks](https://arxiv.org/abs/1801.07606): góc nhìn làm mượt và giới hạn của độ sâu.
5. [PyG: Planetoid](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.datasets.Planetoid.html): cấu trúc dataset và các cách chia. Code này đọc dữ liệu raw, không dùng public split Planetoid.
6. [PyG: GATConv](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.GATConv.html), [SAGEConv](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.SAGEConv.html), [cài đặt](https://pytorch-geometric.readthedocs.io/en/latest/install/installation.html).
7. [Cora raw data – LINQS](https://linqs-data.soe.ucsc.edu/public/lbc/cora.tgz).

Nên đọc theo thứ tự: tài liệu học phần về biểu diễn/MLP/CNN → công thức GCN + code NumPy → GraphSAGE/GAT → kết quả thực nghiệm. Đưa những gì nhóm đã chạy và hiểu vào slide; dùng các hướng mở rộng như câu hỏi nghiên cứu tiếp theo.
