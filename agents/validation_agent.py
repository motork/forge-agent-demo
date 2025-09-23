import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from autogen_core import RoutedAgent, message_handler
from autogen_core import DefaultTopicId
from core.models import (
    ValidationResult, ValidationMessage,
    SchemaMappingMessage, FinalResultMessage
)
import logging
import openai
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidationAgent(RoutedAgent):
    def __init__(self, model_client):
        super().__init__("DataValidationAgent")
        self.model_client = model_client
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Country inference mappings
        self.name_country_patterns = {
            'spain': ['maría', 'josé', 'carlos', 'ana', 'manuel', 'carmen', 'antonio', 'francisco'],
            'france': ['jean', 'marie', 'pierre', 'jacques', 'michel', 'françoise', 'nicolas', 'philippe'],
            'germany': ['hans', 'klaus', 'werner', 'günter', 'helmut', 'brigitte', 'ursula', 'ingrid'],
            'italy': ['giovanni', 'giuseppe', 'antonio', 'francesco', 'mario', 'luigi', 'alessandro'],
            'portugal': ['joão', 'antónio', 'josé', 'manuel', 'francisco', 'luis', 'pedro']
        }

        self.language_country_map = {
            'es': 'Spain',
            'fr': 'France',
            'de': 'Germany',
            'it': 'Italy',
            'pt': 'Portugal',
            'en': 'UK'
        }

    @message_handler
    async def handle_schema_mapping(self, message: SchemaMappingMessage, ctx) -> None:
        """Process schema mapping results and validate/enhance data"""
        logger.info(f"✅ Validation Agent: Processing {len(message.mappings)} mapped fields")

        # Store mapping for later use
        self.current_mappings = {m.source_column: m for m in message.mappings}
        self.missing_fields = message.missing_fields

        # We need the actual CSV data to process, so we'll wait for it
        # This agent will be triggered by the CLI with the actual data

    async def validate_and_enhance_data(self, csv_file_path: str, detections: List) -> FinalResultMessage:
        """Main method to validate and enhance the CSV data"""
        try:
            # Read the CSV data
            df = pd.read_csv(csv_file_path)

            validation_results = []
            enhanced_data = []

            # Store language detections for country inference
            self.language_detections = {d.column: d for d in detections if d.column in df.columns}

            logger.info(f"✅ Validation Agent: Processing {len(df)} records")

            for index, row in df.iterrows():
                enhanced_row = {}

                # Process each mapped field
                for source_col, mapping in self.current_mappings.items():
                    if source_col in row:
                        original_value = row[source_col]

                        # Validate and transform the value
                        result = await self._validate_and_transform(
                            original_value,
                            mapping.target_field,
                            mapping.transformation_needed,
                            row.to_dict()
                        )

                        validation_results.append(result)
                        enhanced_row[mapping.target_field] = result.final_value

                # Handle missing fields (like country inference)
                for missing_field in self.missing_fields:
                    if missing_field == "country":
                        inferred_country = self._infer_country(row.to_dict())
                        enhanced_row["country"] = inferred_country

                        validation_results.append(ValidationResult(
                            field="country",
                            status="enriched",
                            original_value="",
                            final_value=inferred_country,
                            action_taken=f"Inferred from name patterns and language"
                        ))

                enhanced_data.append(enhanced_row)

            # Calculate quality score
            quality_score = self._calculate_quality_score(validation_results)

            # Create final result
            processing_summary = {
                "total_records": len(df),
                "fields_mapped": len(self.current_mappings),
                "fields_enriched": len(self.missing_fields),
                "quality_score": quality_score,
                "validation_results": len(validation_results)
            }

            result = FinalResultMessage(
                mapped_data=enhanced_data,
                processing_summary=processing_summary,
                success=True
            )

            logger.info(f"✅ Validation Agent: Successfully processed {len(enhanced_data)} records")
            logger.info(f"📊 Quality Score: {quality_score:.2f}")

            return result

        except Exception as e:
            logger.error(f"❌ Validation Agent Error: {str(e)}")
            return FinalResultMessage(
                mapped_data=[],
                processing_summary={"error": str(e)},
                success=False
            )

    async def _validate_and_transform(self, value: Any, target_field: str, transformation: str, full_row: Dict) -> ValidationResult:
        """Validate and transform a single value"""
        original_value = str(value)
        final_value = value
        status = "valid"
        action_taken = "none"

        try:
            if transformation == "convert_to_integer":
                try:
                    # Handle different number formats
                    clean_val = str(value).replace(",", "").replace(" ", "")
                    final_value = int(float(clean_val))
                    if str(value) != str(final_value):
                        status = "fixed"
                        action_taken = "Converted to integer"
                except:
                    final_value = 0
                    status = "fixed"
                    action_taken = "Set to 0 (invalid number)"

            elif transformation == "convert_to_decimal":
                try:
                    # Handle different decimal formats (European vs US)
                    clean_val = str(value).replace(",", ".")
                    final_value = float(clean_val)
                    if str(value) != str(final_value):
                        status = "fixed"
                        action_taken = "Converted to decimal"
                except:
                    final_value = 0.0
                    status = "fixed"
                    action_taken = "Set to 0.0 (invalid decimal)"

            elif transformation == "parse_date":
                final_value = self._parse_date(value)
                if str(value) != final_value:
                    status = "fixed"
                    action_taken = "Standardized date format"

            else:
                # No transformation needed, just clean the string
                final_value = str(value).strip()

        except Exception as e:
            logger.warning(f"Transformation error for {target_field}: {str(e)}")
            final_value = str(value)
            status = "valid"

        return ValidationResult(
            field=target_field,
            status=status,
            original_value=original_value,
            final_value=str(final_value),
            action_taken=action_taken
        )

    def _parse_date(self, date_value: Any) -> str:
        """Parse various date formats into ISO format"""
        date_str = str(date_value).strip()

        # Common date patterns
        patterns = [
            "%Y-%m-%d",      # 2024-01-15
            "%d/%m/%Y",      # 15/01/2024
            "%m/%d/%Y",      # 01/15/2024
            "%d.%m.%Y",      # 15.01.2024
            "%d-%m-%Y",      # 15-01-2024
        ]

        for pattern in patterns:
            try:
                parsed_date = datetime.strptime(date_str, pattern)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # If no pattern matches, return original
        return date_str

    def _infer_country(self, row: Dict) -> str:
        """Infer country from name patterns and language detection"""

        # First try to infer from names
        for field_value in row.values():
            if isinstance(field_value, str):
                name_lower = field_value.lower()

                for country, patterns in self.name_country_patterns.items():
                    for pattern in patterns:
                        if pattern in name_lower:
                            return country.title()

        # Then try language detection from the stored detections
        for detection in self.language_detections.values():
            if detection.detected_language in self.language_country_map:
                return self.language_country_map[detection.detected_language]

        # Default
        return "Unknown"

    def _calculate_quality_score(self, validation_results: List[ValidationResult]) -> float:
        """Calculate overall data quality score"""
        if not validation_results:
            return 0.0

        total_fields = len(validation_results)
        valid_fields = sum(1 for r in validation_results if r.status in ["valid", "fixed", "enriched"])

        return valid_fields / total_fields