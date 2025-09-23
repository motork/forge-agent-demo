# Forge Agent

A team of AI agents that takes messy, multi-language automotive CSV files from different European dealerships and intelligently maps them to a unified global schema using **AutoGen 0.7.4**.

## 🎯 The Setup

- **Input CSV**: Mixed automotive **lead data** with columns in different European languages (Spanish, Portuguese, French, German, Italian)
- **Target Schema**: Standardized global automotive format with **strict field mapping** including customer information
- **3 Specialized Agents**: Working together using AutoGen's message-passing architecture
- **Price Conversion**: Automatically converts string prices (€28.500, $45,000) to decimal float values
- **Fuel Type Mapping**: Maps multilingual fuel terms to predefined standard values (Gasoline, Diesel, Electric, Hybrid, LPG)
- **Lead Data Processing**: Validates email formats, normalizes phone numbers, and standardizes lead sources

### Sample Input CSV
```csv
marca_auto,modelo_carro,preço_venda,combustível,ano_fabrico,vendedor_nome,país,cliente_nome,email_cliente,telefone_cliente,origem_lead
Volkswagen,Golf,€28.500,Gasolina,2023,João Silva,Portugal,Maria Santos,maria.santos@email.pt,+351 912 345 678,Website
Tesla,Model S,€89.900,Eléctrico,2023,Ana Rodriguez,Espanha,Carlos Mendez,carlos.mendez@gmail.com,+34 666 789 012,Referral
Toyota,Prius,€32.750,Hybride,2022,Pierre Martin,França,Sophie Dubois,sophie.dubois@orange.fr,+33 6 78 90 12 34,Phone
Audi,A6,€48.900,Diesel,2023,Hans Schmidt,Alemanha,Klaus Weber,klaus.weber@gmx.de,+49 170 123 4567,Showroom
Fiat,500X,€22.400,Benzina,2022,Giuseppe Bianchi,Itália,Marco Rossi,marco.rossi@libero.it,+39 340 567 8901,Online Ad
```

### Target Automotive Schema
```json
{
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
python main.py harmonize examples/random_order_challenge.csv
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
- 🌍 Detects languages in column headers and data values (Spanish, Portuguese, French, German, Italian)
- 🔄 Translates non-English content to English using Google Translate
- 📝 Preserves original automotive context and technical terms
- 📊 Identifies cultural formatting differences (€28.500 vs $28,500)

### 2. Schema Mapping Agent
- 🗺️ Analyzes translated headers and maps to **automotive-specific** target fields
- 🎯 Uses fuzzy matching with automotive keywords (marca→vehicle_make, combustível→fuel_type)
- 🤖 Uses GPT-4o-mini for AI-assisted complex automotive mappings
- ❌ **Strictly rejects** unmappable fields (color, warranty, etc.) with detailed reasons

### 3. Data Validation & Enhancement Agent
- ✅ Validates mapped data against strict automotive schema
- 💰 **Price Conversion**: Converts "€28.500" strings to 28500.0 float values
- ⛽ **Fuel Normalization**: Maps "Gasolina"→"Gasoline", "Électrique"→"Electric", etc.
- 📧 **Email Validation**: Validates and normalizes customer email formats
- 📱 **Phone Normalization**: Cleans and formats phone numbers across European standards
- 🎯 **Lead Source Mapping**: Standardizes "Website", "Referral", "Phone", "Showroom", "Online Ad"
- 🌍 Enriches data (infers country from dealer names: João Silva→Portugal)
- 🛡️ Handles European number formats and currency symbols



## 🔄 Agent Communication Flow

1. **User uploads CSV** → CLI triggers processing
2. **Language Agent**: "Detected Portuguese headers: 'marca_auto', 'combustível', 'preço_venda'"
3. **Language → Schema Agent**: "Translated headers: vehicle_make→marca_auto, fuel_type→combustível, price→preço_venda"
4. **Schema Agent**: "Mapping complete: 90% confidence on 6/7 fields, 1 field rejected (cor_exterior)"
5. **Schema → Validation Agent**: "Converting prices '€28.500' → 28500.0, normalizing 'Gasolina' → 'Gasoline', validating customer emails"
6. **Validation Agent**: "Enhanced lead data: maria.santos@email.pt validated, +351 912 345 678 normalized, 'Website' standardized"
7. **Final Output**: Validated automotive lead data with strict schema compliance and clean customer information

## 📋 Usage Examples

### Basic Processing
```bash
python main.py harmonize examples/dealership_german.csv
```

### With Custom Output
```bash
python main.py harmonize examples/auto_mixed_european.csv --output processed_data.csv
```

### Verbose Mode
```bash
python main.py harmonize examples/random_order_challenge.csv --verbose
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

- ✅ **Real automotive problem** - European dealerships struggle with this daily
- 🌍 **Multi-language automotive data** - Handles Spanish, German, French, Italian, Portuguese dealer data
- 🧠 **Smart automotive inference** - Deduces missing country data from dealer names and languages
- 🔄 **Complex coordination** - Translation → Automotive Mapping → Price/Fuel Validation pipeline
- 💰 **Price string-to-float conversion** - Handles "€28.500" → 28500.0 automatically
- ⛽ **Predefined fuel mapping** - Normalizes "Gasolina"→"Gasoline", "Électrique"→"Electric"
- ❌ **Strict schema enforcement** - Rejects unmappable fields with detailed explanations
- 💼 **Immediate value** - Output is immediately usable for automotive business intelligence
- 📈 **Scalable** - Works with any European automotive dealership data format

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
- **Missing fields**: Some standard automotive fields may not be present
- **Extra fields**: Additional unmapped automotive columns (color, warranty, financing, etc.)

### 🌍 European Automotive Examples
- **🇩🇪 German BMW Dealership**: `autohaus, farbe, finanzierung` (dealership, color, financing)
- **🇮🇹 Italian Fiat Dealer**: `colore, garanzia, concessionario` (color, warranty, dealer)
- **🇫🇷 French Renault Center**: `couleur, garantie_mois, concessionnaire` (color, warranty months, dealer)
- **🇪🇸 Spanish SEAT Outlet**: `color, garantía, concesionario` (color, warranty, dealer)
- **🇵🇹 Portuguese VW Center**: `cor, garantia, revendedor` (color, warranty, reseller)
- **🇳🇱 Dutch Volvo Dealer**: `kleur, garantie, dealer` (color, warranty, dealer)
- **🇵🇱 Polish Škoda Center**: `kolor, gwarancja, dealer` (color, warranty, dealer)
- **🎯 Ultimate Challenge**: Mixed European languages with randomized column order

### ⛽ Fuel Type Mapping Examples
The system automatically normalizes fuel types across languages:
- **Gasoline**: gasoline, petrol, benzin, benzina, essence, gasolina
- **Diesel**: diesel, gasoil, gasoleo, mazut, motorina, nafta
- **Electric**: electric, elettrico, électrique, elektrisch, elétrico, elektryczny
- **Hybrid**: hybrid, ibrido, hybride, híbrido, hybryd, hybryda
- **LPG**: lpg, gpl, autogas, propane

### 💰 Price Conversion Examples
The system handles various European price formats:
- **€28.500** → 28500.0 (Portuguese/German format)
- **€28,500.00** → 28500.0 (US/UK format)
- **PLN 125,000** → 125000.0 (Polish Złoty)
- **$45,000** → 45000.0 (US Dollar)

### 🎯 Lead Source Mapping Examples
The system standardizes lead sources across languages:
- **Website**: website, site, web, online, sito web
- **Phone**: phone, telefon, téléphone, llamada, telefono
- **Referral**: referral, empfehlung, passaparola, doorverwijzing
- **Showroom**: showroom, autohaus, concessionaria, concessionário
- **Online Ad**: ad, advertisement, werbung, pubblicità, reklama

### 📧 Customer Data Validation
- **Email**: Validates format and normalizes to lowercase
- **Phone**: Cleans special characters while preserving international formats
- **Names**: Preserves original formatting and cultural characters

## 📈 Sample Output

```
🌍 Forge Agent
==================================================
📊 Input file: examples/random_order_challenge.csv
💾 Output file: examples/random_order_challenge_harmonized.csv

✅ Agents initialized successfully

🗺️  Schema Agent: Processed 8 fields - 6 mapped, 2 rejected
  ✅ 'marca_auto' -> 'vehicle_make' (confidence: 0.95)
  ✅ 'modelo_carro' -> 'vehicle_model' (confidence: 0.92)
  ✅ 'preço_venda' -> 'price' (confidence: 0.88)
  ✅ 'combustível' -> 'fuel_type' (confidence: 0.93)
  ✅ 'ano_fabrico' -> 'year' (confidence: 0.91)
  ✅ 'vendedor_nome' -> 'dealer_name' (confidence: 0.87)
  ❌ 'cor_exterior' -> REJECTED (Low confidence - not in automotive schema)
  ❌ 'país' -> REJECTED (Already mapped as inferred field)

🎉 Processing completed successfully!

📋 Summary:
  • Total records processed: 5
  • Fields mapped: 6 (including 2 rejected: cor_exterior, país)
  • Fields enriched: 1 (country inference)
  • Quality score: 1.00

👀 Data preview:
  Record 1:
    vehicle_make: Volkswagen
    vehicle_model: Golf
    price: 28500.0
    fuel_type: Gasoline
    year: 2023
    dealer_name: João Silva
    country: Portugal
    customer_name: Maria Santos
    customer_email: maria.santos@email.pt
    customer_phone: +351 912 345 678
    lead_source: Website

💾 Harmonized automotive lead data saved with strict schema compliance!
```