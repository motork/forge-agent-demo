#!/bin/bash
# Smart International Sales Data Harmonizer - Test Runner
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
    echo "🧪 Smart International Sales Data Harmonizer - Test Suite"
    echo "======================================================="
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

    # Test 4: Create additional test data
    print_step "Creating additional test data sets"

    # Spanish test data
    cat > test_spanish.csv << EOF
cliente,producto,cantidad,precio_unitario,fecha_venta,vendedor
María González,Laptop HP,1,850.00,2024-02-01,Carlos Ruiz
José Martínez,Tablet Samsung,2,300.50,2024-02-02,Ana López
EOF

    # French test data
    cat > test_french.csv << EOF
client,produit,quantité,prix_unitaire,date_vente,vendeur
Pierre Dupont,Ordinateur Dell,1,1100.00,2024-02-03,Marie Claire
Jacques Moreau,Souris Logitech,5,25.99,2024-02-04,Jean Bonnet
EOF

    # German test data
    cat > test_german.csv << EOF
kunde,produkt,menge,einzelpreis,verkaufsdatum,verkäufer
Hans Schmidt,Computer Asus,1,950.00,2024-02-05,Klaus Weber
Greta Mueller,Tastatur Microsoft,3,45.50,2024-02-06,Wolfgang Bach
EOF

    print_success "Test data sets created"
    echo

    # Test 5: Spanish data harmonization
    total_tests=$((total_tests + 1))
    if run_test "Spanish Data Harmonization" "python main.py harmonize test_spanish.csv --output test_spanish_harmonized.csv" "Processing completed successfully"; then
        passed_tests=$((passed_tests + 1))

        # Verify output file
        if [[ -f "test_spanish_harmonized.csv" ]]; then
            print_success "Spanish harmonized file created"
            # Check if it has the expected headers
            if head -1 test_spanish_harmonized.csv | grep -q "customer_name,product_name,quantity,unit_price,sale_date,sales_rep,country"; then
                print_success "Spanish file has correct schema"
            else
                print_warning "Spanish file schema might be incorrect"
            fi
        else
            print_warning "Spanish harmonized file was not created"
        fi
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 6: French data harmonization
    total_tests=$((total_tests + 1))
    if run_test "French Data Harmonization" "python main.py harmonize test_french.csv --output test_french_harmonized.csv" "Processing completed successfully"; then
        passed_tests=$((passed_tests + 1))

        if [[ -f "test_french_harmonized.csv" ]]; then
            print_success "French harmonized file created"
        fi
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 7: German data harmonization
    total_tests=$((total_tests + 1))
    if run_test "German Data Harmonization" "python main.py harmonize test_german.csv --output test_german_harmonized.csv" "Processing completed successfully"; then
        passed_tests=$((passed_tests + 1))

        if [[ -f "test_german_harmonized.csv" ]]; then
            print_success "German harmonized file created"
        fi
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 8: Verbose mode test
    total_tests=$((total_tests + 1))
    if run_test "Verbose Mode Test" "python main.py harmonize sample_sales_data.csv --verbose" "Language Detection & Translation"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Test 9: Error handling test
    total_tests=$((total_tests + 1))
    if run_test "Error Handling Test" "python main.py harmonize nonexistent_file.csv" "CSV file not found"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    echo

    # Performance test (optional, only if files exist)
    if [[ -f "test_spanish_harmonized.csv" ]]; then
        print_step "Performance Analysis"

        spanish_records=$(tail -n +2 test_spanish_harmonized.csv | wc -l)
        french_records=$(tail -n +2 test_french_harmonized.csv | wc -l 2>/dev/null || echo "0")
        german_records=$(tail -n +2 test_german_harmonized.csv | wc -l 2>/dev/null || echo "0")

        print_status "Records processed:"
        echo "  - Spanish: $spanish_records records"
        echo "  - French: $french_records records"
        echo "  - German: $german_records records"
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
        echo "The Smart International Sales Data Harmonizer is working correctly."
        echo

        # Show sample output
        if [[ -f "test_spanish_harmonized.csv" ]]; then
            print_step "Sample Output Preview"
            echo "Original Spanish data:"
            head -2 test_spanish.csv
            echo
            echo "Harmonized output:"
            head -2 test_spanish_harmonized.csv
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
        echo

        cleanup_test_files
        exit 1
    fi
}

# Handle script interruption
trap cleanup_test_files INT TERM

# Run main function
main "$@"