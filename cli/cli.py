#!/usr/bin/env python3
"""
Forge Agent CLI
A team of AI agents that harmonizes multi-language sales CSV files.
"""

import asyncio
import click
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for required environment variables
if not os.getenv("OPENAI_API_KEY"):
    click.echo("❌ Error: OPENAI_API_KEY not found in environment variables.")
    click.echo("Please add your OpenAI API key to the .env file.")
    sys.exit(1)

from core.harmonizer_v2 import create_harmonizer


@click.group()
def cli():
    """Forge Agent

    A team of AI agents that takes messy, multi-language sales CSV files
    and intelligently maps them to a unified global schema.
    """
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output CSV file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def harmonize(input_file, output, verbose):
    """Process a multi-language sales CSV file through the agent pipeline.

    INPUT_FILE: Path to the CSV file to process
    """

    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    click.echo("🌍 Forge Agent")
    click.echo("=" * 50)

    # Generate output filename if not provided
    if not output:
        input_path = Path(input_file)
        output = input_path.parent / f"{input_path.stem}_harmonized.csv"

    click.echo(f"📊 Input file: {input_file}")
    click.echo(f"💾 Output file: {output}")
    click.echo("")

    async def process():
        harmonizer = None
        try:
            # Initialize harmonizer
            with click.progressbar(length=100, label='Initializing agents') as bar:
                harmonizer = await create_harmonizer()
                bar.update(100)

            click.echo("✅ Agents initialized successfully")
            click.echo("")

            # Process the CSV
            with click.progressbar(length=100, label='Processing CSV') as bar:
                result = await harmonizer.process_csv(input_file, str(output))
                bar.update(100)

            # Display results
            if result["success"]:
                click.echo("🎉 Processing completed successfully!")
                click.echo("")
                click.echo("📋 Summary:")
                summary = result["summary"]
                click.echo(f"  • Total records processed: {summary['total_records']}")
                click.echo(f"  • Fields mapped: {summary['fields_mapped']}")
                click.echo(f"  • Fields rejected: {summary.get('fields_rejected', 0)}")
                click.echo(f"  • Fields enriched: {summary['fields_enriched']}")
                click.echo(f"  • Quality score: {summary['quality_score']:.2f}")
                click.echo("")

                if result["data_preview"]:
                    click.echo("👀 Data preview (first 3 records):")
                    for i, record in enumerate(result["data_preview"], 1):
                        click.echo(f"  Record {i}:")
                        for field, value in record.items():
                            click.echo(f"    {field}: {value}")
                        click.echo("")

                click.echo(f"💾 Harmonized data saved to: {output}")
            else:
                click.echo(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        except Exception as e:
            click.echo(f"❌ Error: {str(e)}")
            sys.exit(1)
        finally:
            if harmonizer:
                await harmonizer.shutdown()

    # Run the async process
    asyncio.run(process())


@cli.command()
def demo():
    """Create a sample multi-language CSV file for testing."""
    sample_data = [
        ["cliente", "producto", "cantidad", "precio_unitario", "fecha_venta", "vendedor"],
        ["María García", "Laptop Dell", "2", "899.99", "2024-01-15", "Carlos"],
        ["Jean Dubois", "Ordinateur HP", "1", "1200.50", "2024-01-16", "Pierre"],
        ["Hans Mueller", "Computer Lenovo", "3", "750.00", "2024-01-17", "Klaus"],
        ["Giovanni Rossi", "Notebook Asus", "1", "680.00", "2024-01-18", "Marco"],
        ["António Silva", "Computador Apple", "2", "1500.00", "2024-01-19", "João"]
    ]

    filename = "sample_sales_data.csv"

    import csv
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)

    click.echo(f"✅ Sample CSV file created: {filename}")
    click.echo("")
    click.echo("This file contains sales data in multiple languages:")
    click.echo("  • Spanish: María García, Carlos")
    click.echo("  • French: Jean Dubois, Pierre")
    click.echo("  • German: Hans Mueller, Klaus")
    click.echo("  • Italian: Giovanni Rossi, Marco")
    click.echo("  • Portuguese: António Silva, João")
    click.echo("")
    click.echo("Try running: python main.py harmonize sample_sales_data.csv")


@cli.command()
def check():
    """Check system requirements and configuration."""
    click.echo("🔍 Checking system configuration...")
    click.echo("")

    # Check Python version
    import sys
    click.echo(f"Python version: {sys.version}")

    # Check required packages
    required_packages = [
        'autogen_agentchat',
        'openai',
        'pandas',
        'langdetect',
        'googletrans',
        'dotenv',
        'click',
        'pydantic'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            click.echo(f"✅ {package}: installed")
        except ImportError:
            click.echo(f"❌ {package}: missing")
            missing_packages.append(package)

    click.echo("")

    # Check environment variables
    if os.getenv("OPENAI_API_KEY"):
        click.echo("✅ OPENAI_API_KEY: configured")
    else:
        click.echo("❌ OPENAI_API_KEY: missing")
        click.echo("   Add your OpenAI API key to the .env file")

    if os.getenv("OPENAI_MODEL"):
        click.echo(f"✅ OPENAI_MODEL: {os.getenv('OPENAI_MODEL')}")
    else:
        click.echo("⚠️  OPENAI_MODEL: using default (gpt-4o-mini)")

    click.echo("")

    if missing_packages:
        click.echo("❌ Missing packages detected. Run:")
        click.echo("   pip install -r requirements.txt")
        sys.exit(1)
    elif not os.getenv("OPENAI_API_KEY"):
        click.echo("❌ Configuration incomplete. Please set OPENAI_API_KEY.")
        sys.exit(1)
    else:
        click.echo("🎉 System ready for harmonization!")


if __name__ == '__main__':
    cli()