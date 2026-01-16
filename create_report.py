import json
import pandas as pd
import os
import re

# --- CẤU HÌNH ---
ILS_FILE = os.path.join('algorithm', 'ils_batch_results.json')
OUTPUT_FILE = 'Bao_cao_chi_tiet_PDPTW.xlsx'

def extract_group_name(instance_name):
    """
    Tách tên nhóm từ tên file.
    Ví dụ: 'bar-n100-1.txt' -> 'bar-n100'
           'nyc-n100-5.txt' -> 'nyc-n100'
    """
    # Xóa đuôi .txt nếu có
    name = instance_name.replace('.txt', '')
    
    # Logic tách: Lấy phần chữ và phần số đầu tiên (thường là định dạng dataset-size)
    # Pattern: kytuk-so-so -> lấy kytuk-so
    parts = name.split('-')
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}"
    return "Other"

def load_and_process_data():
    if not os.path.exists(ILS_FILE):
        print(f"[LỖI] Không tìm thấy file dữ liệu: {ILS_FILE}")
        return None

    try:
        with open(ILS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[LỖI] Đọc file JSON thất bại: {e}")
        return None

    if not data:
        print("[CẢNH BÁO] File JSON rỗng!")
        return None

    processed_rows = []
    for entry in data:
        # Bỏ qua các lần chạy lỗi hoàn toàn (status = FAILED)
        if entry.get('status') == 'FAILED':
            continue

        instance_name = entry.get('instance', 'Unknown').replace('.txt', '')
        group = extract_group_name(instance_name)
        
        # Format dữ liệu cho đẹp
        row = {
            'Group': group, # Dùng để chia sheet
            'Instance': instance_name,
            'Cost (ILS)': entry.get('cost'),
            'Vehicles': entry.get('vehicles'),
            'Gap Cost (%)': round(entry.get('gap_cost', 0.0), 2),
            'Gap Veh (%)': round(entry.get('gap_vehicles', 0.0), 2),
            'Time (s)': round(entry.get('runtime', 0.0), 2),
            'Best Known Cost': entry.get('best_cost', '-'),
            'Best Known Veh': entry.get('best_vehicles', '-'),
            'Feasible': "YES" if entry.get('is_feasible') else "NO"
        }
        processed_rows.append(row)

    return pd.DataFrame(processed_rows)

def create_excel_report():
    print(">>> Đang xử lý dữ liệu báo cáo...")
    df = load_and_process_data()
    
    if df is None or df.empty:
        print("Không có dữ liệu hợp lệ để tạo báo cáo.")
        return

    print(f">>> Tìm thấy {len(df)} kết quả chạy thử nghiệm.")
    print(f">>> Đang ghi ra file: {OUTPUT_FILE}")

    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            # 1. Tạo Sheet "SUMMARY" (Tổng hợp)
            summary_pivot = df.pivot_table(
                index='Group', 
                values=['Gap Cost (%)', 'Gap Veh (%)', 'Time (s)', 'Cost (ILS)'], 
                aggfunc={'Gap Cost (%)': 'mean', 'Gap Veh (%)': 'mean', 'Time (s)': 'mean', 'Cost (ILS)': 'count'}
            )
            summary_pivot.rename(columns={'Cost (ILS)': 'Total Instances'}, inplace=True)
            # Làm tròn số trong bảng tổng hợp
            summary_pivot = summary_pivot.round(2)
            summary_pivot.to_excel(writer, sheet_name='SUMMARY')
            
            # 2. Tạo Sheet chi tiết cho từng nhóm (bar-n100, nyc-n100...)
            # Lấy danh sách các nhóm duy nhất
            groups = df['Group'].unique()
            groups.sort()
            
            for group_name in groups:
                # Lọc dữ liệu thuộc nhóm này
                group_df = df[df['Group'] == group_name].copy()
                
                # Bỏ cột Group vì tên sheet đã nói lên điều đó rồi
                group_df = group_df.drop(columns=['Group'])
                
                # Sắp xếp theo tên Instance
                group_df = group_df.sort_values(by='Instance')
                
                # Sắp xếp lại thứ tự cột cho giống báo cáo khoa học
                cols_order = [
                    'Instance', 'Vehicles', 'Cost (ILS)', 
                    'Gap Veh (%)', 'Gap Cost (%)', 
                    'Time (s)', 
                    'Best Known Veh', 'Best Known Cost', 
                    'Feasible'
                ]
                # Chỉ lấy các cột tồn tại
                cols_order = [c for c in cols_order if c in group_df.columns]
                group_df = group_df[cols_order]
                
                # Ghi vào sheet mới
                sheet_name = str(group_name)[:30] # Excel giới hạn tên sheet 31 ký tự
                group_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # --- Format độ rộng cột tự động ---
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"\n[THÀNH CÔNG] File báo cáo đã được tạo tại: {os.path.abspath(OUTPUT_FILE)}")
        print("- Sheet 'SUMMARY': Xem thống kê trung bình.")
        print("- Các Sheet khác: Kết quả chi tiết từng bộ dữ liệu (bar-n100, ber-n100...).")

    except Exception as e:
        print(f"[LỖI] Không thể ghi file Excel: {e}")

if __name__ == "__main__":
    create_excel_report()