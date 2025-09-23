#!/usr/bin/env python3
"""
Basic test to verify AutoGen setup and imports
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required packages can be imported"""
    try:
        import autogen_agentchat
        print("✅ autogen-agentchat imported successfully")

        import autogen_core
        print("✅ autogen-core imported successfully")

        import openai
        print("✅ openai imported successfully")

        import pandas
        print("✅ pandas imported successfully")

        import langdetect
        print("✅ langdetect imported successfully")

        import googletrans
        print("✅ googletrans imported successfully")

        from core.models import LanguageDetection, SchemaMapping, ValidationResult
        print("✅ Custom models imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without API calls"""
    try:
        from core.models import LanguageDetection, ProcessCSVMessage

        # Test data model creation
        detection = LanguageDetection(
            column="test",
            detected_language="es",
            translated_text="test",
            confidence=0.8
        )
        print("✅ LanguageDetection model created successfully")

        message = ProcessCSVMessage(
            file_path="test.csv",
            target_schema={"test": "string"}
        )
        print("✅ ProcessCSVMessage model created successfully")

        return True

    except Exception as e:
        print(f"❌ Basic functionality error: {e}")
        return False

def main():
    print("🧪 Running basic system tests...")
    print("=" * 40)

    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        sys.exit(1)

    print()

    # Test basic functionality
    if not test_basic_functionality():
        print("\n❌ Basic functionality tests failed")
        sys.exit(1)

    print("\n🎉 All basic tests passed!")
    print("\nNext steps:")
    print("1. Add your OpenAI API key to .env file")
    print("2. Run: python main.py check")
    print("3. Run: python main.py demo")
    print("4. Run: python main.py harmonize sample_sales_data.csv")

if __name__ == "__main__":
    main()