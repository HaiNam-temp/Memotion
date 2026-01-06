-- 1. USERS
INSERT INTO users (user_id, full_name, email, hashed_password, phone, role, created_at, is_active) VALUES
('4b815548-d435-405a-a7fd-92051c87ef2e', 'Nguyen Van A', 'patient@example.com', 'hashed_pw_1', '0900000001', 'PATIENT', '2025-01-01 09:00:00', TRUE),
('fe08799d-6faf-4eb8-80de-9d34269d32c8', 'Tran Thi B', 'caretaker@example.com', 'hashed_pw_2', '0900000002', 'CARETAKER', '2025-01-01 09:00:00', TRUE);

-- 2. PATIENT - CARETAKER RELATION
INSERT INTO patient_caretaker (patient_id, caretaker_id, assigned_at) VALUES
('4b815548-d435-405a-a7fd-92051c87ef2e', 'fe08799d-6faf-4eb8-80de-9d34269d32c8', '2025-01-01 09:00:00');

-- 3. PATIENT PROFILE
INSERT INTO patient_profile (
    profile_id, patient_id, gender, living_arrangement,
    BMI_score, MAP_score, RHR_score, ADL_score, IADL_score, blood_glucose_level,
    disease_type, condition_note, updated_at
) VALUES (
    'c341ef12-cb27-4017-ae00-346ad318dd87',
    '4b815548-d435-405a-a7fd-92051c87ef2e',
    'MALE',
    'SỐNG CÙNG GIA ĐÌNH',
    23, 95, 72, 80, 7, 110,
    'PHYSICAL_THERAPY',
    'Đau khớp gối phải, hạn chế vận động',
    '2025-01-01 09:00:00'
);

-- 4. PATIENT PHYSICAL THERAPY DETAIL
INSERT INTO patient_physical_therapy (
    profile_id, pain_location, pain_scale_score, pain_character, pain_assessment,
    muscle_tone, muscle_strength, balanced_valuation, fall_risk,
    self_stand_ability, tug_time,
    previous_illness, previous_treatments, daily_actities,
    doctor_recommended, doctor_treatment_plan, note
) VALUES (
    'c341ef12-cb27-4017-ae00-346ad318dd87',
    'Gối phải',
    6,
    'Đau âm ỉ khi vận động',
    'Đau vừa',
    'Tăng nhẹ',
    'Giảm nhẹ',
    'Đi lại chậm, hơi mất thăng bằng',
    'Nguy cơ té ngã trung bình',
    'HARD',
    14,
    'Tăng huyết áp, thoái hóa khớp',
    'Dùng thuốc giảm đau, tập phục hồi chức năng',
    'Đi lại trong nhà, lên xuống vài bậc cầu thang',
    'Nên tập vận động khớp gối hằng ngày',
    'Liệu trình vật lý trị liệu 3 buổi/tuần trong 4 tuần',
    'Cần hỗ trợ khi di chuyển xa'
);

-- 5. CARE PLAN
INSERT INTO care_plan (
    care_plan_id, patient_id, caretaker_id, created_at, updated_at
) VALUES (
    '697fa88d-976e-40b3-88a8-340d1a813e23',
    '4b815548-d435-405a-a7fd-92051c87ef2e',
    'fe08799d-6faf-4eb8-80de-9d34269d32c8',
    '2025-01-01 09:00:00',
    '2025-01-01 09:00:00'
);

-- 6. MEDICATION / NUTRITION / EXERCISE LIBRARY
INSERT INTO medication_library (
    medication_id, name, description, dosage, frequency_per_day, notes, image_path
) VALUES (
    '2acb6e68-01f3-41dd-a279-8f2016939b5e',
    'Paracetamol 500mg',
    'Thuốc giảm đau, hạ sốt',
    '1 viên',
    2,
    'Uống sau ăn',
    '/images/meds/paracetamol.png'
);

INSERT INTO nutrition_library (
    nutrition_id, name, calories, description, meal_type, image_path
) VALUES (
    '3bff51cd-72a9-4023-8c7f-19ec37ec0f71',
    'Cháo yến mạch',
    180,
    'Bữa sáng ít béo, tốt cho tim mạch',
    'BREAKFAST',
    '/images/food/oatmeal.png'
);

INSERT INTO exercise_library (
    exercise_id, name, target_body_region, description, duration_minutes, difficulty_level, video_path
) VALUES (
    'd42e2a3c-8505-4734-ba46-629e5de3590d',
    'Tập co duỗi gối',
    'Khớp gối',
    'Ngồi trên ghế, co duỗi gối chậm rãi 10–15 lần mỗi chân',
    15,
    2,
    '/videos/exercise/knee_flex.mp4'
);

-- 7. TASK
INSERT INTO task (
    task_id, care_plan_id, owner_type, title, description,
    task_date, task_time, task_type,
    medication_id, nutrition_id, exercise_id,
    status, linked_task_id
) VALUES
(
    '5450e11b-0b9d-4c78-b427-46de43b44c60',
    '697fa88d-976e-40b3-88a8-340d1a813e23',
    'PATIENT',
    'Uống Paracetamol sáng',
    'Uống thuốc giảm đau sau ăn sáng',
    '2025-01-02',
    '08:00:00',
    'MEDICATION',
    '2acb6e68-01f3-41dd-a279-8f2016939b5e',
    NULL,
    NULL,
    'PENDING',
    NULL
),
(
    'bbeaddc9-8757-4820-8803-baf77678557e',
    '697fa88d-976e-40b3-88a8-340d1a813e23',
    'PATIENT',
    'Ăn cháo yến mạch',
    'Bữa sáng nhẹ, ít béo',
    '2025-01-02',
    '07:30:00',
    'NUTRITION',
    NULL,
    '3bff51cd-72a9-4023-8c7f-19ec37ec0f71',
    NULL,
    'PENDING',
    NULL
),
(
    '2701ba14-38e4-46d2-a36d-9006be45da68',
    '697fa88d-976e-40b3-88a8-340d1a813e23',
    'PATIENT',
    'Tập co duỗi gối',
    'Bài tập vận động khớp gối',
    '2025-01-02',
    '09:00:00',
    'EXERCISE',
    NULL,
    NULL,
    'd42e2a3c-8505-4734-ba46-629e5de3590d',
    'PENDING',
    NULL
);

-- 8. TASK REMINDER (30 phút trước giờ task)
INSERT INTO task_reminder (
    reminder_id, task_id, remind_before, remind_time, channel, status, created_at
) VALUES
(
    '35a36703-dbda-4e3f-8878-4b600322199d',
    '5450e11b-0b9d-4c78-b427-46de43b44c60',
    INTERVAL '30 minutes',
    '2025-01-02 07:30:00',
    'APP_NOTIFICATION',
    'SCHEDULED',
    '2025-01-01 09:00:00'
),
(
    '06bfc8c9-45a7-44cc-a65d-1296f4f98138',
    'bbeaddc9-8757-4820-8803-baf77678557e',
    INTERVAL '30 minutes',
    '2025-01-02 07:00:00',
    'APP_NOTIFICATION',
    'SCHEDULED',
    '2025-01-01 09:00:00'
),
(
    'c95a1fe4-9a93-4847-943d-d85e8f5fb824',
    '2701ba14-38e4-46d2-a36d-9006be45da68',
    INTERVAL '30 minutes',
    '2025-01-02 08:30:00',
    'APP_NOTIFICATION',
    'SCHEDULED',
    '2025-01-01 09:00:00'
);

-- 9. HEALTH DAILY TRACK
INSERT INTO health_daily_track (
    track_id, patient_id, track_date,
    heart_rate, blood_pressure, blood_sugar, mood_score,
    total_tasks, tasks_completed,
    medication_total, medication_taken,
    stress_level, social_activity, loneliness_score,
    voice_tone, created_at, updated_at
) VALUES (
    '52829afe-5761-496c-b6cd-e8396bb6ea31',
    '4b815548-d435-405a-a7fd-92051c87ef2e',
    '2025-01-02',
    72,
    130,
    6.1,
    4,
    3,
    1,
    1,
    1,
    3,
    40,
    5,
    'STABLE',
    '2025-01-01 09:00:00',
    '2025-01-01 09:00:00'
);

-- 10. NOTIFICATION
INSERT INTO notification (
    notification_id, user_id, title, message,
    task_id, type, is_read, created_at
) VALUES
(
    'de0a88fd-08c9-425d-ad71-d2350be54048',
    '4b815548-d435-405a-a7fd-92051c87ef2e',
    'Nhắc uống thuốc',
    'Đến giờ uống Paracetamol buổi sáng',
    '5450e11b-0b9d-4c78-b427-46de43b44c60',
    'REMINDER',
    FALSE,
    '2025-01-01 09:00:00'
),
(
    'dc18448e-3eb7-44c4-bced-ec3bd4b1e708',
    'fe08799d-6faf-4eb8-80de-9d34269d32c8',
    'Báo cáo task',
    'Bệnh nhân đã hoàn thành 1/3 nhiệm vụ hôm nay',
    NULL,
    'TASK',
    FALSE,
    '2025-01-01 09:00:00'
);
