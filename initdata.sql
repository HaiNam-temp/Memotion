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


INSERT INTO medication_library (medication_id, name, description, dosage, frequency_per_day, notes, image_path) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Ibuprofen 400mg', 'Giảm đau, chống viêm, hạ sốt', '1 viên', 3, 'Uống sau ăn, tránh dạ dày rỗng', '/images/meds/ibuprofen.png'),
('b2c3d4e5-f6g7-8901-bcde-f2345678901', 'Aspirin 500mg', 'Giảm đau, chống viêm, ngừa đông máu', '1 viên', 4, 'Không dùng cho trẻ em dưới 16 tuổi', '/images/meds/aspirin.png'),
('c3d4e5f6-g7h8-9012-cdef-3456789012', 'Naproxen 250mg', 'Giảm đau dài hạn, viêm khớp', '1 viên', 2, 'Uống với nước đầy đủ', '/images/meds/naproxen.png'),
('d4e5f6g7-h8i9-0123-def0-4567890123', 'Amoxicillin 500mg', 'Kháng sinh trị nhiễm khuẩn hô hấp', '1 viên', 3, 'Dùng đủ liệu trình 7 ngày', '/images/meds/amoxicillin.png');


INSERT INTO nutrition_library (nutrition_id, name, calories, description, meal_type, image_path) VALUES
('e5f6g7h8-i9j0-1234-ef01-5678901234', 'Salad gà nướng', 350, 'Bữa trưa giàu protein, ít carb', 'LUNCH', '/images/food/chicken_salad.png'),
('f6g7h8i9-j0k1-2345-fg12-6789012345', 'Cá hồi áp chảo', 400, 'Omega-3 tốt cho tim, bữa tối nhẹ', 'DINNER', '/images/food/salmon.png'),
('g7h8i9j0-k1l2-3456-gh23-7890123456', 'Sinh tố chuối việt quất', 220, 'Bữa phụ giàu vitamin, chất xơ', 'SNACK', '/images/food/smoothie.png'),
('h8i9j0k1-l2m3-4567-hi34-8901234567', 'Khoai lang luộc', 150, 'Nguồn năng lượng chậm, tốt cho tiêu hóa', 'BREAKFAST', '/images/food/sweet_potato.png');


INSERT INTO exercise_library (exercise_id, name, target_body_region, description, duration_minutes, difficulty_level, video_path) VALUES
('i9j0k1l2-m3n4-5678-ij45-9012345678', 'Plank cơ bản', 'Cơ bụng', 'Nằm sấp chống khuỷu tay, giữ thẳng lưng 20-30 giây, 3 hiệp', 10, 1, '/videos/exercise/plank.mp4'),
('j0k1l2m3-n4o5-6789-jk56-0123456789', 'Gánh tạ vai', 'Vai và lưng', 'Đứng thẳng gánh tạ ngang vai, đẩy lên trời 10-12 lần', 20, 3, '/videos/exercise/shoulder_press.mp4'),
('k1l2m3n4-o5p6-7890-kl67-1234567890', 'Đi bộ nhanh', 'Toàn thân', 'Đi bộ tốc độ 5km/h ngoài trời hoặc máy chạy', 30, 1, '/videos/exercise/walking.mp4'),
('l2m3n4o5-p6q7-8901-lm78-2345678901', 'Gập bụng bicycle', 'Cơ bụng chéo', 'Nằm ngửa đạp xe đạp trên không, chạm khuỷu tay vào gối đối diện 15 lần mỗi bên', 15, 2, '/videos/exercise/bicycle_crunch.mp4');


INSERT INTO medication_library (medication_id, name, description, dosage, frequency_per_day, notes, image_path) VALUES
('e5f67890-1234-5678-9abc-def012345678', 'Omeprazole 20mg', 'Giảm axit dạ dày, trị loét', '1 viên', 1, 'Uống trước ăn sáng 30 phút', '/images/meds/omeprazole.png'),
('f6789012-3456-7890-abcd-ef1234567890', 'Cetirizine 10mg', 'Kháng histamin, trị dị ứng', '1 viên', 1, 'Uống buổi tối, gây buồn ngủ', '/images/meds/cetirizine.png'),
('90123456-7890-abcd-ef12-34567890abcd', 'Metformin 500mg', 'Kiểm soát đường huyết tiểu đường', '1 viên', 2, 'Uống cùng bữa ăn', '/images/meds/metformin.png'),
('23456789-0abc-def12-3456-7890abcdef12', 'Amlodipine 5mg', 'Hạ huyết áp, giãn mạch', '1 viên', 1, 'Uống sáng, theo dõi huyết áp', '/images/meds/amlodipine.png'),
('567890ab-cdef-1234-5678-90abcdef1234', 'Simvastatin 20mg', 'Giảm cholesterol, ngừa tim mạch', '1 viên', 1, 'Uống buổi tối', '/images/meds/simvastatin.png');


INSERT INTO nutrition_library (nutrition_id, name, calories, description, meal_type, image_path) VALUES
('12345678-90ab-cdef-1234-567890abcdef12', 'Trứng luộc rau củ', 250, 'Protein cao, bữa sáng no lâu', 'BREAKFAST', '/images/food/boiled_eggs.png'),
('4567890a-bcde-f123-4567-890abcde1234', 'Gà xào bông cải', 320, 'Ít dầu, giàu chất xơ bữa trưa', 'LUNCH', '/images/food/chicken_broccoli.png'),
('7890abcd-ef12-3456-7890-bcde12345678', 'Cá ngừ salad', 280, 'Omega-3, bữa tối nhẹ nhàng', 'DINNER', '/images/food/tuna_salad.png'),
('bcdef123-4567-890a-bcde-f1234567890a', 'Hạt óc chó yogurt', 200, 'Chất béo lành mạnh, bữa phụ', 'SNACK', '/images/food/nuts_yogurt.png'),
('23456789-0abc-def12-3456-7890abcdef12', 'Bánh mì nguyên cám', 160, 'Carb tốt, thay cơm sáng', 'BREAKFAST', '/images/food/wholegrain_bread.png');


INSERT INTO exercise_library (exercise_id, name, target_body_region, description, duration_minutes, difficulty_level, video_path) VALUES
('34567890-abcdef-1234-5678-90abcdef1234', 'Squats cơ bản', 'Chân và mông', 'Chân dang rộng vai, ngồi xổm như ngồi ghế 12-15 lần, 3 hiệp', 15, 2, '/videos/exercise/squats.mp4'),
('67890abc-def12-3456-7890-abcdef123456', 'Chống đẩy tường', 'Ngực và tay', 'Đứng cách tường, chống đẩy 10 lần cho người mới', 10, 1, '/videos/exercise/wall_pushups.mp4'),
('90abcde1-2345-6789-0abc-def1234567890', 'Yoga cây cầu', 'Lưng dưới và hông', 'Nằm ngửa nâng hông, giữ 20 giây, 5 lần', 12, 2, '/videos/exercise/bridge_pose.mp4'),
('abcde123-4567-890a-bcde-f12345678901', 'Nhảy dây', 'Toàn thân cardio', 'Nhảy chậm 200 cái, nghỉ giữa hiệp', 20, 2, '/videos/exercise/jump_rope.mp4'),
('cdef1234-5678-90ab-cdef-123456789abc', 'Giãn cơ vai', 'Vai và cổ', 'Xoay vai nhẹ nhàng, kéo tay qua ngực 10 lần mỗi bên', 8, 1, '/videos/exercise/shoulder_stretch.mp4');


INSERT INTO medication_library (medication_id, name, description, dosage, frequency_per_day, notes, image_path) VALUES
('1a2b3c4d-5e6f-7890-abcd-ef1234567890', 'Loratadine 10mg', 'Trị sổ mũi dị ứng, ngứa', '1 viên', 1, 'Uống bất kỳ lúc nào, không buồn ngủ', '/images/meds/loratadine.png'),
('2b3c4d5e-6f78-9012-bcde-f23456789012', 'Vitamin D3 1000IU', 'Bổ sung vitamin D, xương chắc khỏe', '1 viên', 1, 'Uống sau ăn có chất béo', '/images/meds/vitamin_d.png'),
('3c4d5e6f-7890-1234-cdef-345678901234', 'Calcium 500mg', 'Bổ sung canxi, ngừa loãng xương', '1 viên', 2, 'Kết hợp vitamin D', '/images/meds/calcium.png'),
('4d5e6f78-9012-3456-def0-456789012345', 'Vitamin C 500mg', 'Tăng đề kháng, chống oxy hóa', '1 viên', 2, 'Uống lúc đói tốt hơn', '/images/meds/vitamin_c.png'),
('5e6f7890-1234-5678-ef01-567890123456', 'Magnesium 250mg', 'Giảm chuột rút, ngủ ngon', '1 viên', 1, 'Uống trước ngủ', '/images/meds/magnesium.png');


INSERT INTO nutrition_library (nutrition_id, name, calories, description, meal_type, image_path) VALUES
('6f789012-3456-7890-fg12-678901234567', 'Sinh tố protein chuối', 280, 'Bữa sáng gym, phục hồi cơ bắp', 'BREAKFAST', '/images/food/protein_shake.png'),
('78901234-5678-90ab-gh23-789012345678', 'Đậu phụ xào rau muống', 260, 'Protein thực vật, bữa trưa chay', 'LUNCH', '/images/food/tofu_stirfry.png'),
('89012345-6789-0abc-hi34-890123456789', 'Tôm hấp bông cải', 300, 'Ít calo, giàu kẽm bữa tối', 'DINNER', '/images/food/steamed_shrimp.png'),
('90123456-7890-abcd-ij45-901234567890', 'Táo và bơ đậu phộng', 190, 'Chất béo tốt, bữa xế no lâu', 'SNACK', '/images/food/apple_pb.png'),
('01234567-890a-bcde-jk56-012345678901', 'Sữa chua Hy Lạp', 120, 'Probiotic, hỗ trợ tiêu hóa', 'SNACK', '/images/food/greek_yogurt.png');


INSERT INTO exercise_library (exercise_id, name, target_body_region, description, duration_minutes, difficulty_level, video_path) VALUES
('12345678-90ab-cdef-kl67-123456789012', 'Lunges xen kẽ', 'Chân và mông', 'Bước chân dài, gối trước 90 độ, 10 lần mỗi chân', 15, 2, '/videos/exercise/lunges.mp4'),
('23456789-0abc-def1-lm78-234567890123', 'Chống đẩy gối', 'Ngực tay triceps', 'Quỳ gối chống đẩy, 8-12 lần cho nữ/mới tập', 12, 1, '/videos/exercise/knee_pushups.mp4'),
('34567890-abcdef-123-lm78-345678901234', 'Superman lưng dưới', 'Lưng và mông', 'Nằm sấp nâng tay chân cùng lúc, giữ 5 giây, 12 lần', 10, 1, '/videos/exercise/superman.mp4'),
('4567890a-bcde-f123-n89-456789012345', 'Mountain climbers', 'Toàn thân cardio', 'Tư plank, kéo gối luân phiên nhanh 30 giây x 4', 15, 3, '/videos/exercise/mountain_climber.mp4'),
('567890ab-cdef-1234-op90-567890123456', 'Xoay hông đứng', 'Hông và eo', 'Tay chống hông, xoay hông tròn 20 lần mỗi chiều', 8, 1, '/videos/exercise/hip_circles.mp4');
