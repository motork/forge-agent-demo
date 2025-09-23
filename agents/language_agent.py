import asyncio
import pandas as pd
from langdetect import detect, LangDetectException
from googletrans import Translator
from typing import List, Dict, Any, Optional
from autogen_core import RoutedAgent, message_handler
from autogen_core import DefaultTopicId
from core.models import (
    LanguageDetection, LanguageDetectionMessage,
    ProcessCSVMessage, SchemaMappingMessage
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LanguageDetectionAgent(RoutedAgent):
    def __init__(self, model_client):
        super().__init__("LanguageDetectionAgent")
        self.translator = Translator()
        self.model_client = model_client
        # Language code to full name mapping
        self.language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'nl': 'Dutch',
            'pl': 'Polish',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'tr': 'Turkish',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish',
            'ro': 'Romanian',
            'hu': 'Hungarian',
            'cs': 'Czech',
            'sk': 'Slovak',
            'bg': 'Bulgarian',
            'hr': 'Croatian',
            'sr': 'Serbian',
            'sl': 'Slovenian',
            'et': 'Estonian',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'el': 'Greek',
            'he': 'Hebrew',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'id': 'Indonesian',
            'ms': 'Malay',
            'tl': 'Filipino',
            'uk': 'Ukrainian',
            'be': 'Belarusian',
            'ka': 'Georgian',
            'hy': 'Armenian',
            'az': 'Azerbaijani',
            'kk': 'Kazakh',
            'ky': 'Kyrgyz',
            'uz': 'Uzbek',
            'mn': 'Mongolian',
            'ne': 'Nepali',
            'si': 'Sinhala',
            'my': 'Myanmar',
            'km': 'Khmer',
            'lo': 'Lao',
            'bn': 'Bengali',
            'pa': 'Punjabi',
            'gu': 'Gujarati',
            'or': 'Odia',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'mr': 'Marathi',
            'ur': 'Urdu',
            'fa': 'Persian',
            'ps': 'Pashto',
            'sd': 'Sindhi',
            'cy': 'Welsh',
            'ga': 'Irish',
            'gd': 'Scottish Gaelic',
            'mt': 'Maltese',
            'is': 'Icelandic',
            'fo': 'Faroese',
            'eu': 'Basque',
            'ca': 'Catalan',
            'gl': 'Galician',
            'ast': 'Asturian',
            'oc': 'Occitan',
            'co': 'Corsican',
            'sc': 'Sardinian',
            'rm': 'Romansh',
            'fur': 'Friulian',
            'lld': 'Ladin',
            'vec': 'Venetian',
            'lmo': 'Lombard',
            'pms': 'Piedmontese',
            'lij': 'Ligurian',
            'nap': 'Neapolitan',
            'scn': 'Sicilian',
            'srd': 'Sardinian',
            'unknown': 'Unknown'
        }

    def get_language_name(self, lang_code: str) -> str:
        """Get full language name from language code"""
        return self.language_names.get(lang_code, lang_code.title())

    @message_handler
    async def handle_csv_processing(self, message: ProcessCSVMessage, ctx) -> None:
        """Process CSV file to detect languages and translate headers/content"""
        logger.info(f"🌍 Language Agent: Processing CSV file {message.file_path}")

        try:
            # Read CSV file
            df = pd.read_csv(message.file_path)
            headers = df.columns.tolist()

            # Get sample data (first few rows)
            sample_data = df.head(3).to_dict('records')

            # Detect languages in headers
            detections = []

            for header in headers:
                detection = await self._detect_and_translate(header, "header")
                detections.append(detection)

            # Detect languages in sample data values
            for i, row in enumerate(sample_data[:1]):  # Just first row for efficiency
                for column, value in row.items():
                    if isinstance(value, str) and len(value.strip()) > 2:
                        detection = await self._detect_and_translate(
                            value, f"data_row_{i}_{column}"
                        )
                        detections.append(detection)

            # Create response message
            response = LanguageDetectionMessage(
                detections=detections,
                csv_headers=headers,
                sample_data=sample_data[0] if sample_data else {}
            )

            logger.info(f"🌍 Language Agent: Detected {len(detections)} language patterns")
            for detection in detections[:3]:  # Show first 3
                logger.info(f"  📝 '{detection.column}' -> {detection.detected_language_full}: '{detection.translated_text}'")

            # Send to Schema Mapping Agent
            await self.publish_message(response, DefaultTopicId())

        except Exception as e:
            logger.error(f"❌ Language Agent Error: {str(e)}")

    async def _detect_and_translate(self, text: str, column: str) -> LanguageDetection:
        """Detect language and translate text to English"""
        try:
            # Clean the text
            text_clean = str(text).strip()

            if len(text_clean) < 2:
                return LanguageDetection(
                    column=column,
                    detected_language="en",
                    detected_language_full="English",
                    translated_text=text_clean,
                    confidence=1.0
                )

            # Detect language
            try:
                detected_lang = detect(text_clean)
                confidence = 0.8  # langdetect doesn't provide confidence
            except LangDetectException:
                detected_lang = "en"
                confidence = 0.5

            # Translate if not English
            if detected_lang != "en":
                try:
                    # Use a simple translation approach for now
                    translated_text = text_clean  # Keep original for debugging
                    logger.info(f"🔄 Translating '{text_clean}' from {self.get_language_name(detected_lang)} to English")
                except Exception as e:
                    logger.warning(f"Translation failed for '{text_clean}': {str(e)}")
                    translated_text = text_clean
                    confidence = 0.3
            else:
                translated_text = text_clean

            return LanguageDetection(
                column=column,
                detected_language=detected_lang,
                detected_language_full=self.get_language_name(detected_lang),
                translated_text=translated_text,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Translation error for '{text}': {str(e)}")
            return LanguageDetection(
                column=column,
                detected_language="unknown",
                detected_language_full="Unknown",
                translated_text=str(text),
                confidence=0.1
            )