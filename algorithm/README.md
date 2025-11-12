# PDPTW Algorithm Implementation

Đây là implementation thuật toán giải bài toán Pickup and Delivery Problem with Time Windows (PDPTW) sử dụng benchmark dataset từ repository này.

## Cấu trúc thư mục:
- `data_loader.py`: Classes để đọc instance và solution files
- `solution_encoder.py`: Class để encode solution theo format chuẩn  
- `construction_heuristic.py`: Thuật toán construction heuristic   
- `local_search.py`: Các move operators cho local search
- `metaheuristic.py`: Metaheuristic algorithms (SA, TS, GA)
- `evaluator.py`: Script đánh giá hiệu suất
- `main.py`: File chính để chạy thuật toán

## Sử dụng:
```bash
python main.py --instance instances/sample_instance.txt --method construction
python main.py --instance instances/sample_instance.txt --method metaheuristic --algorithm sa
```

## Citation:
Khi sử dụng dataset này trong nghiên cứu, vui lòng cite bài báo gốc:
```
@article{sartori-buriol-2020,
    title = "A Study on the Pickup and Delivery Problem with Time Windows: Matheuristics and New Instances",
    author = "Carlo S. Sartori and Luciana S. Buriol",
    journal = "Computers & Operations Research",
    pages = "105065",
    year = "2020",
    issn = "0305-0548",
    doi = "https://doi.org/10.1016/j.cor.2020.105065"
}
```
