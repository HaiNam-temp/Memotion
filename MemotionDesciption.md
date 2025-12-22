# MEMOTION – HỆ THỐNG CHĂM SÓC SỨC KHỎE & TINH THẦN CHO NGƯỜI BỆNH

## 1. Tổng quan hệ thống

**Memotion** là hệ thống hỗ trợ chăm sóc sức khỏe toàn diện cho bệnh nhân (đặc biệt là người cao tuổi), kết hợp giữa:

* Theo dõi sức khỏe thể chất
* Theo dõi tinh thần – cảm xúc
* Lộ trình chăm sóc (Care Plan)
* Nhắc lịch uống thuốc, ăn uống, tập luyện
* Tương tác với chatbot AI để hỗ trợ tâm lý và ghi nhận lịch sử hội thoại

Hệ thống có **2 vai trò chính**:

* **PATIENT**: Người bệnh
* **CARETAKER**: Người chăm sóc (gia đình, y tá, điều dưỡng…)

---

## 2. Mô hình người dùng & quan hệ

### 2.1 Users

Bảng `users` lưu toàn bộ người dùng trong hệ thống.

* Mỗi user có một vai trò: `PATIENT` hoặc `CARETAKER`
* Email là duy nhất

### 2.2 Quan hệ Patient – Caretaker (1–1)

Bảng `patient_caretaker`:

* 1 bệnh nhân chỉ có **1 người chăm sóc chính**
* 1 người chăm sóc chỉ chăm **1 bệnh nhân** (theo thiết kế hiện tại)

---

## 3. Hồ sơ bệnh nhân (Patient Profile)

### 3.1 Patient Profile – thông tin chung

Bảng `patient_profile` đại diện cho **hồ sơ sức khỏe tổng quát** của bệnh nhân:

* Thông tin sinh học: giới tính, BMI, nhịp tim, huyết áp, đường huyết
* Chỉ số chức năng sinh hoạt: ADL, IADL
* Loại bệnh chính (`disease_type`):

  * PHYSICAL_THERAPY (vật lý trị liệu – xương khớp)
  * MENTAL_DECLINE (suy giảm trí nhớ)
  * LONELINESS (cô đơn – trầm cảm)

Mỗi bệnh nhân **chỉ có 1 profile active**.

---

### 3.2 Bảng chi tiết theo từng loại bệnh

Thiết kế theo hướng **table-per-disease** để:

* Tránh bảng quá lớn
* Dễ mở rộng thêm bệnh mới
* Dữ liệu đúng ngữ nghĩa y khoa

#### a. Physical Therapy (Xương khớp – VLTL)

Bảng `patient_physical_therapy`:

* Vị trí đau, mức độ đau (VAS)
* Đánh giá cơ, thăng bằng, nguy cơ té ngã
* Khả năng đứng dậy, thời gian TUG
* Tiền sử bệnh, điều trị trước đó
* Khuyến nghị & liệu trình từ bác sĩ

#### b. Mental Decline (Suy giảm trí nhớ)

Bảng `patient_mental_decline`:

* Điểm MMSE, FAST
* Vấn đề trí nhớ, định hướng
* Chức năng sinh hoạt cần hỗ trợ
* Thay đổi hành vi
* Nhận xét & kế hoạch điều trị

#### c. Loneliness (Cô đơn – tinh thần)

Bảng `patient_loneliness`:

* LSNS-6 (gia đình, bạn bè)
* UCLA loneliness score
* GDS-15 (trầm cảm)
* Trạng thái cảm xúc, hành vi

---

## 4. Care Plan – Lộ trình chăm sóc

Bảng `care_plan`:

* Mỗi bệnh nhân chỉ có **1 care plan đang active**
* Gắn với người chăm sóc chịu trách nhiệm

Care Plan là **xương sống của hệ thống task**.

---

## 5. Task & Thư viện nội dung

### 5.1 Thư viện nội dung (Library)

Dùng để tái sử dụng dữ liệu chuẩn:

* `medication_library`: thuốc
* `nutrition_library`: bữa ăn
* `exercise_library`: bài tập

---

### 5.2 Task – Công việc hằng ngày

Bảng `task` là bảng trung tâm:

Mỗi task gồm:

* Thuộc 1 care_plan
* Có thời gian cụ thể (date + time)
* Có loại:

  * MEDICATION
  * NUTRITION
  * EXERCISE
* Trạng thái: `PENDING | DONE | SKIPPED`

#### Task liên kết Patient ↔ Caretaker

Trường `linked_task_id` dùng để:

* Khi caretaker tạo task theo dõi
* Patient có task tương ứng để thực hiện

---

## 6. Nhắc lịch – Reminder Service

### 6.1 Task Reminder

Bảng `task_reminder`:

* Mỗi task có thể có nhiều reminder
* Nhắc trước: 10 phút, 30 phút, 2 giờ…
* Kênh:

  * APP_NOTIFICATION
  * SMS
  * VOICE_CALL

### 6.2 Logic nhắc lịch

1. Khi tạo task → tạo reminder
2. Hệ thống tính `remind_time`
3. Background job (Scheduler):

   * Quét reminder sắp đến hạn
   * Gửi notification
   * Cập nhật trạng thái `SENT`

---

## 7. Theo dõi sức khỏe & cảm xúc hằng ngày

### 7.1 Health Daily Track

Bảng `health_daily_track`:

* Mỗi bệnh nhân **1 bản ghi / ngày**
* Lưu:

  * Chỉ số sinh tồn
  * Cảm xúc (mood, stress, loneliness)
  * Mức độ hoàn thành task
  * Hoạt động xã hội
  * Phân tích giọng nói (cho AI)

Dữ liệu này dùng để:

* Phân tích xu hướng
* Cảnh báo sớm
* Đầu vào cho AI

---

## 8. Notification System

Bảng `notification`:

* Gửi cho patient hoặc caretaker
* Các loại:

  * REMINDER
  * TASK
  * HEALTH
  * SYSTEM

Ví dụ:

* Quên uống thuốc
* Chỉ số stress tăng cao
* Không hoàn thành task nhiều ngày

---

## 9. AI Chatbot & Lịch sử hội thoại (định hướng mở rộng)

Hệ thống được thiết kế sẵn để mở rộng:

* Chatbot nói chuyện với bệnh nhân mỗi ngày
* Ghi nhận:

  * Cảm xúc
  * Từ khóa tiêu cực
  * Dấu hiệu suy giảm trí nhớ

Lịch sử chat sẽ được:

* Lưu theo ngày
* Liên kết với health_daily_track
* Làm dữ liệu huấn luyện AI

---

## 10. Tổng kết kiến trúc

**Ưu điểm thiết kế**:

* Chuẩn hóa dữ liệu y tế
* Dễ mở rộng bệnh mới, task mới
* Tách rõ domain: Profile – Care Plan – Task – Health – AI
* Phù hợp microservice hoặc monolith mở rộng

**Hướng phát triển tiếp**:

* Risk Scoring Engine
* AI cảnh báo sớm
* Voice assistant cho người cao tuổi
* Dashboard phân tích cho caretaker

---

> Memotion không chỉ là app nhắc lịch, mà là **hệ sinh thái chăm sóc sức khỏe và tinh thần liên tục**.
