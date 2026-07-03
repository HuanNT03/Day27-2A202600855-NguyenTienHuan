# Reflection (≤1 page)

Fill this in before you submit.

**Which fault types were hardest to catch, and why?**
Các lỗi tinh vi (**Subtle Faults**) trong phase Private là khó bắt nhất, đặc biệt là:
1. **Embedding Drift & Corpus Staleness** (`embedding_batch`): Độ lệch centroid (`0.0289`–`0.0311`) và số ngày trung bình của tài liệu (`31.8`–`37.6`) của các batch lỗi nằm hoàn toàn bên trong phân phối hoạt động bình thường của các batch sạch (centroid shift sạch tối đa là `0.0387` và doc age sạch tối đa là `37.5`). Do đó, không thể dùng bất kỳ ngưỡng tĩnh hay ngưỡng rolling đơn biến nào để lọc sạch chúng mà không gây báo động giả (FPR).
2. **Runtime Anomaly** (`lineage_run`): Thời gian thực thi lỗi (`4481.3`–`4739.4` ms) thấp hơn cả thời gian thực thi sạch tối đa (`4805.1` ms), làm lu mờ hoàn toàn tín hiệu lỗi trong phương sai tự nhiên của hệ thống.
3. **Subtle Data Batch Anomalies** (`data_batch`): `null_spike` (`0.0076`) và `distribution_shift` (`85.72`) đều nhỏ hơn các điểm cực đại sạch (`0.0105` và `87.58`), biến chúng thành các nhiễu trắng đối với các bộ kiểm tra đơn lẻ.

**What would you change about your cost/coverage tradeoff, if you had another pass?**
Nếu có cơ hội làm lại hoặc tối ưu hóa sâu hơn, tôi sẽ áp dụng các cải tiến MLOps sau:
1. **Multivariate Anomaly Detection (Phát hiện dị thường đa biến)**: Kết hợp các tín hiệu đơn biến thành không gian đa chiều (ví dụ: vẽ tương quan giữa Centroid Shift và Doc Age). Các điểm lỗi tuy có giá trị đơn lẻ bình thường nhưng thường nằm ngoài đường tương quan chung (joint distribution outliers), giúp phát hiện chính xác hơn.
2. **Sequential Drift Detection (CUSUM/EWMA)**: Thay vì đánh giá từng event độc lập, tôi sẽ dùng thuật toán CUSUM hoặc EWMA để giám sát chuỗi thời gian của luồng sự kiện. Một sự dịch chuyển nhỏ nhưng liên tục về giá trị trung bình sẽ kích hoạt cảnh báo sớm.
3. **Adaptive Local Baselines**: Lưu trữ ngữ cảnh cụ thể cho từng thực thể (ví dụ: baselines riêng cho từng `table` hoặc `corpus`) thay vì so sánh với một baseline dùng chung cho toàn bộ stream. Điều này sẽ triệt tiêu gần như hoàn toàn FPR.

