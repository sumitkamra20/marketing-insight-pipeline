#!/usr/bin/env python3
"""
Data Conversion and Schema Analysis for ELT Pipeline
This script converts .xls/.xlsx files to CSV, loads all CSV files into pandas dataframes,
and provides schema analysis for Snowflake table design.
"""

import pandas as pd
import os
from pathlib import Path
import json
from typing import Dict, Any, List

class DataConversionAndSchema:
    def __init__(self, data_dir: str = "../data/raw"):
        self.data_dir = data_dir
        self.dataframes = {}
        self.schemas = {}

    def convert_excel_to_csv(self, excel_file_path: str, output_dir: str = None) -> str:
        """
        Convert Excel file to CSV format.

        Args:
            excel_file_path: Path to the Excel file
            output_dir: Directory to save the CSV file (default: same as Excel file)

        Returns:
            Path to the created CSV file
        """
        if output_dir is None:
            output_dir = os.path.dirname(excel_file_path)

        # Read Excel file
        df = pd.read_excel(excel_file_path)

        # Create CSV filename
        excel_filename = os.path.basename(excel_file_path)
        csv_filename = excel_filename.replace('.xlsx', '.csv').replace('.xls', '.csv')
        csv_path = os.path.join(output_dir, csv_filename)

        # Convert to CSV
        df.to_csv(csv_path, index=False)

        print(f"✓ Converted {excel_filename} to {csv_filename}")
        return csv_path

    def convert_all_excel_files(self) -> List[str]:
        """
        Convert all Excel files in the data directory to CSV.

        Returns:
            List of converted CSV file paths
        """
        excel_files = []
        for file_path in Path(self.data_dir).glob("*.xlsx"):
            excel_files.append(str(file_path))
        for file_path in Path(self.data_dir).glob("*.xls"):
            excel_files.append(str(file_path))

        print(f"Found {len(excel_files)} Excel files to convert:")
        for file in excel_files:
            print(f"  - {os.path.basename(file)}")

        converted_files = []
        for excel_file in excel_files:
            csv_file = self.convert_excel_to_csv(excel_file)
            converted_files.append(csv_file)

        return converted_files

    def load_csv_to_dataframes(self) -> Dict[str, pd.DataFrame]:
        """
        Load all CSV files into pandas dataframes.

        Returns:
            Dictionary with table names as keys and dataframes as values
        """
        csv_files = list(Path(self.data_dir).glob("*.csv"))

        print(f"\nLoading {len(csv_files)} CSV files into pandas dataframes:")

        for csv_file in csv_files:
            table_name = csv_file.stem  # filename without extension
            try:
                df = pd.read_csv(csv_file)
                self.dataframes[table_name] = df
                print(f"✓ Loaded {table_name}: {len(df):,} rows × {len(df.columns)} columns")
            except Exception as e:
                print(f"✗ Error loading {csv_file}: {str(e)}")

        return self.dataframes

    def analyze_schema(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Analyze schema of a dataframe for Snowflake design.

        Args:
            df: Pandas dataframe
            table_name: Name of the table

        Returns:
            Schema information dictionary
        """
        schema_info = {
            'table_name': table_name.upper(),
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': {}
        }

        for column in df.columns:
            # Basic statistics
            col_info = {
                'column_name': column.replace(' ', '_').replace('-', '_').upper(),
                'pandas_dtype': str(df[column].dtype),
                'null_count': int(df[column].isnull().sum()),
                'null_percentage': float((df[column].isnull().sum() / len(df)) * 100),
                'unique_values': int(df[column].nunique()),
                'sample_values': df[column].dropna().head(3).tolist()
            }

            # Snowflake data type mapping
            if df[column].dtype == 'object':
                max_length = df[column].astype(str).str.len().max()
                if pd.isna(max_length):
                    max_length = 1
                col_info['snowflake_type'] = f'VARCHAR({int(max_length)})'
            elif df[column].dtype in ['int64', 'int32', 'int16', 'int8']:
                col_info['snowflake_type'] = 'NUMBER'
            elif df[column].dtype in ['float64', 'float32']:
                col_info['snowflake_type'] = 'FLOAT'
            elif 'datetime' in str(df[column].dtype).lower():
                col_info['snowflake_type'] = 'TIMESTAMP'
            elif df[column].dtype == 'bool':
                col_info['snowflake_type'] = 'BOOLEAN'
            else:
                col_info['snowflake_type'] = 'VARIANT'

            schema_info['columns'][column] = col_info

        return schema_info

    def generate_snowflake_ddl(self, schema_info: Dict[str, Any]) -> str:
        """
        Generate Snowflake DDL statement from schema information.

        Args:
            schema_info: Schema information dictionary

        Returns:
            DDL statement string
        """
        table_name = schema_info['table_name']
        ddl = f"CREATE OR REPLACE TABLE {table_name} (\n"

        columns = []
        for col_name, col_info in schema_info['columns'].items():
            clean_col_name = col_info['column_name']
            nullable = "NULL" if col_info['null_count'] > 0 else "NOT NULL"
            columns.append(f"    {clean_col_name} {col_info['snowflake_type']} {nullable}")

        ddl += ",\n".join(columns)
        ddl += "\n);"

        return ddl

    def print_schema_summary(self):
        """Print a summary of all schemas for Snowflake design."""
        print("\n" + "="*80)
        print("SCHEMA ANALYSIS FOR SNOWFLAKE TABLE DESIGN")
        print("="*80)

        for table_name, schema in self.schemas.items():
            print(f"\n📊 TABLE: {schema['table_name']}")
            print(f"   Rows: {schema['total_rows']:,} | Columns: {schema['total_columns']}")
            print("-" * 60)

            for col_name, col_info in schema['columns'].items():
                null_indicator = "🔴" if col_info['null_count'] > 0 else "🟢"
                print(f"   {col_info['column_name']:<20} {col_info['snowflake_type']:<15} {null_indicator} "
                      f"({col_info['unique_values']} unique)")

            print(f"\n📝 Snowflake DDL:")
            print(self.generate_snowflake_ddl(schema))

    def export_schemas_to_json(self, filename: str = "table_schemas.json"):
        """Export all schema information to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.schemas, f, indent=2, default=str)
        print(f"\n💾 Schema information exported to: {filename}")

    def run_full_analysis(self):
        """Run the complete data conversion and schema analysis process."""
        print("🔄 Starting Data Conversion and Schema Analysis")
        print("="*60)

        # Step 1: Convert Excel files
        converted_files = self.convert_all_excel_files()

        # Step 2: Load all CSV files into dataframes
        self.load_csv_to_dataframes()

        # Step 3: Analyze schema for each dataframe
        print(f"\n🔍 Analyzing schemas for {len(self.dataframes)} tables:")
        for table_name, df in self.dataframes.items():
            schema = self.analyze_schema(df, table_name)
            self.schemas[table_name] = schema
            print(f"✓ Analyzed schema for {table_name}")

        # Step 4: Display results
        self.print_schema_summary()

        # Step 5: Export to JSON
        self.export_schemas_to_json()

        print(f"\n✅ Analysis complete! Processed {len(self.dataframes)} tables.")
        print(f"📁 Dataframes available in .dataframes dict")
        print(f"📋 Schemas available in .schemas dict")

def main():
    """Main function to run data conversion and schema analysis."""
    analyzer = DataConversionAndSchema()
    analyzer.run_full_analysis()

    # Return the analyzer object for interactive use
    return analyzer

if __name__ == "__main__":
    analyzer = main()
