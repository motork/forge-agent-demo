import asyncio
import pandas as pd
from typing import Dict, Any, List
from autogen_core import SingleThreadedAgentRuntime, AgentId
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

from agents.language_agent import LanguageDetectionAgent
from agents.schema_agent import SchemaMappingAgent
from agents.validation_agent import DataValidationAgent
from .models import ProcessCSVMessage, FinalResultMessage

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForgeAgentHarmonizer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.runtime = None
        self.results = {}

    async def initialize(self):
        """Initialize the AutoGen runtime and agents"""
        logger.info("🚀 Initializing Sales Data Harmonizer v2...")

        # Create runtime
        self.runtime = SingleThreadedAgentRuntime()

        # Register agent factories
        await self.runtime.register_factory(
            type="LanguageDetectionAgent",
            agent_factory=lambda: LanguageDetectionAgent(model_client=self.client)
        )

        await self.runtime.register_factory(
            type="SchemaMappingAgent",
            agent_factory=lambda: SchemaMappingAgent(model_client=self.client)
        )

        await self.runtime.register_factory(
            type="DataValidationAgent",
            agent_factory=lambda: DataValidationAgent(model_client=self.client)
        )

        # Start runtime
        self.runtime.start()
        logger.info("✅ All agents initialized and runtime started")

    async def process_csv(self, file_path: str, output_path: str = None) -> Dict[str, Any]:
        """Process a CSV file through the agent pipeline"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        logger.info(f"📊 Processing CSV file: {file_path}")

        try:
            # Read CSV to get basic info for processing
            df = pd.read_csv(file_path)
            logger.info(f"📋 Found {len(df)} records with columns: {list(df.columns)}")

            # For now, let's do a simplified direct processing approach
            # since the agent message passing in AutoGen 0.7.4 requires more complex setup

            # Create agents directly for processing
            language_agent = LanguageDetectionAgent(model_client=self.client)
            schema_agent = SchemaMappingAgent(model_client=self.client)
            validation_agent = DataValidationAgent(model_client=self.client)

            # Step 1: Language Detection & Translation
            logger.info("🌍 Step 1: Language Detection & Translation")

            # Process language detection manually
            detections = []
            headers = df.columns.tolist()
            sample_data = df.head(1).to_dict('records')[0] if len(df) > 0 else {}

            for header in headers:
                detection = await language_agent._detect_and_translate(header, "header")
                detections.append(detection)
                logger.info(f"  📝 '{header}' -> {detection.detected_language}: '{detection.translated_text}'")

            # Step 2: Schema Mapping
            logger.info("🗺️ Step 2: Schema Mapping")

            # Extract translated headers
            translated_headers = {}
            for detection in detections:
                if detection.column in headers:
                    translated_headers[detection.column] = detection.translated_text.lower()

            # Perform mapping
            mappings = []
            for source_column in headers:
                mapping = await schema_agent._map_column_to_schema(
                    source_column,
                    translated_headers.get(source_column, source_column),
                    sample_data
                )
                if mapping:
                    mappings.append(mapping)
                    logger.info(f"  📋 '{mapping.source_column}' -> '{mapping.target_field}' ({mapping.mapping_confidence:.2f})")

            # Set current mappings for validation agent
            validation_agent.current_mappings = {m.source_column: m for m in mappings}
            validation_agent.missing_fields = []

            # Calculate missing fields
            mapped_fields = {m.target_field for m in mappings}
            target_schema = {
                "customer_name": "string",
                "product_name": "string",
                "quantity": "integer",
                "unit_price": "decimal",
                "sale_date": "date",
                "sales_rep": "string",
                "country": "string"
            }
            missing_fields = [field for field in target_schema.keys() if field not in mapped_fields]
            validation_agent.missing_fields = missing_fields

            if missing_fields:
                logger.info(f"  ⚠️ Missing fields: {missing_fields}")

            # Step 3: Data Validation & Enhancement
            logger.info("✅ Step 3: Data Validation & Enhancement")

            final_result = await validation_agent.validate_and_enhance_data(
                file_path,
                detections
            )

            # Save results if output path provided
            if output_path and final_result.success:
                self._save_results(final_result, output_path)

            return self._format_results(final_result)

        except Exception as e:
            logger.error(f"❌ Error processing CSV: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _save_results(self, result: FinalResultMessage, output_path: str):
        """Save the harmonized data to CSV"""
        try:
            df = pd.DataFrame(result.mapped_data)
            df.to_csv(output_path, index=False)
            logger.info(f"💾 Results saved to: {output_path}")
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")

    def _format_results(self, result: FinalResultMessage) -> Dict[str, Any]:
        """Format results for display"""
        if not result.success:
            return {
                "success": False,
                "error": result.processing_summary.get("error", "Unknown error")
            }

        return {
            "success": True,
            "summary": result.processing_summary,
            "data_preview": result.mapped_data[:3] if result.mapped_data else [],
            "total_records": len(result.mapped_data)
        }

    async def shutdown(self):
        """Clean shutdown of the harmonizer"""
        if self.runtime:
            await self.runtime.stop()
            logger.info("🛑 Harmonizer shutdown complete")


async def create_harmonizer():
    """Factory function to create and initialize forge agent harmonizer"""
    harmonizer = ForgeAgentHarmonizer()
    await harmonizer.initialize()
    return harmonizer