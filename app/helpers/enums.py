import enum


class UserRole(enum.Enum):
    PATIENT = 'PATIENT'
    CARETAKER = 'CARETAKER'

class Gender(enum.Enum):
    MALE = 'MALE'
    FEMALE = 'FEMALE'
    OTHER = 'OTHER'

class DiseaseType(enum.Enum):
    PHYSICAL_THERAPY = 'PHYSICAL_THERAPY'
    MENTAL_DECLINE = 'MENTAL_DECLINE'
    LONELINESS = 'LONELINESS'
