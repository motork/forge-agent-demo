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

        # Define strict mapping keywords for each target field
        field_keywords = {
            "customer_name": ["customer", "client", "cliente", "customer_name", "client_name", "nome_cliente"],
            "product_name": ["product", "produto", "produit", "produkt", "product_name", "nome_produto", "articolo", "item"],
            "quantity": ["quantity", "qty", "cantidad", "quantité", "menge", "anzahl", "quantita"],
            "unit_price": ["unit_price", "price", "precio", "prix", "preis", "prezzo", "precio_unitario", "prezzo_pezzo"],
            "sale_date": ["sale_date", "date", "fecha", "datum", "data", "fecha_venta", "data_vendita", "data_ordine"],
            "sales_rep": ["sales_rep", "rep", "vendedor", "représentant", "verkäufer", "venditore", "cameriere"],
            "country": ["country", "país", "pays", "land", "paese", "pais"]
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

        if best_match and best_score > 0.7:
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
                reason = f"Low confidence ({best_score:.2f}) - below threshold (0.7)"
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

            prompt = f"""You are a data mapping expert. Analyze the CSV column and map it to the correct target schema field.

Column Details:
- Original name: "{source_column}"
- Translated name: "{translated_text}"
- Sample value: "{sample_value}"

Target Schema Fields:
1. customer_name - customer or client name
2. product_name - product, item, or service name
3. quantity - number of items/units
4. unit_price - price per single item
5. sale_date - date of sale/transaction
6. sales_rep - salesperson or representative name
7. country - country of sale/origin

IMPORTANT: Respond with ONLY valid JSON, no additional text:

{{"target_field": "field_name", "confidence": 0.85, "reasoning": "brief explanation"}}"""

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
            logger.debug(f"OpenAI response for '{source_column}': {result}")

            # Parse JSON response with better error handling
            import json
            mapping_result = json.loads(result)

            # Validate required fields
            if not all(key in mapping_result for key in ["target_field", "confidence"]):
                logger.warning(f"AI response missing required fields: {mapping_result}")
                return None

            # Validate target field is in our schema
            valid_fields = ["customer_name", "product_name", "quantity", "unit_price", "sale_date", "sales_rep", "country"]
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