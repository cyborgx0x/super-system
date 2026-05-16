# Use Case — Super System

## Tổng quan

Ứng dụng giúp người dùng đạt thuần thục kỹ năng thông qua gamification kiểu truyện hệ thống. AI Agent chạy nền, sinh nhiệm vụ cá nhân hóa và chấm điểm tự động. Người dùng không chat với agent — chỉ tương tác qua danh sách nhiệm vụ.

**MVP:** Kỹ năng viết lách.

---

## Thuật ngữ

| Thuật ngữ | Định nghĩa |
|-----------|-----------|
| **Hệ thống** | AI Agent hoạt động nền — quan sát, sinh nhiệm vụ, chấm điểm và cập nhật hồ sơ kỹ năng |
| **Nhiệm vụ chính tuyến** | Chuỗi nhiệm vụ chuẩn dùng để xác định level thực tế của người dùng |
| **Nhiệm vụ phụ tuyến** | Nhiệm vụ target điểm yếu cụ thể, sinh động theo tiến trình |
| **Điểm thuần thục** | Đơn vị đo mức thành thạo theo từng khía cạnh kỹ năng |
| **Hồ sơ kỹ năng** | Bản đồ kỹ năng của người dùng, agent lưu trong memory và cập nhật liên tục |

---

## Actor

| Actor | Vai trò |
|-------|---------|
| **Người dùng** | Điền form onboarding, chọn nhiệm vụ, nộp bài, xem kết quả |
| **AI Agent** | Hoạt động hoàn toàn nền: đọc hồ sơ, sinh nhiệm vụ, chấm bài, cập nhật hồ sơ |

---

## UC01 — Onboarding

**Mục tiêu:** Thu thập thông tin tối thiểu để agent sinh danh sách nhiệm vụ đầu tiên.

**Tiền điều kiện:** Người dùng chưa có hồ sơ kỹ năng.

**Luồng:**

1. Hệ thống hiển thị form ngắn: kỹ năng muốn phát triển, mục tiêu, bối cảnh cuộc sống, tự đánh giá kinh nghiệm.
2. Người dùng điền và submit form.
3. Agent chạy nền: tạo hồ sơ kỹ năng, sinh danh sách nhiệm vụ chính tuyến đầu tiên.
4. Hệ thống hiển thị danh sách nhiệm vụ.

---

## UC02 — Xem và chọn nhiệm vụ

**Mục tiêu:** Người dùng chọn một nhiệm vụ để thực hiện từ danh sách đã chuẩn bị sẵn.

**Luồng:**

1. Người dùng mở ứng dụng, thấy danh sách nhiệm vụ.
2. Mỗi nhiệm vụ hiển thị: tiêu đề, loại nhiệm vụ, bối cảnh, phần thưởng dự kiến.
3. Người dùng chọn một nhiệm vụ để bắt đầu.

**Loại nhiệm vụ:**

| Loại | Mục tiêu |
|------|----------|
| **Output** | Viết một đoạn văn theo bối cảnh cho trước |
| **Feynman** | Giải thích một khái niệm bằng ngôn ngữ của bản thân |
| **Phân tích** | Đọc đoạn văn mẫu, chỉ ra điểm yếu theo khía cạnh cụ thể |
| **Sửa bài** | Rewrite đoạn văn để cải thiện một khía cạnh xác định |

---

## UC03 — Nộp bài

**Mục tiêu:** Người dùng hoàn thành và nộp kết quả nhiệm vụ.

**Luồng:**

1. Người dùng đọc yêu cầu nhiệm vụ, thực hiện và nhập bài vào form.
2. Người dùng nộp bài.
3. Agent chạy nền: chấm điểm, cập nhật hồ sơ kỹ năng, sinh nhiệm vụ tiếp theo.
4. Hệ thống hiển thị kết quả.

---

## UC04 — Xem kết quả

**Mục tiêu:** Người dùng nhận phản hồi tức thì về bài nộp.

**Luồng:**

1. Hệ thống hiển thị điểm từng khía cạnh kỹ năng, nhận xét ngắn và tổng điểm thuần thục nhận được.
2. Người dùng chuyển sang nhiệm vụ tiếp theo hoặc quay về danh sách.

---

## UC05 — Xem tiến trình

**Mục tiêu:** Người dùng theo dõi sự phát triển kỹ năng theo thời gian.

**Luồng:**

1. Người dùng vào mục tiến trình.
2. Hệ thống hiển thị hồ sơ kỹ năng: điểm thuần thục theo từng khía cạnh, lịch sử nhiệm vụ, điểm yếu đang được target.

---

## Ràng buộc

- Không có màn hình chat. Người dùng chỉ tương tác qua: form onboarding → danh sách nhiệm vụ → form nộp bài → kết quả.
- Agent hoạt động hoàn toàn nền.
- Nhiệm vụ phải target deliberate practice — nhắm vào điểm yếu hiện tại, không sinh ngẫu nhiên.
- Rubric chấm điểm phải calibrate theo level thực tế của người dùng.
- Instant feedback — kết quả trả về trong cùng phiên làm việc.
