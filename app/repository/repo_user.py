from typing import Optional
from fastapi import Depends
from app.db.base import get_db
from app.models.model_user import User
from app.models.model_patient_caretaker import PatientCaretaker

class UserRepository:
    def __init__(self, db_session = Depends(get_db)):
        self.db = db_session

    def get_all(self):
        return self.db.query(User).all()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.user_id == user_id).first()

    def create(self, user_data: User) -> User:
        self.db.add(user_data)
        self.db.commit()
        self.db.refresh(user_data)
        return user_data

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_patient_caretaker(self, patient_id, caretaker_id):
        patient_caretaker = PatientCaretaker(
            patient_id=patient_id,
            caretaker_id=caretaker_id
        )
        self.db.add(patient_caretaker)
        self.db.commit()
        return patient_caretaker

    def get_patient_id_by_caretaker(self, caretaker_id: str) -> Optional[str]:
        result = self.db.query(PatientCaretaker.patient_id).filter(PatientCaretaker.caretaker_id == caretaker_id).first()
        return result[0] if result else None

    def get_assigned_patient(self, caretaker_id: str) -> Optional[User]:
        patient_id = self.get_patient_id_by_caretaker(caretaker_id)
        if patient_id:
            return self.get_by_id(patient_id)
        return None
