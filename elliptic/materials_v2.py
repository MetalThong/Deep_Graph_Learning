"""Revision 2 narrative: measured ablations, current cases, honest test reuse."""
from pathlib import Path
import copy, json
import materials as base

R=Path(__file__).resolve().parent

def main():
    report=json.loads((R/'optimization/report.json').read_text(encoding='utf-8'));metrics=json.loads((R/'results/metrics.json').read_text(encoding='utf-8'))
    slides=copy.deepcopy(base.slides);study=copy.deepcopy(base.study);S={r['model']:r for r in metrics['summary']}
    runs={r['model']:r for r in metrics['runs'] if r['seed']==0};cfg=runs['gcn']['config'];p=base.p
    cases={r['key']:r for r in json.loads((R/'results/demo_cases.json').read_text(encoding='utf-8'))}
    old=next(r for r in report['summary'] if r['name']=='GCN baseline')
    control=f"GCN đạt {p(S['gcn']['f1'])}% F1, đối chứng MLP cùng thiết lập đạt {p(S['mlp']['f1'])}%."
    compare='F1 trung bình của GCN cao hơn MLP trên lần chia này; ba seed chưa đủ để khẳng định ưu thế tổng quát.' if S['gcn']['f1']>S['mlp']['f1'] else 'GCN chưa có F1 trung bình cao hơn MLP trên lần chia này.'
    winner=max(S,key=lambda k:S[k]['f1']);names={'rf_all':'RF all','rf_local':'RF local','gcn':'GCN + skip','mlp':'MLP'}
    disclosure='Tập test từng được xem ở bản đầu. Bản cải tiến chọn cấu hình, checkpoint và ngưỡng bằng validation, rồi đánh giá lại test cũ. Nhóm chưa có một tập mới hoàn toàn để xác nhận độc lập.'
    pos_weight=23510/2871 if cfg['pos_weight']=='ratio' else cfg['pos_weight']
    training=f"Nhóm tăng ngân sách tối đa lên {cfg['epochs']} epoch và patience {cfg['patience']}. Checkpoint được chọn bằng AP validation. Cấu hình cuối có hidden {cfg['hidden']}, dropout {cfg['dropout']}, learning rate {cfg['lr']} và trọng số dương khoảng {pos_weight:.2f}. "
    training+=f"Đặc trưng neural được chặn trong khoảng âm {cfg['clip']} đến dương {cfg['clip']} sau chuẩn hóa. " if cfg['clip'] else 'Đặc trưng neural được chuẩn hóa bằng scaler học trên train. '
    if cfg.get('transform')=='quantile':training+='Nhóm còn dùng chuẩn hóa theo phân vị, học từ train, để chuyển từng đặc trưng sang thang đo gần phân bố chuẩn. '
    training+='MLP dùng cùng các thiết lập đó để đối chứng việc thêm phép truyền tin.'
    slides[7]['script']=base.slides[7]['script']+' '+disclosure
    if cfg['clip']:slides[6]['script']+=f" Sau chuẩn hóa, riêng các mô hình neural chặn giá trị đầu vào ở ±{cfg['clip']} để hạn chế ảnh hưởng của giá trị cực lớn. RF dùng đặc trưng không chặn."
    if cfg.get('transform')=='quantile':slides[6]['script']+=' Với GCN và MLP, nhóm thêm QuantileTransformer: học phân bố từng cột từ train, chuyển theo phân vị sang thang đo gần chuẩn rồi giữ nguyên phép biến đổi cho validation/test. RF dùng đặc trưng như bản đầu. Bước này không nhìn nhãn và không fit trên test.'
    slides[10]['body']=['93 đặc trưng / nút',f"{cfg['hidden']} chiều ẩn và ReLU",'Điểm đầu ra qua sigmoid']
    slides[14]['script']=f"Bảng cuối gồm bốn mô hình, mỗi mô hình ba seed. RF local dùng 93 đặc trưng; RF all thêm 72 đặc trưng tổng hợp hàng xóm. MLP và GCN đều có {95*cfg['hidden']+94} tham số, dùng cùng đầu vào và thiết lập huấn luyện cuối. Nhóm chọn thiết lập neural bằng validation của GCN rồi áp dụng cho MLP để đối chứng. Đây chưa phải kết quả tối ưu riêng cho MLP. Tất cả dùng chung cách chia thời gian. SD qua ba seed không phải khoảng tin cậy."
    slides[11].update(body=['Weighted BCE cho lớp illicit',f"Tối đa {cfg['epochs']} epoch, patience {cfg['patience']}",'Checkpoint và ngưỡng chọn bằng validation'],script=training,refs='optimize_gcn.py; optimization/selection.json; results/metrics.json')
    slides[15]['script']=f"Bản đầu GCN chỉ đạt {p(old['f1'])}% F1. Sau các đối chứng và tối ưu trên validation, GCN đạt {p(S['gcn']['f1'])}%. RF local đạt {p(S['rf_local']['f1'])}%, RF all đạt {p(S['rf_all']['f1'])}%, còn MLP với thiết lập neural tương ứng đạt {p(S['mlp']['f1'])}%. {compare} Các số là trung bình ba seed. {disclosure}"
    slides[16]['script']=f"GCN có Precision {p(S['gcn']['precision'])}%, Recall {p(S['gcn']['recall'])}% và AP {p(S['gcn']['ap'])}%. RF all có Precision {p(S['rf_all']['precision'])}%, Recall {p(S['rf_all']['recall'])}% và AP {p(S['rf_all']['ap'])}%. Precision phản ánh tỷ lệ cảnh báo đúng, Recall phản ánh tỷ lệ illicit được tìm ra. AP kiểm tra khả năng xếp hạng qua nhiều ngưỡng. Vì thế nhóm đọc cả ba khía cạnh, không lấy một ví dụ đẹp để thay kết quả toàn tập."
    if abs(S['gcn']['ap']-S['rf_all']['ap'])<.02:
        slides[16]['script']+=' AP của hai mô hình khá gần, trong khi F1 chênh lệch lớn. Điều này cho thấy cần phân biệt chất lượng xếp hạng với hiệu quả tại ngưỡng đã chọn. Nhóm giữ nguyên ngưỡng từ validation, không chọn lại bằng test.'
    long=next(r for r in report['ablations'] if r['key']=='long_gcn_0')
    slides[18].update(title='Vì sao bản đầu GCN thấp?',body=['Ban đầu: 74,8% AP validation',f"Tăng ngân sách: {p(long['validation']['ap'])}% AP",f"Cấu hình được chọn: {p(runs['gcn']['validation']['ap'])}% AP"],script=f"Nguyên nhân có bằng chứng rõ nhất là ngân sách học. Cả ba seed cũ chọn checkpoint epoch 179, sát giới hạn 180. Ở seed 0, giữ kiến trúc và tăng ngân sách cùng patience nâng AP validation từ 74,8% lên {p(long['validation']['ap'])}%. Nhóm còn thử giảm trọng số lớp, chặn giá trị lớn và chuẩn hóa theo phân vị. Sau năm cấu hình thăm dò, ứng viên tốt nhất được chạy đủ ba seed. Nhóm chọn bằng AP validation trung bình và dừng ứng viên còn lại khi cận trên toán học của nó cũng không thể vượt kết quả này. Cách đối xứng hóa graph và nhiễu hàng xóm vẫn là các giả thuyết cần thí nghiệm riêng, chưa được coi là nguyên nhân đã chứng minh.",refs='optimization/report.json; optimization/audit.json; optimize_gcn.py')
    for index,key in [(19,'detected'),(20,'false_alarm')]:
        c=cases[key];label='illicit' if c['label']==1 else 'licit'
        slides[index]['body']=[f"#{c['id']} · lát cắt {c['step']}",f"GCN: {c['scores']['gcn']:.4f}".replace('.',','),f'Nhãn tham chiếu: {label}']
        slides[index]['script']=f"Giao dịch {c['id']} ở lát cắt {c['step']} có điểm GCN {c['scores']['gcn']:.4f}, so với ngưỡng validation {runs['gcn']['threshold']:.4f}. Nhãn tham chiếu là {label}. "+('Đây là một trường hợp phát hiện đúng. Em so sánh thêm với các mô hình trên giao diện nhưng không suy rộng từ một giao dịch ra toàn bộ dataset.' if key=='detected' else 'Đây là một cảnh báo nhầm. Điểm cao không bảo đảm dự đoán đúng. Khi đánh giá công cụ sàng lọc, số cảnh báo nhầm cũng quan trọng như số illicit tìm thấy.')+' Các trường hợp được chọn sau đánh giá để minh họa. Hình mạng cung cấp ngữ cảnh, chưa phải giải thích nhân quả.'
    slides[25].update(body=[f"GCN: {p(old['f1'])}% thành {p(S['gcn']['f1'])}% F1",f"{names[winner]} có F1 cao nhất trong lần chia này",'Đối chứng cho thấy giới hạn của từng mô hình'],script=f"Nhóm tăng ngân sách học, cải thiện xử lý đặc trưng và chọn cấu hình bằng validation. GCN tăng từ {p(old['f1'])}% lên {p(S['gcn']['f1'])}% F1. {control} {names[winner]} có F1 cao nhất. RF all đã có 72 đặc trưng tổng hợp hàng xóm, còn GCN học cách kết hợp đặc trưng theo graph. Kết quả giúp nhóm lựa chọn mô hình dựa trên bằng chứng và hiểu giá trị của thông tin quan hệ. {disclosure}")
    slides[25]['script']=slides[25]['script'].replace(control,f"Đối chứng MLP cùng thiết lập đạt {p(S['mlp']['f1'])}%.")
    # Replace obsolete explanations and concrete case IDs throughout the study guide.
    for ch in study:
        for sec in ch['sections']:
            h=sec['heading']
            if h=='Luồng dữ liệu':sec['text']='prepare_data.py chuẩn bị dữ liệu. train.py lưu quy trình baseline 180 epoch. optimize_gcn.py thử cấu hình bằng validation; selection.json chốt lựa chọn trước khi đánh giá test lại. report_optimization.py kiểm tra số liệu, promote_optimized.py đồng bộ mô hình hiện hành, export_demo.py đóng gói cho web.'
            elif h=='Training, validation, test':sec['text']='Train cập nhật trọng số, validation chọn cấu hình, checkpoint và ngưỡng. Train 1-29, validation 30-34, test 35-49. '+disclosure
            elif h=='“GCN kém hơn thì đề tài có thất bại không?”':sec['text']=f'Bài toán là kiểm chứng thông tin quan hệ và xây dựng demo có đối chứng. {control} {names[winner]} có F1 cao nhất. Bài báo Elliptic gốc cũng ghi nhận RF mạnh hơn GCN. Cần nói rõ đầu vào, giao thức và giới hạn của từng kết quả.'
            elif h=='“Vì sao GCN kém?”':sec['text']=slides[18]['script']
            elif h=='00:00–01:00 · Định nghĩa':sec['text']=f"Mở trang, nói một nút là giao dịch, cạnh là dòng Bitcoin. Chọn Phát hiện đúng: ID {cases['detected']['id']}, lát cắt {cases['detected']['step']}. Đọc điểm GCN và ngưỡng. Chưa mở nhãn tham chiếu."
            elif h=='03:00–04:30 · Hai loại sai':sec['text']=f"Chọn Cảnh báo nhầm: ID {cases['false_alarm']['id']}, lát cắt {cases['false_alarm']['step']}, nhãn licit. Chuyển Bỏ sót: ID {cases['missed']['id']}, lát cắt {cases['missed']['step']}, nhãn illicit nhưng điểm dưới ngưỡng. Giải thích FP và FN."
            elif h=='06:00–07:00 · Unknown và kết luận':sec['text']=f"Chọn Chưa có nhãn: ID {cases['unknown']['id']}, lát cắt {cases['unknown']['step']}. Nói chưa thể xác nhận đúng sai. Kết thúc bằng bảng kết quả: {control} {names[winner]} có F1 cao nhất trong thực nghiệm này."
            elif h=='Tiêu chí sẵn sàng':sec['text']='Đạt ít nhất bốn câu tự kiểm tra và hoàn thành demo khoảng bảy phút. Giải thích được unknown, điểm chưa hiệu chỉnh, snapshot lịch sử và việc bản tối ưu dùng lại test cũ. Đọc đúng kết quả đối chứng GCN, MLP và RF.'
    if cfg.get('transform')=='quantile':
        for ch in study:
            if ch['title']=='Ngày 2 / Hiểu cách GCN tính điểm':ch['sections'].append(dict(heading='Chuẩn hóa ở bản 2',text='QuantileTransformer học phân bố mỗi cột trên train rồi đổi giá trị theo phân vị sang thang đo gần chuẩn. Giữ nguyên phép biến đổi cho validation và test. Không dùng nhãn để học bước này. GCN và MLP đều nhận cùng feature đã biến đổi; browser tải các feature đó từ file dữ liệu.'))
    study.append(dict(title='Bản cập nhật / Giải thích với thầy',sections=[dict(heading='Câu trả lời khoảng một phút',text=slides[25]['script']),dict(heading='Bằng chứng cần mở khi được hỏi',text='Mở optimization.html trên demo để xem đường học validation, đối chứng từng thay đổi và kết quả cũ/mới. Số liệu gốc nằm trong optimization/report.json. Bản 180 epoch và kết quả của nó được giữ trong optimization/baseline/.'),dict(heading='RF cũng tiếp cận thông tin graph',text='RF all nhận 72 đặc trưng do nhà cung cấp tổng hợp từ hàng xóm. GCN nhận graph và học phép biến đổi bằng truyền tin. RF local và đối chứng MLP giúp phân biệt tác dụng của dữ liệu đầu vào với tác dụng của kiến trúc.'),dict(heading='Giới hạn cần nói đúng',text=disclosure)]))
    out={'title':base.slides[0]['title'].replace('\n',' '),'url':base.URL,'slides':slides,'study':study,'sources':[{'title':'Elliptic dataset','url':base.DATA},{'title':'Weber et al. (2019)','url':base.PAPER},{'title':'Kipf & Welling: GCN','url':base.GCN}],'duration_seconds':sum(s['seconds'] for s in slides),'revision':2}
    (R/'presentation/.build/content.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Revision 2:',len(slides),'slides,',len(study),'study chapters')

if __name__=='__main__':main()
