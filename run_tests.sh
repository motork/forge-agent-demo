#!/bin/bash
# Forge Agent - Automotive Lead Data Harmonizer Test Runner
# This script runs comprehensive tests to verify the system is working correctly

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup test files
cleanup_test_files() {
    print_status "Cleaning up test files..."
    rm -f test_*.csv *_harmonized.csv
    print_success "Test files cleaned up"
}

# Function to run a test and capture output
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"

    print_step "Running: $test_name"

    if output=$(eval "$test_command" 2>&1); then
        if [[ -n "$expected_pattern" ]] && [[ ! "$output" =~ $expected_pattern ]]; then
            print_error "Test failed: Expected pattern '$expected_pattern' not found"
            echo "Output: $output"
            return 1
        else
            print_success "Test passed: $test_name"
            return 0
        fi
    else
        print_error "Test failed: $test_name"
        echo "Output: $output"
        return 1
    fi
}

# Main test runner
main() {
    echo "🧪 Forge Agent - Automotive Lead Data Harmonizer Test Suite"
    echo "==========================================================="
    echo

    # Check if we're in the right directory
    if [[ ! -f "main.py" ]] || [[ ! -f "requirements.txt" ]]; then
        print_error "Please run this script from the project root directory (mapping_demo/)"
        exit 1
    fi

    # Check for required commands
    print_step "Checking system requirements"

    if ! command_exists python3; then
        print_error "Python3 is not installed or not in PATH"
        exit 1
    fi

    if ! command_exists pip; then
        print_error "pip is not installed or not in PATH"
        exit 1
    fi

    print_success "System requirements check passed"
    echo

    # Check virtual environment
    print_step "Checking virtual environment"

    if [[ ! -d "venv" ]]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi

    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
    echo

    # Install dependencies
    print_step "Installing/updating dependencies"
    pip install -r requirements.txt > /dev/null 2>&1
    print_success "Dependencies installed"
    echo

    # Initialize test counters
    total_tests=0
    passed_tests=0
    failed_tests=0

    # Test 1: Basic import test
    total_tests=$((total_tests + 1))
    if run_test "Basic Import Test" "python tests/test_basic.py" "All basic tests passed"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 2: System configuration check
    total_tests=$((total_tests + 1))
    if run_test "System Configuration Check" "python main.py check" "System ready for harmonization"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 3: Demo data creation
    total_tests=$((total_tests + 1))
    if run_test "Demo Data Creation" "python main.py demo" "Sample CSV file created"; then
        passed_tests=$((passed_tests + 1))

        # Verify demo file was created
        if [[ -f "sample_sales_data.csv" ]]; then
            print_success "Demo CSV file exists"
        else
            print_warning "Demo CSV file was not created"
        fi
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 4: Create additional automotive test data
    print_step "Creating additional automotive test data sets"

    # Spanish automotive lead data
    cat > test_spanish_auto.csv << EOF
marca,modelo,precio,combustible,año,vendedor,cliente,email,telefono,fuente
SEAT,León,€22.300,Gasolina,2022,Carlos Vega,María González,maria.gonzalez@telefonica.es,+34 615 789 012,Teléfono
Audi,A3,€28.500,Diesel,2023,Ana López,José Martínez,jose.martinez@gmail.com,+34 622 456 789,Web
EOF

    # French automotive lead data
    cat > test_french_auto.csv << EOF
marque,modèle,prix,carburant,année,vendeur,client_nom,email_client,téléphone_client,source_lead
Renault,Clio,€19.500,Essence,2023,Pierre Martin,Sophie Dupont,sophie.dupont@orange.fr,+33 6 12 34 56 78,Site Internet
Peugeot,308,€25.800,Hybride,2022,Marie Claire,Jacques Moreau,j.moreau@free.fr,+33 6 87 65 43 21,Concession
EOF

    # German automotive lead data
    cat > test_german_auto.csv << EOF
marke,modell,preis,kraftstoff,baujahr,händler,kunde_name,kunde_email,kunde_telefon,quelle
BMW,X3,€45.900,Benzin,2023,Klaus Weber,Hans Schmidt,h.schmidt@web.de,+49 151 234 5678,Website
Volkswagen,Golf,€28.750,Diesel,2022,Wolfgang Bach,Greta Mueller,g.mueller@t-online.de,+49 172 987 6543,Empfehlung
EOF

    print_success "Test data sets created"
    echo

    # Test 5: Spanish automotive data harmonization
    total_tests=$((total_tests + 1))
    if run_test "Spanish Automotive Lead Data Harmonization" "python main.py harmonize test_spanish_auto.csv --output test_spanish_auto_harmonized.csv" "Processing completed successfully"; then
        passed_tests=$((passed_tests + 1))

        # Verify output file
        if [[ -f "test_spanish_auto_harmonized.csv" ]]; then
            print_success "Spanish automotive harmonized file created"
            # Check if it has the expected automotive headers
            if head -1 test_spanish_auto_harmonized.csv | grep -q "vehicle_make,vehicle_model,price,fuel_type,year,dealer_name,country,customer_name,customer_email,customer_phone,lead_source"; then
                print_success "Spanish automotive file has correct schema"
            else
                print_warning "Spanish automotive file schema might be incorrect"
            fi
        else
            print_warning "Spanish automotive harmonized file was not created"
        fi
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 6: French automotive data harmonization
    total_tests=$((total_tests + 1))
    if run_test "French Automotive Lead Data Harmonization" "python main.py harmonize test_french_auto.csv --output test_french_auto_harmonized.csv" "Processing completed successfully"; then
        passed_tests=$((passed_tests + 1))

        if [[ -f "test_french_auto_harmonized.csv" ]]; then
            print_success "French automotive harmonized file created"
        fi
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 7: German automotive data harmonization
    total_tests=$((total_tests + 1))
    if run_test "German Automotive Lead Data Harmonization" "python main.py harmonize test_german_auto.csv --output test_german_auto_harmonized.csv" "Processing completed successfully"; then
        passed_tests=$((passed_tests + 1))

        if [[ -f "test_german_auto_harmonized.csv" ]]; then
            print_success "German automotive harmonized file created"
        fi
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 8: Existing examples harmonization
    total_tests=$((total_tests + 1))
    if run_test "Random Order Challenge Test" "python main.py harmonize examples/random_order_challenge.csv --output test_random_harmonized.csv" "Processing completed successfully"; then
        passed_tests=$((passed_tests + 1))
        print_success "Random order challenge test passed"
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 9: Mixed European leads test
    total_tests=$((total_tests + 1))
    if run_test "Mixed European Leads Test" "python main.py harmonize examples/leads_mixed_european.csv --output test_mixed_harmonized.csv" "Processing completed successfully"; then
        passed_tests=$((passed_tests + 1))
        print_success "Mixed European leads test passed"
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 10: Verbose mode test
    total_tests=$((total_tests + 1))
    if run_test "Verbose Mode Test" "python main.py harmonize examples/dealership_german.csv --verbose" "Language Detection & Translation"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 11: Error handling test
    total_tests=$((total_tests + 1))
    if run_test "Error Handling Test" "python main.py harmonize nonexistent_file.csv" "CSV file not found"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Performance test (optional, only if files exist)
    if [[ -f "test_spanish_auto_harmonized.csv" ]]; then
        print_step "Performance Analysis"

        spanish_records=$(tail -n +2 test_spanish_auto_harmonized.csv | wc -l)
        french_records=$(tail -n +2 test_french_auto_harmonized.csv | wc -l 2>/dev/null || echo "0")
        german_records=$(tail -n +2 test_german_auto_harmonized.csv | wc -l 2>/dev/null || echo "0")
        mixed_records=$(tail -n +2 test_mixed_harmonized.csv | wc -l 2>/dev/null || echo "0")

        print_status "Automotive lead records processed:"
        echo "  - Spanish automotive: $spanish_records records"
        echo "  - French automotive: $french_records records"
        echo "  - German automotive: $german_records records"
        echo "  - Mixed European leads: $mixed_records records"
        echo
    fi

    # Summary
    echo "📊 Test Results Summary"
    echo "======================"
    echo -e "${BLUE}Total Tests:${NC} $total_tests"
    echo -e "${GREEN}Passed:${NC} $passed_tests"
    echo -e "${RED}Failed:${NC} $failed_tests"
    echo

    if [[ $failed_tests -eq 0 ]]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
        echo "The Forge Agent - Automotive Lead Data Harmonizer is working correctly."
        echo

        # Show sample output
        if [[ -f "test_spanish_auto_harmonized.csv" ]]; then
            print_step "Sample Automotive Lead Data Output Preview"
            echo "Original Spanish automotive data:"
            head -2 test_spanish_auto.csv
            echo
            echo "Harmonized automotive lead output:"
            head -2 test_spanish_auto_harmonized.csv
            echo
        fi

        cleanup_test_files
        exit 0
    else
        echo -e "${RED}❌ SOME TESTS FAILED${NC}"
        echo "Please check the error messages above and fix the issues."
        echo

        print_status "Common issues and solutions:"
        echo "1. Missing OpenAI API key: Add your key to the .env file"
        echo "2. Missing dependencies: Run 'pip install -r requirements.txt'"
        echo "3. Virtual environment issues: Ensure venv is activated"
        echo "4. Network issues: Check internet connection for translation services"
        echo "5. Automotive schema mismatch: Ensure all 11 fields are properly mapped"
        echo

        cleanup_test_files
        exit 1
    fi
}

# Handle script interruption
trap cleanup_test_files INT TERM

# Run main function
main "$@"