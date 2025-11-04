"""
Output formatting utilities
"""

import json
import csv
import sys
from typing import List, Dict, Any
from tabulate import tabulate
from leadsauce.utils.config import get_config


def format_table(data: List[Dict[str, Any]], headers: List[str], tablefmt: str = 'grid') -> str:
    """
    Format data as table

    Args:
        data: List of dictionaries with data
        headers: List of column headers
        tablefmt: Table format (grid, simple, plain, etc.)

    Returns:
        Formatted table string
    """
    if not data:
        return "No data to display"

    rows = []
    for item in data:
        row = [item.get(h, '-') for h in headers]
        rows.append(row)

    return tabulate(rows, headers=headers, tablefmt=tablefmt)


def format_json(data: Any, indent: int = 2) -> str:
    """
    Format data as JSON

    Args:
        data: Data to format
        indent: JSON indentation

    Returns:
        JSON string
    """
    return json.dumps(data, indent=indent, default=str)


def format_csv(data: List[Dict[str, Any]], headers: List[str], output_file: str = None) -> str:
    """
    Format data as CSV

    Args:
        data: List of dictionaries with data
        headers: List of column headers
        output_file: Optional file path to write CSV

    Returns:
        CSV string or None if written to file
    """
    if not data:
        return ""

    if output_file:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        return None
    else:
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()


def format_output(data: Any, format_type: str = None, headers: List[str] = None) -> str:
    """
    Format output based on configuration or specified format

    Args:
        data: Data to format
        format_type: Output format (table, json, csv, text)
        headers: Column headers for table/CSV format

    Returns:
        Formatted output string
    """
    if format_type is None:
        config = get_config()
        format_type = config.get('output.format', 'table')

    if format_type == 'json':
        if isinstance(data, list):
            return format_json(data)
        elif isinstance(data, dict):
            return format_json(data)
        else:
            return format_json({'result': data})

    elif format_type == 'csv':
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if headers is None:
                headers = list(data[0].keys())
            return format_csv(data, headers)
        else:
            return str(data)

    elif format_type == 'table':
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if headers is None:
                headers = list(data[0].keys())
            return format_table(data, headers)
        else:
            return str(data)

    else:  # text
        return str(data)


def print_success(message: str):
    """Print success message in green"""
    from click import secho
    secho(f"✓ {message}", fg='green')


def print_error(message: str):
    """Print error message in red"""
    from click import secho
    secho(f"✗ {message}", fg='red')


def print_warning(message: str):
    """Print warning message in yellow"""
    from click import secho
    secho(f"⚠ {message}", fg='yellow')


def print_info(message: str):
    """Print info message in cyan"""
    from click import secho
    secho(f"ℹ {message}", fg='cyan')


def truncate_string(s: str, max_length: int = 50) -> str:
    """Truncate string to max length"""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."


def format_date(dt, format_str: str = None) -> str:
    """Format datetime object"""
    from leadsauce.utils.constants import DATE_FORMAT, DATETIME_FORMAT

    if dt is None:
        return "Never"

    if format_str is None:
        format_str = DATETIME_FORMAT if hasattr(dt, 'hour') else DATE_FORMAT

    return dt.strftime(format_str)


def format_boolean(value: bool) -> str:
    """Format boolean value"""
    return "Yes" if value else "No"


def format_list(items: List[Any], separator: str = ", ", max_items: int = None) -> str:
    """Format list as string"""
    if not items:
        return "-"

    if max_items and len(items) > max_items:
        items = items[:max_items]
        return separator.join(str(i) for i in items) + f" (+{len(items) - max_items} more)"

    return separator.join(str(i) for i in items)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def paginate_output(items: List[Any], page: int = 1, per_page: int = 50) -> tuple:
    """
    Paginate list of items

    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (paginated_items, total_pages, current_page)
    """
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return items[start_idx:end_idx], total_pages, page
