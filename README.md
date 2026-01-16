# PDPTW Solver - Demo Project

Đây là dự án giải quyết bài toán **Pickup and Delivery Problem with Time Windows (PDPTW)** sử dụng các thuật toán Metaheuristics hiện đại.

Dự án được thiết kế để tối ưu hóa lộ trình giao nhận hàng hóa với các ràng buộc khắt khe về khung thời gian (Time Windows) và ưu tiên (Precedence).

---

## � 1. Cài đặt & Chuẩn bị

### Bước 1: Clone dự án
```bash
git clone https://github.com/thanhsonnee/pdptw-instances.git
cd pdptw-instances
```

### Bước 2: Cài đặt môi trường
Đảm bảo bạn đã cài đặt Python (3.8+). Sau đó cài đặt các thư viện cần thiết:
```bash
cd algorithm
pip install -r requirements.txt
```

---

## 🎮 2. Demo Chức năng (Kịch bản Demo)

Dưới đây là 3 kịch bản demo chính để trình bày khả năng của hệ thống.

### Kịch bản 1: Kiểm tra nhanh (Quick sanity check)
Chạy thử nghiệm trên 3 bộ dữ liệu chuẩn (Li & Lim) để đảm bảo hệ thống hoạt động ổn định.

**Lệnh chạy:**
```bash
python test_li_lim_quick.py
```
**Kết quả mong đợi:**
- Thời gian chạy: ~1 phút
- Kết quả: Feasible (Hợp lệ) cho cả 3 instances (lc101, lr101, lrc101).

### Kịch bản 2: Giải bài toán thực tế & Trực quan hóa (Viusalization)
Giải bài toán quy mô lớn (Barcelona) và hiển thị lộ trình lên bản đồ thực tế.

**Lệnh chạy:**
```bash
python demo_sartori.py
```
**Kết quả mong đợi:**
- Hệ thống sẽ tìm lời giải trong 60s.
- File kết quả được lưu tại `algorithm/output_demo/solution_bar-n100-1.txt`.

**Xem trên bản đồ:**
1. Mở file `visualizer/visualizer.html` bằng trình duyệt web.
2. Mục **Instance**: Chọn file `instances/n100/n100/bar-n100-1.txt`.
3. Mục **Solution**: Chọn file kết quả vừa tạo (`algorithm/output_demo/solution_bar-n100-1.txt`).
4. Quan sát lộ trình được vẽ trên bản đồ.

### Kịch bản 3: Benchmark toàn diện (Full Test)
Chạy kiểm thử trên toàn bộ 56 instances của bộ Li & Lim (chỉ chạy nếu có nhiều thời gian).

**Lệnh chạy:**
```bash
python test_li_lim.py
```

### Kịch bản 4: Phase 1 Test (Kiểm thử tối ưu hóa Phase 1)
Chạy thử nghiệm trên instance lc101 với các cải tiến mới nhất (Lexicographic ordering, Route Elimination, Worst Removal, Variable Regret-k).

### Script kiểm tra tính hợp lệ (Validation)
Để chứng minh kết quả tạo ra luôn tuân thủ mọi ràng buộc:
```bash
python check_feasible.py
```

---

## 🧠 3. Giải thích Thuật toán

Dự án sử dụng chiến lược **Multi-stage Metaheuristics** (Metaheuristics đa giai đoạn):

1.  **Giai đoạn 1: Khởi tạo (Construction)**
    -   Sử dụng giải thuật tham lam (Greedy) hoặc Clarke-Wright Savings để tạo ra một lời giải ban đầu *chấp nhận được* (feasible).

2.  **Giai đoạn 2: Giảm số lượng xe (AGES)**
    -   Áp dụng thuật toán **AGES (Automated Generation of Efficient Solutions)**.
    -   Cố gắng gộp các lộ trình nhỏ lại với nhau, mục tiêu chính là giảm số lượng xe sử dụng xuống mức tối thiểu.

3.  **Giai đoạn 3: Tối ưu chi phí (LNS & Local Search)**
    -   **LNS (Large Neighborhood Search)**: Phá hủy (xóa bớt khách hàng) và sửa chữa (thêm lại khách hàng) để tìm cấu trúc lộ trình tốt hơn.
    -   **Local Search**: Tinh chỉnh cục bộ (2-opt, Relocate, Exchange) để giảm tổng quãng đường di chuyển.

4.  **Cơ chế thoát cực trị địa phương (Perturbation)**
    -   Nếu thuật toán bị kẹt, hệ thống sẽ "rung lắc" (perturb) lời giải bằng cách đảo lộn ngẫu nhiên một số phần tử, giúp tìm kiếm các hướng đi mới.

---

## 📂 4. Cấu trúc Thư mục

-   `algorithm/`: Chứa mã nguồn chính (Python).
-   `instances/`: Dữ liệu đầu vào (Li & Lim, Sartori Real-world).
-   `solutions/`: Nơi lưu trữ các kết quả tốt nhất từng tìm được.
-   `visualizer/`: Công cụ hiển thị lộ trình (HTML/JS).
-   `docs/`: Tài liệu chi tiết và báo cáo kỹ thuật.

---
