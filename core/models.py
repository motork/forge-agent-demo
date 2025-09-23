from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


@dataclass
class LanguageDetection:
    column: str
    detected_language: str
    detected_language_full: str
    translated_text: str
    confidence: float


@dataclass
class SchemaMapping:
    source_column: str
    target_field: str
    mapping_confidence: float
    transformation_needed: str
    status: str  # "mapped", "rejected", "unmapped"
    rejection_reason: Optional[str] = None


@dataclass
class ValidationResult:
    field: str
    status: str  # "valid", "fixed", "enriched"
    original_value: str
    final_value: str
    action_taken: str


class LanguageDetectionMessage(BaseModel):
    detections: List[LanguageDetection]
    csv_headers: List[str]
    sample_data: Dict[str, Any]


class SchemaMappingMessage(BaseModel):
    mappings: List[SchemaMapping]
    confidence_score: float
    missing_fields: List[str]


class ValidationMessage(BaseModel):
    results: List[ValidationResult]
    enriched_data: List[Dict[str, Any]]
    quality_score: float


class ProcessCSVMessage(BaseModel):
    file_path: str
    target_schema: Dict[str, str]


class FinalResultMessage(BaseModel):
    mapped_data: List[Dict[str, Any]]
    processing_summary: Dict[str, Any]
    success: bool