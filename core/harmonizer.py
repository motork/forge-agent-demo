import asyncio
import json
import pandas as pd
from typing import Dict, Any, List
from autogen_core import SingleThreadedAgentRuntime
from autogen_core import DefaultTopicId
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


class SalesDataHarmonizer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.runtime = None
        self.language_agent = None
        self.schema_agent = None
        self.validation_agent = None

    async def initialize(self):
        """Initialize the AutoGen runtime and agents"""
        logger.info("🚀 Initializing Sales Data Harmonizer...")

        # Create runtime
        self.runtime = SingleThreadedAgentRuntime()

        # Create agents
        self.language_agent = LanguageDetectionAgent(model_client=self.client)
        self.schema_agent = SchemaMappingAgent(model_client=self.client)
        self.validation_agent = DataValidationAgent(model_client=self.client)

        # Register agents with runtime using register_factory
        await self.runtime.register_factory(
            type="LanguageDetectionAgent",
            agent_factory=lambda: self.language_agent
        )

        await self.runtime.register_factory(
            type="SchemaMappingAgent",
            agent_factory=lambda: self.schema_agent
        )

        await self.runtime.register_factory(
            type="DataValidationAgent",
            agent_factory=lambda: self.validation_agent
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
            # Step 1: Language Detection
            logger.info("🌍 Step 1: Language Detection & Translation")
            message = ProcessCSVMessage(
                file_path=file_path,
                target_schema={
                    "customer_name": "string",
                    "product_name": "string",
                    "quantity": "integer",
                    "unit_price": "decimal",
                    "sale_date": "date",
                    "sales_rep": "string",
                    "country": "string"
                }
            )

            # Send to language agent
            await self.runtime.send_message(message, self.language_agent)

            # Wait a moment for processing
            await asyncio.sleep(2)

            # Step 2: Schema Mapping (handled by agent communication)
            logger.info("🗺️  Step 2: Schema Mapping")
            await asyncio.sleep(2)

            # Step 3: Data Validation & Enhancement
            logger.info("✅ Step 3: Data Validation & Enhancement")

            # Get the language detections from the language agent
            detections = []
            if hasattr(self.language_agent, '_last_detections'):
                detections = self.language_agent._last_detections

            # Process through validation agent
            final_result = await self.validation_agent.validate_and_enhance_data(
                file_path,
                detections
            )

            # Save results if output path provided
            if output_path and final_result.success:
                self._save_results(final_result, output_path)

            return self._format_results(final_result)

        except Exception as e:
            logger.error(f"❌ Error processing CSV: {str(e)}")
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


# Enhanced agents to store intermediate results for the synchronous flow
class EnhancedLanguageDetectionAgent(LanguageDetectionAgent):
    def __init__(self, model_client):
        super().__init__(model_client)
        self._last_detections = []

    async def handle_csv_processing(self, message: ProcessCSVMessage, ctx) -> None:
        await super().handle_csv_processing(message, ctx)
        # Store detections for later access
        self._last_detections = getattr(self, '_current_detections', [])


# Update the harmonizer to use enhanced agents
async def create_harmonizer():
    """Factory function to create and initialize harmonizer"""
    harmonizer = SalesDataHarmonizer()
    await harmonizer.initialize()
    return harmonizer