"""
Repository for Care Plan operations.
Handles database queries for care_plan table.
"""
import logging
from typing import Optional
from uuid import UUID
from fastapi_sqlalchemy import db
from app.models.model_care_plan import CarePlan

logger = logging.getLogger(__name__)


class CarePlanRepository:
    """Repository for CarePlan entity."""

    def __init__(self, db_session = None):
        """
        Initialize repository.

        Args:
            db_session: Database session. If None, uses fastapi_sqlalchemy db.session.
        """
        self.db = db_session or db.session

    def get_by_id(self, care_plan_id: UUID) -> Optional[CarePlan]:
        """
        Get care plan by ID.

        Args:
            care_plan_id: Care plan UUID.

        Returns:
            CarePlan object or None.
        """
        return self.db.query(CarePlan).filter(CarePlan.care_plan_id == care_plan_id).first()

    def get_by_patient_id(self, patient_id: UUID) -> Optional[CarePlan]:
        """
        Get care plan by patient ID.

        Args:
            patient_id: Patient UUID.

        Returns:
            CarePlan object or None.
        """
        return self.db.query(CarePlan).filter(CarePlan.patient_id == patient_id).first()

    def create(self, care_plan: CarePlan) -> CarePlan:
        """
        Create new care plan.

        Args:
            care_plan: CarePlan object to create.

        Returns:
            Created CarePlan with generated ID.
        """
        self.db.add(care_plan)
        self.db.commit()
        self.db.refresh(care_plan)
        logger.info(f"Created care plan: {care_plan.care_plan_id}")
        return care_plan

    def update(self, care_plan: CarePlan) -> CarePlan:
        """
        Update existing care plan.

        Args:
            care_plan: CarePlan object with updated fields.

        Returns:
            Updated CarePlan.
        """
        self.db.commit()
        self.db.refresh(care_plan)
        logger.info(f"Updated care plan: {care_plan.care_plan_id}")
        return care_plan

    def delete(self, care_plan_id: UUID) -> bool:
        """
        Delete care plan by ID.

        Args:
            care_plan_id: Care plan UUID.

        Returns:
            True if deleted, False if not found.
        """
        care_plan = self.get_by_id(care_plan_id)
        if care_plan:
            self.db.delete(care_plan)
            self.db.commit()
            logger.info(f"Deleted care plan: {care_plan_id}")
            return True
        return False

    def exists_for_patient(self, patient_id: UUID) -> bool:
        """
        Check if care plan exists for patient.

        Args:
            patient_id: Patient UUID.

        Returns:
            True if exists, False otherwise.
        """
        count = self.db.query(CarePlan).filter(CarePlan.patient_id == patient_id).count()
        return count > 0
