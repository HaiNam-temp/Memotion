from fastapi import Depends
from typing import List, Dict, Any
import os
from app.repository.repo_medication_library import MedicationLibraryRepository
from app.schemas.sche_medication_library import MedicationLibraryCreateRequest, MedicationLibraryResponse
from app.ai_agent.medication_scan_agent import MedicationScanAgent
from app.core.config import settings, BASE_DIR
from app.helpers.exception_handler import CustomException

class MedicationLibraryService:
    def __init__(self, medication_repo: MedicationLibraryRepository = Depends()):
        self.medication_repo = medication_repo
        self.scan_agent = MedicationScanAgent()

    def create_medication(self, medication_data: MedicationLibraryCreateRequest) -> MedicationLibraryResponse:
        medication = self.medication_repo.create(medication_data)
        return MedicationLibraryResponse.from_orm(medication)

    def get_all_medications(self, limit: int = 50) -> List[MedicationLibraryResponse]:
        medications = self.medication_repo.get_all(limit=limit)
        return [MedicationLibraryResponse.from_orm(m) for m in medications]

    def delete_medication(self, medication_id: str) -> bool:
        return self.medication_repo.delete(medication_id)

    def scan_and_process_medication_image(self, image_path: str) -> Dict[str, Any]:
        """
        Scan medication image and process the result.
        If medication found and not in library, add it with image.

        Args:
            image_path: Absolute path to the uploaded image file.

        Returns:
            Medication data or error message.
        """
        # Scan the image
        scan_result = self.scan_agent.scan_medication_image(image_path)

        if "error" in scan_result:
            raise CustomException(http_code=404, code='404', message="Thuốc Not found")
        elif "agent_error" in scan_result:
            raise CustomException(http_code=500, code='500', message=scan_result["agent_error"])

        # Extract medication info
        medication_data = {
            "name": scan_result.get("name", ""),
            "description": scan_result.get("description", ""),
            "dosage": scan_result.get("dosage", ""),
            "frequency_per_day": scan_result.get("frequency_per_day"),
            "notes": scan_result.get("notes", ""),
            "image_path": None  # Will be set after upload
        }

        # Check if medication exists by name
        existing_medication = self.medication_repo.get_by_name_like(medication_data["name"])
        if existing_medication:
            # Return existing medication
            return MedicationLibraryResponse.from_orm(existing_medication)

        # Medication not found, create new one
        # First, upload the image to get image_path
        upload_result = self._upload_medication_image(image_path)
        medication_data["image_path"] = upload_result

        # Create medication in database
        create_request = MedicationLibraryCreateRequest(**medication_data)
        new_medication = self.medication_repo.create(create_request)

        return MedicationLibraryResponse.from_orm(new_medication)

    def _upload_medication_image(self, image_path: str) -> str:
        """
        Upload medication image and return the relative path.

        Args:
            image_path: Absolute path to the image file.

        Returns:
            Relative path to the uploaded image.
        """
        import shutil
        import json

        # Load counter
        counter_file = os.path.join(BASE_DIR, 'counter.json')
        if os.path.exists(counter_file):
            with open(counter_file, 'r') as f:
                counter = json.load(f)
        else:
            counter = {"nutrition": 0, "exercise": 0, "medication": 0}

        # Ensure all keys exist
        if "medication" not in counter:
            counter["medication"] = 0
        if "nutrition" not in counter:
            counter["nutrition"] = 0
        if "exercise" not in counter:
            counter["exercise"] = 0

        num = counter["medication"]
        counter["medication"] = num + 1

        # Save counter
        with open(counter_file, 'w') as f:
            json.dump(counter, f)

        # Create upload directory
        upload_path = os.path.join(settings.UPLOAD_DIR, "medication")
        os.makedirs(upload_path, exist_ok=True)

        # Generate new filename
        file_extension = os.path.splitext(image_path)[1].lower()
        original_name = os.path.splitext(os.path.basename(image_path))[0]
        new_filename = f"Medication_{original_name}_{num}{file_extension}"
        file_location = os.path.join(upload_path, new_filename)

        # Copy file
        shutil.copy2(image_path, file_location)

        # Return relative path
        relative_path = f"/static/uploads/medication/{new_filename}"
        return relative_path
