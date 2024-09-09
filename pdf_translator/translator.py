import fitz  # PyMuPDF to handle PDF
from deep_translator import GoogleTranslator

def translate_text(text, target_lang='si'):
    translator = GoogleTranslator(source='auto', target=target_lang)
    return translator.translate(text)

def extract_pdf_content(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text = page.get_text("text")  # Extract as readable text format
        blocks = page.get_text("dict")['blocks']  # Extract layout blocks (to identify tables)
        pages.append((text, blocks))
    
    return pages

def identify_tables(blocks):
    tables = []
    for block in blocks:
        if block.get('type') == 1 and 'lines' in block:  # Type 1 indicates a table block
            lines = block['lines']
            table_data = []
            for line in lines:
                row = [span['text'] for span in line['spans']]
                table_data.append(row)
            tables.append(table_data)
    return tables

def save_translated_text_as_file(file_path, pages_content, translated_texts):
    with open(file_path, 'w', encoding='utf-8') as file:
        for i, (original_text, blocks) in enumerate(pages_content):
            translated_text = translated_texts[i]

            # Write translated text to file
            file.write(f"--- Page {i + 1} ---\n")
            file.write(translated_text + "\n")
            file.write("\n")

            # Write tables to file
            tables = identify_tables(blocks)
            for table_data in tables:
                for row in table_data:
                    file.write(" | ".join(row) + "\n")
                file.write("\n")
            
            # Add a page break
            file.write("\n\n")
