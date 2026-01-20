-- 1. USERS
INSERT INTO users (user_id, full_name, email, hashed_password, phone, role, created_at, is_active) VALUES
('4b815548-d435-405a-a7fd-92051c87ef2e', 'Nguyen Van A', 'patient@example.com', 'hashed_pw_1', '0900000001', 'PATIENT', '2025-01-01 09:00:00', TRUE),
('fe08799d-6faf-4eb8-80de-9d34269d32c8', 'Tran Thi B', 'caretaker@example.com', 'hashed_pw_2', '0900000002', 'CARETAKER', '2025-01-01 09:00:00', TRUE);

-- 2. PATIENT - CARETAKER RELATION
INSERT INTO patient_caretaker (patient_id, caretaker_id, assigned_at) VALUES
('4b815548-d435-405a-a7fd-92051c87ef2e', 'fe08799d-6faf-4eb8-80de-9d34269d32c8', '2025-01-01 09:00:00');

-- 3. PATIENT PROFILE-- chạy trong postgres hoặc DB khác
CREATE DATABASE memotion;

-- sau đó CONNECT vào memotion
\c memotion;

-- tạo schema
CREATE SCHEMA memotion;

-- set schema mặc định
SET search_path TO memotion;

-- 1. USERS
CREATE TABLE users (
                       user_id        UUID PRIMARY KEY,
                       full_name      VARCHAR(255) NOT NULL,
                       email          VARCHAR(255) UNIQUE NOT NULL,
                       hashed_password varchar(255) NOT NULL,
                       phone          VARCHAR(50),
                       role           VARCHAR(20) NOT NULL CHECK(role IN ('PATIENT', 'CARETAKER')),
                       created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       is_active BOOLEAN DEFAULT TRUE
);

-- 2. PATIENT - CARETAKER RELATION (1-1)
CREATE TABLE patient_caretaker (
                                   patient_id     UUID PRIMARY KEY,
                                   caretaker_id   UUID UNIQUE NOT NULL,   -- đảm bảo 1 caretaker chỉ chăm 1 patient
                                   assigned_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                                   CONSTRAINT fk_patient FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
                                   CONSTRAINT fk_caretaker FOREIGN KEY (caretaker_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 3. PATIENT PROFILE (bệnh, tình trạng) chung
CREATE TABLE patient_profile (
                                 profile_id     UUID PRIMARY KEY,
                                 patient_id     UUID UNIQUE NOT NULL,
                                 gender Varchar(255)CHECK (gender IN ('MALE', 'FEMALE')),
                                 living_arrangement Varchar(255),
                                 BMI_score INT, -- chỉ số cân nặng
                                 MAP_score INT, -- huyết áp trung bình
                                 RHR_score INT, -- nhịp tim
                                 ADL_score INT, -- chức năng sinh hoạt hàng ngày : khả năng tự phục vụ bản thân:  ăn uống
                                 IADL_score INT, -- chức năng thực hành hàng ngày : đi chợ, xem điện thoại
                                 blood_glucose_level INT , -- chỉ số tiểu đường
                                 disease_type   VARCHAR(100) NOT NULL
                                     CHECK (disease_type IN ('PHYSICAL_THERAPY', 'MENTAL_DECLINE', 'LONELINESS')),
                                 condition_note TEXT,
                                 updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                                 CONSTRAINT fk_profile_patient
                                     FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Chi tiết bệnh vật lý ( xướng khớp)
CREATE TABLE patient_physical_therapy (
                                          profile_id       UUID PRIMARY KEY,
                                          pain_location    VARCHAR(255),       -- đầu gối, lưng, vai, cổ...
                                          pain_scale_score INT, -- Thang đo VAS
                                          pain_character   Varchar(255), --(tính chất đau: âm ỉ, nhói, lan…)
                                          pain_assessment varchar(255),-- mức độ đau : ko đau, đau nhẹ, đau vừa, đau không chịu nổi
                                          muscle_tone varchar(255), -- mức độ cứng, khó cử động ở các tư thế gấp và duỗi
                                          muscle_strength varchar(255), --mức độ sức mạnh , cơ yếu
                                          balanced_valuation varchar(255), --có thể đi bình thường, cân bằng : có thể đi lại, rối loạn chức năng thăng bằng
                                          fall_risk varchar(255), -- nguy cơ té ngã
                                          self_stand_ability VARCHAR(100)
                                              CHECK (self_stand_ability IN ('EASY', 'HARD', 'IMPOSSIBLE')),
                                          tug_time INT,
                                          previous_illness varchar(255), -- bệnh nền, bệnh tiền sử
                                          previous_treatments varchar(255), --(điều trị trước: thuốc, phẫu thuật, VLTL…)
                                          daily_actities varchar(255),-- (mô tả chức năng có thể thực hiện: đi, đứng, lên cầu thang…)
                                          doctor_recommended TEXT, -- lời khuyên từ bác sĩ
                                          doctor_treatment_plan TEXT, -- liệu trình từ bác sĩ
                                          note                    TEXT, -- các trạng thái đặc biệt/ riêng biệt (others)
                                              CONSTRAINT fk_pt_profile
                                              FOREIGN KEY (profile_id) REFERENCES patient_profile(profile_id)
                                                  ON DELETE CASCADE
);
-- chi tiết bệnh suy giảm trí nhớ
CREATE TABLE patient_mental_decline (
                                        profile_id  UUID PRIMARY KEY,
                                        MMSE_score INT, -- thang đo điểm về suy giảm trí nhớ và suy giảm trí tuệ
                                        previous_illness varchar(255), -- bệnh nền, bệnh tiền sử
                                        previous_treatments varchar(255), --(điều trị trước: thuốc, phẫu thuật, VLTL…)
                                        functional_assessment_staging_test_score INT, --(Functional Assessment Staging Test): thang “giai đoạn chức năng” cho bệnh Alzheimer
                                        memory_issue       VARCHAR(255),   -- mô tả: hay quên tên người thân, quên cuộc hẹn...
                                        orientation_issue  VARCHAR(255),   -- mô tả: lạc đường, nhầm ngày tháng...
                                        community_affairs  Varchar(255), -- mô tả về hoạt động cộng đồng: ít tham gia hoạt động, tham gia bình thường
                                        home_relationship Varchar(255), -- mối quan hệ và chức năng trong gia đình
                                        daily_function_can_do     VARCHAR(255),   -- mô tả các hoạt động thường ngày có thể thực hiện
                                        daily_function_need_help VARCHAR(255), -- mô tả: cần trợ giúp tắm rửa, quên tắt bếp...
                                        behavior_change    VARCHAR(255),   -- mô tả thay đổi hành vi

                                        doctor_recommended TEXT,-- lời khuyên từ bác sĩ
                                        doctor_treatment_plan TEXT,-- liệu trình từ bác sĩ
                                        note                    TEXT,-- các trạng thái đặc biệt/ riêng biệt (others)

                                        CONSTRAINT fk_md_profile
                                            FOREIGN KEY (profile_id) REFERENCES patient_profile(profile_id)
                                                ON DELETE CASCADE
);


-- chi tiết bệnh cô đơn
CREATE TABLE patient_loneliness (
                                    profile_id          UUID PRIMARY KEY,
                                    previous_illness varchar(255), -- bệnh nền, bệnh tiền sử
                                    lsns6_family_score INT, -- điểm đánh giá gia đình theo LSNS6
                                    lsns6_friends_score INT, -- điểm đánh giá bạn bè theo LSNS6
                                    ucla_loneliness_score INT,
                                    gds15_score INT,
                                    mood_status             VARCHAR(50),    -- Hay buồn, Vui vẻ, Cô đơn, Lo âu..
                                    behavior_change_note    VARCHAR(255),   -- mô tả thay đổi hành vi
                                    note                TEXT,

                                    CONSTRAINT fk_lonely_profile
                                        FOREIGN KEY (profile_id) REFERENCES patient_profile(profile_id)
                                            ON DELETE CASCADE
);



-- CARE PLAN (Lộ trình – luôn chỉ 1 active)
CREATE TABLE care_plan (
                           care_plan_id   UUID PRIMARY KEY,
                           patient_id     UUID NOT NULL UNIQUE,  -- chỉ 1 care_plan active cho mỗi bệnh nhân
                           caretaker_id   UUID NOT NULL,
                           created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                           CONSTRAINT fk_plan_patient FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE,
                           CONSTRAINT fk_plan_caretaker FOREIGN KEY (caretaker_id) REFERENCES users(user_id) ON DELETE CASCADE
);
--  SUBTABLE: MEDICATION TASK DETAILS
CREATE TABLE medication_library (
                                    medication_id UUID PRIMARY KEY,
                                    name          VARCHAR(255),
                                    description  TEXT,
                                    dosage        VARCHAR(255),   -- 1 viên, 5ml...
                                    frequency_per_day INT,
                                    notes         TEXT,
                                    image_path VARCHAR(255)
);

-- SUBTABLE: NUTRITION TASK DETAILS
CREATE TABLE nutrition_library (
                                   nutrition_id UUID PRIMARY KEY,
                                   name         VARCHAR(255),
                                   calories     INT,
                                   description  TEXT,
                                   meal_type    VARCHAR(50),
                                   image_path VARCHAR(255)
);

--SUBTABLE: EXERCISE TASK DETAILS
CREATE TABLE exercise_library (
                                  exercise_id UUID PRIMARY KEY,
                                  name        VARCHAR(255) NOT NULL,
                                  target_body_region VARCHAR(255), -- vùng cơ thể tập trung chính
                                  description TEXT,
                                  duration_minutes INT,          -- thời gian bài tập
                                  difficulty_level INT CHECK (difficulty_level BETWEEN 1 AND 5),
                                  video_path VARCHAR(255)
);

--TASK (Task chung)
CREATE TABLE task (
                      task_id        UUID PRIMARY KEY,
                      care_plan_id   UUID NOT NULL,
                      owner_type     VARCHAR(20) NOT NULL CHECK(owner_type IN ('PATIENT', 'CARETAKER')),
                      title          VARCHAR(255) NOT NULL,
                      description    TEXT,
                      task_date      DATE NOT NULL,
                      task_time      TIME NOT NULL,
                      task_type      VARCHAR(20) NOT NULL CHECK(task_type IN ('MEDICATION', 'NUTRITION', 'EXERCISE')),
                      medication_id UUID,
                      nutrition_id UUID,
                      exercise_id UUID,
                      status         VARCHAR(20) DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'DONE', 'SKIPPED')),
                      linked_task_id UUID, -- task của caretaker ↔ task của patient

                      CONSTRAINT fk_task_plan FOREIGN KEY (care_plan_id) REFERENCES care_plan(care_plan_id) ON DELETE CASCADE,
                      CONSTRAINT fk_link_task FOREIGN KEY (linked_task_id) REFERENCES task(task_id) ON DELETE SET NULL,
                      CONSTRAINT fk_task_nutrition FOREIGN KEY (nutrition_id) REFERENCES nutrition_library(nutrition_id) ON DELETE SET NULL,
                      CONSTRAINT fk_task_medication  FOREIGN KEY (medication_id) REFERENCES medication_library(medication_id) ON DELETE SET NULL,
                      CONSTRAINT fk_task_exercise FOREIGN KEY (exercise_id) REFERENCES exercise_library(exercise_id) ON DELETE SET NULL
);


CREATE TABLE task_reminder (
                               reminder_id     UUID PRIMARY KEY,
                               task_id         UUID NOT NULL,
                               remind_before   INTERVAL NOT NULL,  -- ví dụ '30 minutes', '2 hours'
                               remind_time     TIMESTAMP,          -- hệ thống tính ra reminder_time từ task_date + task_time - remind_before
                               channel         VARCHAR(50) NOT NULL
                                   CHECK(channel IN ('APP_NOTIFICATION', 'SMS', 'VOICE_CALL')),
                               status          VARCHAR(20) DEFAULT 'SCHEDULED'
                                   CHECK(status IN ('SCHEDULED', 'SENT', 'CANCELLED')),
                               created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                               CONSTRAINT fk_reminder_task FOREIGN KEY (task_id)
                                   REFERENCES task(task_id) ON DELETE CASCADE
);

CREATE TABLE health_daily_track (
                                    track_id          UUID PRIMARY KEY,
                                    patient_id        UUID NOT NULL,
                                    track_date        DATE NOT NULL,   -- ngày theo dõi, 1 ngày chỉ có 1 record
                                    heart_rate        INT,             -- nhịp tim
                                    blood_pressure INT,            -- huyết áp tâm thu
                                    blood_sugar       FLOAT,           -- đường huyết (tuỳ bệnh)
                                    mood_score        INT CHECK (mood_score BETWEEN 1 AND 5), -- đánh giá cảm xúc

                                    total_tasks       INT DEFAULT 0,   -- tổng số task trong ngày
                                    tasks_completed   INT DEFAULT 0,   -- số task đã hoàn thành
                                    medication_total  INT DEFAULT 0,   -- tổng số thuốc cần uống
                                    medication_taken  INT DEFAULT 0,   -- số thuốc đã uống
                                    stress_level    INT CHECK(stress_level BETWEEN 0 AND 10), -- mức căng thẳng

                                    social_activity INT CHECK(social_activity BETWEEN 0 AND 100), -- giao tiếp xã hội
                                    loneliness_score INT CHECK(loneliness_score BETWEEN 0 AND 10), -- mức cô đơn
                                    voice_tone      VARCHAR(50) NULL, -- phân tích giọng nói : run, lặp từ , ...
                                    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                                    UNIQUE(patient_id, track_date),

                                    CONSTRAINT fk_health_track_patient
                                        FOREIGN KEY (patient_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE TABLE notification (
                              notification_id   UUID PRIMARY KEY,
                              user_id           UUID NOT NULL,         -- người bệnh hoặc người chăm sóc
                              title             VARCHAR(255) NOT NULL,
                              message           TEXT NOT NULL,
                              task_id           UUID,                  -- nếu notification liên quan tới 1 task
                              type              VARCHAR(50) NOT NULL    -- REMINDER, SYSTEM, HEALTH_ALERT, ...
                                  CHECK(type IN ('REMINDER', 'SYSTEM', 'HEALTH', 'TASK')),
                              is_read           BOOLEAN DEFAULT FALSE,
                              created_at        TIMESTAMP DEFAULT NOW(),

                              FOREIGN KEY (user_id) REFERENCES users(user_id),
                              FOREIGN KEY (task_id) REFERENCES task(task_id)
);

-- 1. Tạo 3 trường mới trong patient_profile (quan hệ 1-1)
ALTER TABLE patient_profile
    ADD COLUMN physical_therapy_id UUID UNIQUE,
    ADD COLUMN mental_decline_id UUID UNIQUE,
    ADD COLUMN loneliness_id UUID UNIQUE;

-- 2. Xóa các FK cũ từ 3 bảng detail
ALTER TABLE patient_physical_therapy
    DROP CONSTRAINT IF EXISTS fk_pt_profile;

ALTER TABLE patient_mental_decline
    DROP CONSTRAINT IF EXISTS fk_md_profile;

ALTER TABLE patient_loneliness
    DROP CONSTRAINT IF EXISTS fk_lonely_profile;

-- 3. Tạo FK mới từ patient_profile đến 3 bảng detail
ALTER TABLE patient_profile
    ADD CONSTRAINT fk_profile_physical_therapy
        FOREIGN KEY (physical_therapy_id) REFERENCES patient_physical_therapy(profile_id)
            ON DELETE SET NULL;

ALTER TABLE patient_profile
    ADD CONSTRAINT fk_profile_mental_decline
        FOREIGN KEY (mental_therapy_id) REFERENCES patient_mental_decline(profile_id)
            ON DELETE SET NULL;

ALTER TABLE patient_profile
    ADD CONSTRAINT fk_profile_loneliness
        FOREIGN KEY (loneliness_id) REFERENCES patient_loneliness(profile_id)
            ON DELETE SET NULL;

-- 4. Tạo FK ngược lại từ 3 bảng detail về patient_profile (tùy chọn - đảm bảo tính toàn vẹn)
ALTER TABLE patient_physical_therapy
    ADD CONSTRAINT fk_pt_profile_new
        FOREIGN KEY (profile_id) REFERENCES patient_profile(profile_id)
            ON DELETE CASCADE;

ALTER TABLE patient_mental_decline
    ADD CONSTRAINT fk_md_profile_new
        FOREIGN KEY (profile_id) REFERENCES patient_profile(profile_id)
            ON DELETE CASCADE;

ALTER TABLE patient_loneliness
    ADD CONSTRAINT fk_lonely_profile_new
        FOREIGN KEY (profile_id) REFERENCES patient_profile(profile_id)
            ON DELETE CASCADE;
-- Add is_first_login column to users table
ALTER TABLE memotion.users 
ADD COLUMN is_first_login BOOLEAN DEFAULT true NOT NULL;