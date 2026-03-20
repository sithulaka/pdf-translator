import logging

logger = logging.getLogger(__name__)


def identify_tables(blocks):
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
    """Extract tables — tries heuristic for now. Phase 2 will add page.find_tables()."""
    return identify_tables(blocks)
