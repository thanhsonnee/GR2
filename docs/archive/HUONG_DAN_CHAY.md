<!--
STATUS: ARCHIVED (do not edit - historical reference only)
PURPOSE: Vietnamese running instructions (original version)
DATE: Archived January 2026
REPLACED BY: algorithm/QUICKSTART.md
-->

# HƯỚNG DẪN CHẠY THUẬT TOÁN PDPTW

## Cách chạy nhanh

### 1. Test nhanh (3 instances Li & Lim)
```bash
cd algorithm
python test_li_lim_quick.py
```
**Thời gian**: ~1 phút

**Kết quả mong muốn**:
```
[1/3] Testing lc101...
  Result: 20 veh, cost 2234, feasible=True ✓

[2/3] Testing lr101...
  Result: 29 veh, cost 2393, feasible=True ✓

[3/3] Testing lrc101...
  Result: 22 veh, cost 2486, feasible=True ✓
```

**Giải thích**:
- `feasible=True` → Lời giải HỢP LỆ ✓
- `feasible=False` → Lời giải VI PHẠM ràng buộc ✗

---

### 2. Test đầy đủ Li & Lim (56 instances)
```bash
cd algorithm
python test_li_lim.py
```
**Thời gian**: ~10-15 phút

**Kết quả được lưu vào**:
- `li_lim_results.json` - Kết quả chi tiết
- `li_lim_results.csv` - Bảng Excel-friendly

---

### 3. Test Sartori & Buriol (3 instances)
```bash
cd algorithm
python test_feasibility.py
```
**Thời gian**: ~3 phút

---

## Cách xem kết quả

### Xem trực tiếp trong console

Tìm dòng này:
```
============================================================
ILS COMPLETED
============================================================
Best solution: 20 vehicles, cost 2234
Feasible solution: YES          ← Quan trọng!
Vehicle gap: 0.00%
Cost gap: 0.00%
Total time: 24.46s
```

**Nếu thấy `Feasible solution: YES`** → OK ✓

**Nếu thấy `Feasible solution: NO`** → Có lỗi, cần fix ✗

---

### Xem file JSON (chi tiết từng instance)

Mở `li_lim_results.json`:
```json
{
  "summary": {
    "total": 56,
    "feasible": 56,      ← Số lời giải hợp lệ
    "infeasible": 0,     ← Số lời giải vi phạm
    "failed": 0          ← Số instance lỗi
  },
  "results": [
    {
      "instance": "lc101",
      "feasible": true,   ← Hợp lệ: true/false
      "vehicles": 20,
      "cost": 2234.5,
      "runtime": 24.5
    },
    ...
  ]
}
```

---

### Xem file CSV (import vào Excel)

Mở `li_lim_results.csv`:
```
Instance,Class,Status,Feasible,Vehicles,Cost,Runtime_s
lc101,LC,FEASIBLE,True,20,2234.00,24.50
lc102,LC,FEASIBLE,True,18,2015.00,22.30
...
```

**Cột quan trọng**:
- `Status`: FEASIBLE (OK) / INFEASIBLE (Lỗi)
- `Feasible`: True (OK) / False (Lỗi)

---

## Cách kiểm tra nhanh: Tất cả có feasible không?

### Lệnh đơn giản: Kiểm tra JSON
```bash
cd algorithm
python check_feasible.py
```

**Kết quả mong muốn**:
```
KẾT QUẢ LI & LIM
Tổng số instances: 56
Feasible (HỢP LỆ): 56/56 (100.0%)
✓ TẤT CẢ ĐỀU FEASIBLE - HOÀN HẢO!
```

---

### Lệnh đơn giản: Kiểm tra CSV
```bash
cd algorithm
python check_csv.py
```

**Kết quả mong muốn**: Hiển thị bảng thống kê + `✓ TẤT CẢ ĐỀU FEASIBLE!`

---

## Ý nghĩa các ràng buộc (PHẢI đảm bảo)

1. **Pickup trước Delivery**: Phải lấy hàng trước khi giao
2. **Time Window**: Đến đúng giờ (không sớm/muộn quá)
3. **Capacity**: Không chở quá tải trọng xe
4. **Mỗi request đúng 1 lần**: Không thiếu, không thừa

**Nếu vi phạm 1 trong 4 → `feasible=False`**

---

## Nếu gặp lỗi

### Lỗi: "No module named ..."
```bash
# Kiểm tra đang ở thư mục nào
pwd

# Phải ở thư mục algorithm/
cd algorithm
```

### Lỗi: "File not found"
```bash
# Kiểm tra file instances có đúng không
ls ../instances/pdp_100/lc101.txt

# Nếu không có → kiểm tra đường dẫn
```

### Xem log chi tiết khi chạy
```bash
python test_li_lim.py 2>&1 | tee output.txt
```
Sau đó mở `output.txt` để xem chi tiết.

---

## Tóm tắt

| File Test | Dataset | Số Instances | Thời gian |
|-----------|---------|--------------|-----------|
| `test_li_lim_quick.py` | Li & Lim | 3 | 1 min |
| `test_li_lim.py` | Li & Lim | 56 | 10-15 min |
| `test_feasibility.py` | Sartori | 3 | 3 min |

**Kiểm tra nhanh**: 
- Console có `Feasible solution: YES` → ✓
- JSON có `"feasible": true` → ✓
- CSV có `Feasible,True` → ✓

**MỌI LỜI GIẢI PHẢI FEASIBLE!**
