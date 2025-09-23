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

        # Target schema definition
        self.target_schema = {
            "customer_name": "string",
            "product_name": "string",
            "quantity": "integer",
            "unit_price": "decimal",
            "sale_date": "date",
            "sales_rep": "string",
            "country": "string"
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
        """Map a source column to target schema field"""

        # Define mapping keywords for each target field
        field_keywords = {
            "customer_name": ["customer", "client", "cliente", "name", "nombre", "nom", "kunde"],
            "product_name": ["product", "item", "producto", "produit", "artikel", "produkt"],
            "quantity": ["quantity", "qty", "amount", "cantidad", "quantité", "menge", "anzahl"],
            "unit_price": ["price", "cost", "precio", "prix", "preis", "unit", "unitario"],
            "sale_date": ["date", "fecha", "datum", "time", "venta", "sale"],
            "sales_rep": ["rep", "vendor", "seller", "vendedor", "représentant", "verkäufer"],
            "country": ["country", "país", "pays", "land", "nation"]
        }

        best_match = None
        best_score = 0

        # Try fuzzy matching with translated text
        for target_field, keywords in field_keywords.items():
            for keyword in keywords:
                # Calculate similarity
                similarity = SequenceMatcher(None, translated_text.lower(), keyword.lower()).ratio()
                if similarity > best_score:
                    best_score = similarity
                    best_match = target_field

        # Use AI for better mapping if fuzzy matching confidence is low
        if best_score < 0.6:
            try:
                ai_mapping = await self._ai_assisted_mapping(source_column, translated_text, sample_data)
                if ai_mapping and ai_mapping['confidence'] > best_score:
                    best_match = ai_mapping['target_field']
                    best_score = ai_mapping['confidence']
            except Exception as e:
                logger.warning(f"AI mapping failed for {source_column}: {str(e)}")

        if best_match and best_score > 0.3:
            # Determine transformation needed
            transformation = self._determine_transformation(best_match, sample_data.get(source_column))

            return SchemaMapping(
                source_column=source_column,
                target_field=best_match,
                mapping_confidence=best_score,
                transformation_needed=transformation,
                status="mapped"
            )
        else:
            # Return rejected mapping with reason
            if best_match:
                reason = f"Low confidence ({best_score:.2f}) - below threshold (0.3)"
            else:
                reason = "No suitable target field found"

            return SchemaMapping(
                source_column=source_column,
                target_field="unmapped",
                mapping_confidence=best_score,
                transformation_needed="none",
                status="rejected",
                rejection_reason=reason
            )

    async def _ai_assisted_mapping(self, source_column: str, translated_text: str, sample_data: Dict) -> Optional[Dict]:
        """Use AI to assist with complex column mapping"""
        try:
            sample_value = sample_data.get(source_column, "")

            prompt = f"""
Given a CSV column with the following details:
- Original column name: {source_column}
- Translated column name: {translated_text}
- Sample value: {sample_value}

Map this to one of these target schema fields:
- customer_name (customer/client name)
- product_name (product/item name)
- quantity (number of items)
- unit_price (price per item)
- sale_date (date of sale)
- sales_rep (salesperson name)
- country (country of sale)

Respond with JSON: {{"target_field": "field_name", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}
"""

            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.1
            )

            result = response.choices[0].message.content.strip()

            # Parse JSON response
            import json
            mapping_result = json.loads(result)

            return mapping_result

        except Exception as e:
            logger.warning(f"AI mapping error: {str(e)}")
            return None

    def _determine_transformation(self, target_field: str, sample_value: Any) -> str:
        """Determine what transformation is needed for the data"""
        if target_field == "quantity":
            return "convert_to_integer"
        elif target_field == "unit_price":
            return "convert_to_decimal"
        elif target_field == "sale_date":
            return "parse_date"
        elif target_field == "country":
            return "infer_country"
        else:
            return "none"