import asyncio
from typing import List, Dict, Any, Optional
from autogen_core import RoutedAgent, message_handler
from autogen_core import DefaultTopicId
from core.models import (
    SchemaMapping, SchemaMappingMessage,
    LanguageDetectionMessage, ValidationMessage
)
import logging
from difflib import SequenceMatcher
import openai
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaMappingAgent(RoutedAgent):
    def __init__(self, model_client):
        super().__init__("SchemaMappingAgent")
        self.model_client = model_client
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Target automotive schema definition with customer lead data
        self.target_schema = {
            "vehicle_make": "string",
            "vehicle_model": "string",
            "price": "decimal",
            "fuel_type": "string",
            "year": "integer",
            "dealer_name": "string",
            "country": "string",
            "customer_name": "string",
            "customer_email": "string",
            "customer_phone": "string",
            "lead_source": "string"
        }

        # Predefined fuel type mappings
        self.fuel_mappings = {
            # Gasoline variations
            "gasoline": "Gasoline", "petrol": "Gasoline", "benzin": "Gasoline", "benzina": "Gasoline",
            "essence": "Gasoline", "gasolina": "Gasoline", "benzyne": "Gasoline",
            # Diesel variations
            "diesel": "Diesel", "gasoil": "Diesel", "gasoleo": "Diesel", "mazut": "Diesel",
            "motorina": "Diesel", "nafta": "Diesel",
            # Electric variations
            "electric": "Electric", "elettrico": "Electric", "électrique": "Electric",
            "elektrisch": "Electric", "elétrico": "Electric", "elektrik": "Electric",
            # Hybrid variations
            "hybrid": "Hybrid", "ibrido": "Hybrid", "hybride": "Hybrid", "híbrido": "Hybrid",
            "hibrit": "Hybrid", "hybryd": "Hybrid",
            # LPG variations
            "lpg": "LPG", "gpl": "LPG", "autogas": "LPG", "propane": "LPG"
        }

    @message_handler
    async def handle_language_detection(self, message: LanguageDetectionMessage, ctx) -> None:
        """Process language detection results and map to target schema"""
        logger.info(f"🗺️  Schema Agent: Received language detection for {len(message.csv_headers)} columns")

        try:
            # Extract translated headers
            translated_headers = {}
            for detection in message.detections:
                if detection.column in message.csv_headers:
                    translated_headers[detection.column] = detection.translated_text.lower()

            # Perform mapping for all columns
            mappings = []
            for source_column in message.csv_headers:
                mapping = await self._map_column_to_schema(
                    source_column,
                    translated_headers.get(source_column, source_column),
                    message.sample_data
                )
                # Include all mappings (mapped and rejected)
                mappings.append(mapping)

            # Calculate overall confidence based on mapped fields only
            mapped_mappings = [m for m in mappings if m.status == "mapped"]
            confidence_score = sum(m.mapping_confidence for m in mapped_mappings) / len(mapped_mappings) if mapped_mappings else 0

            # Find missing fields
            mapped_fields = {m.target_field for m in mapped_mappings}
            missing_fields = [field for field in self.target_schema.keys() if field not in mapped_fields]

            # Create response
            response = SchemaMappingMessage(
                mappings=mappings,
                confidence_score=confidence_score,
                missing_fields=missing_fields
            )

            mapped_count = len([m for m in mappings if m.status == "mapped"])
            rejected_count = len([m for m in mappings if m.status == "rejected"])

            logger.info(f"🗺️  Schema Agent: Processed {len(mappings)} fields - {mapped_count} mapped, {rejected_count} rejected")
            logger.info(f"  📊 Overall confidence: {confidence_score:.2f}")

            for mapping in mappings:
                if mapping.status == "mapped":
                    logger.info(f"  ✅ '{mapping.source_column}' -> '{mapping.target_field}' (confidence: {mapping.mapping_confidence:.2f})")
                else:
                    logger.info(f"  ❌ '{mapping.source_column}' -> REJECTED ({mapping.rejection_reason})")

            if missing_fields:
                logger.info(f"  ⚠️  Missing target fields: {missing_fields}")

            # Send to Validation Agent
            await self.publish_message(response, DefaultTopicId())

        except Exception as e:
            logger.error(f"❌ Schema Agent Error: {str(e)}")

    async def _map_column_to_schema(self, source_column: str, translated_text: str, sample_data: Dict) -> Optional[SchemaMapping]:
        """Map a source column to target schema field using AI-first approach"""

        # Let AI handle ALL mappings intelligently
        try:
            ai_mapping = await self._ai_assisted_mapping(source_column, translated_text, sample_data)
            if ai_mapping and ai_mapping['confidence'] > 0.6:
                transformation = self._determine_transformation(ai_mapping['target_field'], sample_data.get(source_column))

                return SchemaMapping(
                    source_column=source_column,
                    target_field=ai_mapping['target_field'],
                    mapping_confidence=ai_mapping['confidence'],
                    transformation_needed=transformation,
                    status="mapped"
                )
            else:
                # Return rejected mapping with AI reasoning
                reason = ai_mapping.get('reasoning', 'Low AI confidence') if ai_mapping else "AI mapping failed"
                confidence = ai_mapping.get('confidence', 0.0) if ai_mapping else 0.0

                return SchemaMapping(
                    source_column=source_column,
                    target_field="unmapped",
                    mapping_confidence=confidence,
                    transformation_needed="none",
                    status="rejected",
                    rejection_reason=reason
                )
        except Exception as e:
            logger.warning(f"AI mapping failed for {source_column}: {str(e)}")
            return SchemaMapping(
                source_column=source_column,
                target_field="unmapped",
                mapping_confidence=0.0,
                transformation_needed="none",
                status="rejected",
                rejection_reason=f"AI mapping error: {str(e)}"
            )

    async def _ai_assisted_mapping(self, source_column: str, translated_text: str, sample_data: Dict) -> Optional[Dict]:
        """Use AI to assist with complex column mapping"""
        try:
            sample_value = sample_data.get(source_column, "")

            prompt = f"""You are an intelligent automotive data harmonization system. Your task is to analyze CSV columns from car dealership data across different languages and map them to a standardized schema.

## Input Data
- Source column: "{source_column}"
- Translated/normalized name: "{translated_text}"
- Sample data value: "{sample_value}"

## Target Schema (Automotive Lead Management)
1. vehicle_make - Manufacturer/brand (BMW, Mercedes, Audi, Toyota, etc.)
2. vehicle_model - Specific model (X5, A4, Golf, Camry, etc.)
3. price - Vehicle price/cost (numbers, currency symbols)
4. fuel_type - Fuel/energy type (Gasoline, Diesel, Electric, Hybrid, LPG)
5. year - Manufacturing/model year (4-digit years)
6. dealer_name - Dealership, salesperson, or seller name
7. country - Country of sale/origin
8. customer_name - Customer's full name
9. customer_email - Customer's email address
10. customer_phone - Customer's phone/telephone number
11. lead_source - Lead generation source (website, referral, phone, etc.)

## Your Analysis Process
1. **Content Analysis**: Examine the sample value to understand the actual data type
2. **Semantic Understanding**: Consider the column name meaning across languages
3. **Context Reasoning**: Use automotive domain knowledge for ambiguous cases
4. **Confidence Assessment**: Rate your certainty (0.0-1.0) based on clarity of evidence

## Decision Guidelines
- Prioritize data content over column names when they conflict
- For compound names (email_cliente, kunde_phone), focus on the data type, not customer indicator
- Email addresses (@ symbols) always map to customer_email regardless of column name
- Phone numbers (+ symbols, digit patterns) always map to customer_phone
- Price indicators (currency symbols, large numbers) map to price
- Be conservative with confidence - uncertain mappings should have lower scores

Respond with JSON only:
{{"target_field": "field_name", "confidence": 0.75, "reasoning": "why this mapping makes sense"}}"""

            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a data mapping specialist. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            result = response.choices[0].message.content.strip()
            logger.info(f"OpenAI raw response for '{source_column}': {result}")

            # Parse JSON response with better error handling
            import json
            mapping_result = json.loads(result)

            # Validate required fields
            if not all(key in mapping_result for key in ["target_field", "confidence"]):
                logger.warning(f"AI response missing required fields: {mapping_result}")
                return None

            # Validate target field is in our automotive schema
            valid_fields = ["vehicle_make", "vehicle_model", "price", "fuel_type", "year", "dealer_name", "country", "customer_name", "customer_email", "customer_phone", "lead_source"]
            if mapping_result["target_field"] not in valid_fields:
                logger.warning(f"AI returned invalid target field '{mapping_result['target_field']}' for '{source_column}'")
                return None

            # Ensure confidence is a float between 0 and 1
            confidence = float(mapping_result["confidence"])
            if confidence < 0 or confidence > 1:
                confidence = max(0, min(1, confidence))
                mapping_result["confidence"] = confidence

            logger.info(f"🤖 AI mapping: '{source_column}' -> '{mapping_result['target_field']}' (confidence: {confidence:.2f})")
            return mapping_result

        except json.JSONDecodeError as e:
            logger.warning(f"AI mapping JSON error for '{source_column}': {str(e)} - Response: {result if 'result' in locals() else 'No response'}")
            return None
        except Exception as e:
            logger.warning(f"AI mapping error for '{source_column}': {str(e)}")
            return None

    def _determine_transformation(self, target_field: str, sample_value: Any) -> str:
        """Determine what transformation is needed for automotive data"""
        if target_field == "year":
            return "convert_to_integer"
        elif target_field == "price":
            return "convert_to_decimal"
        elif target_field == "fuel_type":
            return "normalize_fuel_type"
        elif target_field == "country":
            return "infer_country"
        elif target_field == "customer_email":
            return "validate_email"
        elif target_field == "customer_phone":
            return "normalize_phone"
        elif target_field == "lead_source":
            return "validate_lead_source"
        else:
            return "none"