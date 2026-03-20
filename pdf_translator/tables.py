import logging

logger = logging.getLogger(__name__)


def identify_tables_from_page(page):
    """Detect tables using PyMuPDF's built-in table finder."""
    try:
        table_finder = page.find_tables()
        tables = []
        for table in table_finder.tables:
            table_data = table.extract()
            cleaned = []
            for row in table_data:
                cleaned_row = [cell if cell else "" for cell in row]
                if any(cell.strip() for cell in cleaned_row):
                    cleaned.append(cleaned_row)
            if cleaned:
                tables.append(cleaned)
        return tables
    except Exception as e:
        logger.warning("Table detection failed: %s. Falling back to heuristic.", e)
        return []


def identify_tables(blocks):
    """Fallback heuristic for table detection from PDF blocks."""
    tables = []
    for block in blocks:
        if block.get('type') == 0 and 'lines' in block:
            lines = block['lines']
            if len(lines) >= 2:
                multi_span_lines = sum(1 for line in lines if len(line.get('spans', [])) > 1)
                if multi_span_lines >= 2:
                    table_data = []
                    for line in lines:
                        row = [span['text'] for span in line.get('spans', []) if span['text'].strip()]
                        if row:
                            table_data.append(row)
                    if table_data:
                        tables.append(table_data)
    return tables


def extract_tables_from_page(page, blocks):
    """Extract tables — tries built-in detection first, falls back to heuristic."""
    tables = identify_tables_from_page(page)
    if not tables:
        tables = identify_tables(blocks)
    return tables
