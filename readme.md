# Forge Agent

A team of AI agents that takes messy, multi-language sales CSV files from different countries and intelligently maps them to a unified global schema using **AutoGen 0.7.4**.

## 🎯 The Setup

- **Input CSV**: Mixed sales data with columns in different languages (English, Spanish, German, French)
- **Target Schema**: Standardized global sales format
- **3 Specialized Agents**: Working together using AutoGen's message-passing architecture

### Sample Input CSV
```csv
cliente,producto,cantidad,precio_unitario,fecha_venta,vendedor
María García,Laptop Dell,2,899.99,2024-01-15,Carlos
Jean Dubois,Ordinateur HP,1,1200.50,2024-01-16,Pierre
Hans Mueller,Computer Lenovo,3,750.00,2024-01-17,Klaus
```

### Target Schema
```json
{
  "customer_name": "string",
  "product_name": "string",
  "quantity": "integer",
  "unit_price": "decimal",
  "sale_date": "date",
  "sales_rep": "string",
  "country": "string"
}
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure your OpenAI API key in .env file
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "OPENAI_MODEL=gpt-4o-mini" >> .env
```

### 2. Test the System

**Quick Test (Recommended):**
```bash
# Run comprehensive quick test
./quick_test.sh
```

**Manual Testing:**
```bash
# Check configuration
python main.py check

# Create sample data
python main.py demo

# Process the sample file
python main.py harmonize sample_sales_data.csv
```

**Full Test Suite:**
```bash
# Run complete test suite with multiple languages
./run_tests.sh
```

**Agent Communication Demo:**
```bash
# Interactive demonstration showing agent communication flow
./demo_agent_communication.sh
```

## 🤖 The Agent Team

### 1. Language Detection & Translation Agent
- 🌍 Detects languages in column headers and data values
- 🔄 Translates non-English content to English using Google Translate
- 📝 Preserves original context and meaning
- 📊 Identifies cultural formatting differences (dates, numbers)

### 2. Schema Mapping Agent
- 🗺️ Analyzes translated headers and data patterns
- 🎯 Maps source columns to target schema fields using fuzzy matching
- 🤖 Uses GPT-4o-mini for AI-assisted complex mappings
- ❓ Identifies missing fields and suggests defaults

### 3. Data Validation & Enhancement Agent
- ✅ Validates mapped data against target schema
- 🔧 Fixes formatting issues (date formats, decimal separators)
- 🌍 Enriches data (infers country from sales rep names/language)
- 🛡️ Handles data quality issues and conflicts



## 🔄 Agent Communication Flow

1. **User uploads CSV** → CLI triggers processing
2. **Language Agent**: "Detected Spanish headers: 'cliente', 'producto', 'precio_unitario'"
3. **Language → Schema Agent**: "Translated headers: customer→cliente, product→producto, unit_price→precio_unitario"
4. **Schema Agent**: "Mapping complete: 85% confidence on all fields except missing 'country'"
5. **Schema → Validation Agent**: "Need country inference for records with Spanish names"
6. **Validation Agent**: "Inferred countries: María García→Spain, Jean Dubois→France, Hans Mueller→Germany"
7. **Final Output**: Perfectly mapped, validated data in target schema

## 📋 Usage Examples

### Basic Processing
```bash
python main.py harmonize input.csv
```

### With Custom Output
```bash
python main.py harmonize input.csv --output processed_data.csv
```

### Verbose Mode
```bash
python main.py harmonize input.csv --verbose
```

## 📊 Agent Communication Messages

The agents communicate using typed Pydantic models following AutoGen 0.7.4 best practices:

```python
@dataclass
class LanguageDetection:
    column: str
    detected_language: str
    translated_text: str
    confidence: float

@dataclass
class SchemaMapping:
    source_column: str
    target_field: str
    mapping_confidence: float
    transformation_needed: str

@dataclass
class ValidationResult:
    field: str
    status: str  # "valid", "fixed", "enriched"
    original_value: str
    final_value: str
    action_taken: str
```

## 🏗️ Architecture

Built on **AutoGen 0.7.4** with:
- **SingleThreadedAgentRuntime** for agent coordination
- **Message-based communication** using publish/subscribe pattern
- **Typed message handlers** with `@message_handler` decorators
- **RoutedAgent** base class for intelligent message routing

## 💡 Why This Rocks

- ✅ **Real business problem** - Companies actually struggle with this daily
- 🌍 **Multi-language wow factor** - Handles Spanish, German, French, Italian, Portuguese
- 🧠 **Smart inference** - Deduces missing country data from names/language patterns
- 🔄 **Complex coordination** - Translation → Mapping → Validation pipeline
- 💼 **Immediate value** - Output is immediately usable for business
- 📈 **Scalable** - Works with any language/schema combination

## 📁 Project Structure

```
mapping_demo/
├── 📦 agents/             # AI Agent implementations
│   ├── language_agent.py  # Language detection & translation
│   ├── schema_agent.py    # Schema mapping
│   └── validation_agent.py # Data validation & enhancement
├── 🏗️ core/               # Core business logic
│   ├── models.py          # Message models & data classes
│   └── harmonizer.py      # Main orchestrator
├── 🖥️ cli/                # Command-line interface
│   └── cli.py             # CLI commands
├── 🧪 tests/              # Test files
│   └── test_basic.py      # Basic functionality tests
├── 📜 scripts/            # Utility scripts
│   └── activate.sh        # Environment activation helper
├── 📚 docs/               # Documentation
│   └── ARCHITECTURE.md    # Architecture overview
├── 🎯 main.py             # Main entry point
├── 📋 requirements.txt    # Dependencies
├── 🔧 .env                # Environment variables
├── 📄 .env.example        # Environment template
└── 📖 README.md           # This file
```

## 🔧 Requirements

- Python 3.10+
- OpenAI API key (for GPT-4o-mini)
- AutoGen 0.7.4
- Internet connection (for Google Translate)

## 📊 Enhanced Examples with Challenging Scenarios

The project includes diverse examples that test the system's robustness:

### 🎯 Column Order Variations
- **Random order**: Fields appear in different positions
- **Missing fields**: Some standard fields may not be present
- **Extra fields**: Additional unmapped columns (payment methods, categories, etc.)

### 🌍 Domain-Specific Examples
- **🍕 Italian Restaurant**: `tavolo, metodo_pagamento` (table, payment method)
- **🔌 French Electronics**: `garantie_mois, code_promo` (warranty, promo code)
- **🚗 German Automotive**: `autohaus, farbe, finanzierung` (dealership, color, financing)
- **📚 Portuguese Bookstore**: `isbn, editora, secao` (ISBN, publisher, section)
- **💊 Spanish Pharmacy**: `receta_numero, laboratorio` (prescription #, lab)
- **🏨 Hotel Reservations**: Mixed EU languages with special characters
- **🎯 Ultimate Challenge**: Completely randomized column order

## 📈 Sample Output

```
🌍 Forge Agent
==================================================
📊 Input file: examples/pharmacy_spanish.csv
💾 Output file: examples/pharmacy_spanish_harmonized.csv

✅ Agents initialized successfully

🎉 Processing completed successfully!

📋 Summary:
  • Total records processed: 5
  • Fields mapped: 9 (including unmapped: laboratorio, tipo_medicamento)
  • Fields enriched: 0
  • Quality score: 1.00

👀 Data preview:
  Record 1:
    customer_name: Carmen Ruiz
    product_name: Ibuprofeno 600mg
    quantity: 2
    unit_price: 8.5
    sale_date: 2024-03-25
    sales_rep: Dr. Patricia López
    country: Spain

💾 Harmonized data saved with intelligent field mapping!
```