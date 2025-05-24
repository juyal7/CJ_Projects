import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Any

# Compile regex patterns once for better performance
DATE_PATTERN = re.compile(r'\[([\d-]+)\s+([\d:.]+)\]')
OFFSET_PATTERN = re.compile(r'\(\+([\d.]+)\)')
IDENTIFIER_PATTERN = re.compile(r'([a-zA-Z0-9-]+)\s+([a-zA-Z0-9_]+):([a-zA-Z0-9_]+):')
KV_PATTERN = re.compile(r'([a-zA-Z0-9_]+)\s*=\s*("(?:[^"\\]|\\.)*"|[^,\s]+)')

def parse_telecom_log_file(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Parse telecom log file and return a DataFrame with structured data.
    
    Args:
        file_path: Path to the log file
        
    Returns:
        pd.DataFrame: Structured data from log file
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")
    
    log_entries: List[Dict[str, Any]] = []
    
    with file_path.open('r') as file:
        for line in file:
            if not line.strip():
                continue
                
            entry = _parse_log_line(line)
            if entry:
                log_entries.append(entry)
    
    # Create DataFrame and optimize column types
    df = pd.DataFrame(log_entries)
    _optimize_dataframe(df)
    
    return df

def _parse_log_line(line: str) -> Dict[str, Any]:
    """
    Parse a single log line and extract structured data.
    
    Args:
        line: Single line from log file
        
    Returns:
        dict: Extracted data from log line
    """
    entry: Dict[str, Any] = {}
    
    # Extract timestamp
    if date_match := DATE_PATTERN.search(line):
        entry['date'] = date_match.group(1)
        entry['time'] = date_match.group(2)
        entry['timestamp'] = f"{date_match.group(1)} {date_match.group(2)}"
    
    # Extract offset
    if offset_match := OFFSET_PATTERN.search(line):
        entry['offset'] = float(offset_match.group(1))
    
    # Extract identifier components
    if identifier_match := IDENTIFIER_PATTERN.search(line):
        entry['system'] = identifier_match.group(1)
        entry['component'] = identifier_match.group(2)
        entry['event_type'] = identifier_match.group(3)
    
    # Extract key-value pairs
    _parse_key_value_pairs(line, entry)
    
    return entry

def _parse_key_value_pairs(line: str, entry: Dict[str, Any]) -> None:
    """
    Parse key-value pairs from log line and add to entry dictionary.
    
    Args:
        line: Log line containing key-value pairs
        entry: Dictionary to store parsed values
    """
    for key, value in KV_PATTERN.findall(line):
        # Clean up the value
        value = value.strip('"')
        
        # Convert to appropriate type
        try:
            if value.isdigit():
                value = int(value)
            elif re.match(r'^-?\d+\.\d+$', value):
                value = float(value)
        except (ValueError, AttributeError):
            pass
        
        entry[key] = value

def _optimize_dataframe(df: pd.DataFrame) -> None:
    """
    Optimize DataFrame memory usage by setting appropriate column types.
    
    Args:
        df: DataFrame to optimize
    """
    # Convert string columns to category type
    string_columns = ['system', 'component', 'event_type', 'date', 'time']
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype('category')
    
    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

def save_to_excel(df: pd.DataFrame, output_path: Union[str, Path]) -> None:
    """
    Save DataFrame to Excel file with optimized column widths.
    
    Args:
        df: DataFrame to save
        output_path: Path to save Excel file
    """
    output_path = Path(output_path)
    
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Log Data', index=False)
            
            worksheet = writer.sheets['Log Data']
            for idx, col in enumerate(df.columns):
                # Calculate optimal width (max 50 characters)
                max_length = min(
                    max(
                        df[col].astype(str).str.len().max(),
                        len(str(col))
                    ) + 2,
                    50
                )
                col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx//26) + chr(65 + (idx % 26))
                worksheet.column_dimensions[col_letter].width = max_length
    
    except Exception as e:
        raise IOError(f"Failed to save Excel file: {e}")

def main() -> None:
    """Main execution function with error handling."""
    try:
        input_file = Path("c:/Users/Chanchal Juyal/CJ_Projects/test.py")
        output_file = Path("telecom_log_data.xlsx")
        
        print(f"Parsing log file: {input_file}")
        df = parse_telecom_log_file(input_file)
        
        print(f"Extracted {len(df):,} log entries with {len(df.columns)} fields")
        print(f"Fields found: {', '.join(df.columns)}")
        
        print(f"Saving data to Excel: {output_file}")
        save_to_excel(df, output_file)
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
