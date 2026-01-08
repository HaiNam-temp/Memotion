from fastapi import Depends, HTTPException
import logging
from app.repository.repo_patient_profile import PatientProfileRepository
from app.repository.repo_user import UserRepository
from app.schemas.sche_patient_profile import PatientProfileCreateRequest, PhysicalTherapyCreateRequest, PatientProfileUpdateRequest, PhysicalTherapyUpdateRequest
from app.models.model_patient_profile import PatientProfile
from app.models.model_patient_physical_therapy import PatientPhysicalTherapy
from app.models.model_user import User
from app.helpers.enums import UserRole

logger = logging.getLogger(__name__)

class PatientProfileService:
    def __init__(self, profile_repo: PatientProfileRepository = Depends(), user_repo: UserRepository = Depends()):
        self.profile_repo = profile_repo
        self.user_repo = user_repo

    def create_patient_profile(self, data: PatientProfileCreateRequest, current_user: User):
        # Check if current user is a caretaker
        if current_user.role != UserRole.CARETAKER.value:
            raise Exception("Only caretakers can create patient profiles")

        # Find the patient that this caretaker is responsible for
        assigned_patient = self.user_repo.get_assigned_patient(current_user.user_id)
        if not assigned_patient:
            raise Exception("No patient assigned to this caretaker")

        # Check if the assigned patient already has a profile
        if self.profile_repo.get_profile_by_patient_id(assigned_patient.user_id):
            raise Exception("Patient profile already exists")

        # Create the profile for the assigned patient
        new_profile = PatientProfile(
            patient_id=assigned_patient.user_id,
            gender=data.gender.value if data.gender else None,
            living_arrangement=data.living_arrangement,
            bmi_score=data.bmi_score,
            map_score=data.map_score,
            rhr_score=data.rhr_score,
            adl_score=data.adl_score,
            iadl_score=data.iadl_score,
            blood_glucose_level=data.blood_glucose_level,
            disease_type=data.disease_type.value,
            condition_note=data.condition_note
        )
        return self.profile_repo.create_profile(new_profile)

    def get_patient_profile(self, current_user: User):
        profile = self.profile_repo.get_profile_by_patient_id(current_user.user_id)
        if not profile:
            raise Exception("Patient profile not found")
        return profile

    def update_patient_profile(self, data: PatientProfileUpdateRequest, current_user: User):
        profile = self.profile_repo.get_profile_by_patient_id(current_user.user_id)
        if not profile:
            raise Exception("Patient profile not found")
        
        if data.gender is not None:
            profile.gender = data.gender.value
        if data.living_arrangement is not None:
            profile.living_arrangement = data.living_arrangement
        if data.bmi_score is not None:
            profile.bmi_score = data.bmi_score
        if data.map_score is not None:
            profile.map_score = data.map_score
        if data.rhr_score is not None:
            profile.rhr_score = data.rhr_score
        if data.adl_score is not None:
            profile.adl_score = data.adl_score
        if data.iadl_score is not None:
            profile.iadl_score = data.iadl_score
        if data.blood_glucose_level is not None:
            profile.blood_glucose_level = data.blood_glucose_level
        if data.disease_type is not None:
            profile.disease_type = data.disease_type.value
        if data.condition_note is not None:
            profile.condition_note = data.condition_note
            
        return self.profile_repo.update_profile(profile)

    def delete_patient_profile(self, current_user: User):
        profile = self.profile_repo.get_profile_by_patient_id(current_user.user_id)
        if not profile:
            raise Exception("Patient profile not found")
        
        # Check if current user is the patient or caretaker
        if current_user.role == UserRole.PATIENT.value:
            # Patient can delete their own profile
            pass
        elif current_user.role == UserRole.CARETAKER.value:
            # Caretaker can delete profile of their assigned patient
            assigned_patient = self.user_repo.get_assigned_patient(current_user.user_id)
            if not assigned_patient or assigned_patient.user_id != profile.patient_id:
                raise Exception("Unauthorized to delete this profile")
        else:
            raise Exception("Unauthorized role")
        
        self.profile_repo.delete_profile(profile)

    def create_physical_therapy_profile(self, data: PhysicalTherapyCreateRequest, current_user: User):
        # Check if current user is a caretaker
        if current_user.role != UserRole.CARETAKER.value:
            raise Exception("Only caretakers can create physical therapy profiles")

        # Find the patient that this caretaker is responsible for
        assigned_patient = self.user_repo.get_assigned_patient(current_user.user_id)
        if not assigned_patient:
            raise Exception("No patient assigned to this caretaker")

        # Get existing profile for the assigned patient
        profile = self.profile_repo.get_profile_by_patient_id(assigned_patient.user_id)
        if not profile:
            raise Exception("Patient profile not found. Please create a general profile first.")
        
        if profile.disease_type != 'PHYSICAL_THERAPY':
             raise Exception("Patient disease type is not PHYSICAL_THERAPY")

        # Check if physical therapy profile already exists
        if profile.physical_therapy_id:
             raise Exception("Physical therapy profile already exists")

        logger.info(f"Creating physical therapy profile for patient {assigned_patient.user_id} with profile_id {profile.profile_id}")

        new_therapy = PatientPhysicalTherapy(
            profile_id=profile.profile_id,  # Use the patient profile's ID as foreign key
            pain_location=data.pain_location,
            pain_scale_score=data.pain_scale_score,
            pain_character=data.pain_character,
            pain_assessment=data.pain_assessment,
            muscle_tone=data.muscle_tone,
            muscle_strength=data.muscle_strength,
            balanced_valuation=data.balanced_valuation,
            fall_risk=data.fall_risk,
            self_stand_ability=data.self_stand_ability,
            tug_time=data.tug_time,
            previous_illness=data.previous_illness,
            previous_treatments=data.previous_treatments,
            daily_actities=data.daily_actities,
            doctor_recommended=data.doctor_recommended,
            doctor_treatment_plan=data.doctor_treatment_plan,
            note=data.note
        )
        created_therapy = self.profile_repo.create_physical_therapy(new_therapy)
        
        # Update profile with physical_therapy_id (same as profile_id since it's the foreign key)
        profile.physical_therapy_id = profile.profile_id
        self.profile_repo.update_profile(profile)
        
        logger.info(f"Successfully created physical therapy profile with id {profile.profile_id}")
        return created_therapy

    def get_physical_therapy_profile(self, current_user: User):
        therapy = self.profile_repo.get_physical_therapy_by_patient_id(current_user.user_id)
        if not therapy:
            raise Exception("Physical therapy profile not found")
        return therapy

    def update_physical_therapy_profile(self, data: PhysicalTherapyUpdateRequest, current_user: User):
        profile = self.profile_repo.get_profile_by_patient_id(current_user.user_id)
        if not profile:
            raise Exception("Patient profile not found")
        
        therapy = self.profile_repo.get_physical_therapy_by_profile_id(profile.profile_id)
        if not therapy:
            raise Exception("Physical therapy profile not found")

        if data.pain_location is not None:
            therapy.pain_location = data.pain_location
        if data.pain_scale_score is not None:
            therapy.pain_scale_score = data.pain_scale_score
        if data.pain_character is not None:
            therapy.pain_character = data.pain_character
        if data.pain_assessment is not None:
            therapy.pain_assessment = data.pain_assessment
        if data.muscle_tone is not None:
            therapy.muscle_tone = data.muscle_tone
        if data.muscle_strength is not None:
            therapy.muscle_strength = data.muscle_strength
        if data.balanced_valuation is not None:
            therapy.balanced_valuation = data.balanced_valuation
        if data.fall_risk is not None:
            therapy.fall_risk = data.fall_risk
        if data.self_stand_ability is not None:
            therapy.self_stand_ability = data.self_stand_ability
        if data.tug_time is not None:
            therapy.tug_time = data.tug_time
        if data.previous_illness is not None:
            therapy.previous_illness = data.previous_illness
        if data.previous_treatments is not None:
            therapy.previous_treatments = data.previous_treatments
        if data.daily_actities is not None:
            therapy.daily_actities = data.daily_actities
        if data.doctor_recommended is not None:
            therapy.doctor_recommended = data.doctor_recommended
        if data.doctor_treatment_plan is not None:
            therapy.doctor_treatment_plan = data.doctor_treatment_plan
        if data.note is not None:
            therapy.note = data.note
            
        return self.profile_repo.update_physical_therapy(therapy)

    def delete_physical_therapy_profile(self, current_user: User):
        profile = self.profile_repo.get_profile_by_patient_id(current_user.user_id)
        if not profile:
            raise Exception("Patient profile not found")
        
        therapy = self.profile_repo.get_physical_therapy_by_profile_id(profile.profile_id)
        if not therapy:
            raise Exception("Physical therapy profile not found")

        # Check if current user is the patient or caretaker
        if current_user.role == UserRole.PATIENT.value:
            # Patient can delete their own profile
            pass
        elif current_user.role == UserRole.CARETAKER.value:
            # Caretaker can delete profile of their assigned patient
            assigned_patient = self.user_repo.get_assigned_patient(current_user.user_id)
            if not assigned_patient or assigned_patient.user_id != profile.patient_id:
                raise Exception("Unauthorized to delete this profile")
        else:
            raise Exception("Unauthorized role")
        
        self.profile_repo.delete_physical_therapy(therapy)
        
        # Update profile to remove physical_therapy_id
        profile.physical_therapy_id = None
        self.profile_repo.update_profile(profile)
