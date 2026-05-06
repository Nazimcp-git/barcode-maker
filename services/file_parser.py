"""
Data Input Parser.

Handles all data input methods for QR code generation:
- Numeric ranges with prefix/suffix
- CSV file parsing
- Excel file parsing
- Manual text input
"""
import os
import pandas as pd


def parse_range(start, end, step=1, prefix='', suffix=''):
    """
    Generate a list of values from a numeric range with optional prefix/suffix.

    Args:
        start (int): Start of range (inclusive).
        end (int): End of range (inclusive).
        step (int): Increment step (default 1).
        prefix (str): Text to prepend to each value.
        suffix (str): Text to append to each value.

    Returns:
        list[str]: List of formatted values.

    Raises:
        ValueError: If range parameters are invalid.
    """
    if step <= 0:
        raise ValueError("Step must be a positive integer.")
    if start > end:
        raise ValueError("Start must be less than or equal to end.")
    if (end - start) / step > 50000:
        raise ValueError("Range would generate more than 50,000 items. Please reduce the range.")

    values = []
    current = start
    while current <= end:
        values.append(f"{prefix}{current}{suffix}")
        current += step

    return values


def parse_csv(file_path, column_name=None):
    """
    Parse a CSV file and extract values from a specified column.

    Args:
        file_path (str): Path to the CSV file.
        column_name (str, optional): Column to extract. If None, uses first column.

    Returns:
        list[str]: List of values from the specified column.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the column doesn't exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError("CSV file is empty.")

    if column_name and column_name in df.columns:
        values = df[column_name].dropna().astype(str).tolist()
    elif column_name:
        raise ValueError(f"Column '{column_name}' not found. Available columns: {list(df.columns)}")
    else:
        # Use first column
        values = df.iloc[:, 0].dropna().astype(str).tolist()

    return values


def parse_excel(file_path, sheet_name=None, column_name=None):
    """
    Parse an Excel file and extract values from a specified column.

    Args:
        file_path (str): Path to the Excel file.
        sheet_name (str, optional): Sheet name. If None, uses first sheet.
        column_name (str, optional): Column to extract. If None, uses first column.

    Returns:
        list[str]: List of values from the specified column.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the sheet or column doesn't exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    kwargs = {'engine': 'openpyxl'}
    if sheet_name:
        kwargs['sheet_name'] = sheet_name

    df = pd.read_excel(file_path, **kwargs)

    if df.empty:
        raise ValueError("Excel file is empty.")

    if column_name and column_name in df.columns:
        values = df[column_name].dropna().astype(str).tolist()
    elif column_name:
        raise ValueError(f"Column '{column_name}' not found. Available columns: {list(df.columns)}")
    else:
        values = df.iloc[:, 0].dropna().astype(str).tolist()

    return values


def parse_text(text):
    """
    Parse manual text input (one value per line).

    Args:
        text (str): Multi-line text input.

    Returns:
        list[str]: List of non-empty, trimmed values.
    """
    if not text or not text.strip():
        return []

    lines = text.strip().split('\n')
    values = [line.strip() for line in lines if line.strip()]
    return values


def get_file_columns(file_path):
    """
    Get column names from a CSV or Excel file.

    Args:
        file_path (str): Path to the file.

    Returns:
        dict: {'columns': list[str], 'preview': list[list], 'total_rows': int}
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext in ('.xlsx', '.xls'):
        df = pd.read_excel(file_path, engine='openpyxl')
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    columns = list(df.columns)
    # Get first 10 rows as preview
    preview = df.head(10).fillna('').astype(str).values.tolist()
    total_rows = len(df)

    return {
        'columns': columns,
        'preview': preview,
        'total_rows': total_rows,
    }
