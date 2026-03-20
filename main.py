import os
import sys
from pdf_translator.translator import extract_pdf_content, translate_text, save_translated_text_as_file

def process_pdfs(input_folder, output_folder):
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        sys.exit(1)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in '{input_folder}'.")
        return

    total_files = len(pdf_files)
    print(f"Found {total_files} PDF file(s) to process.\n")

    for file_idx, file_name in enumerate(pdf_files, 1):
        pdf_path = os.path.join(input_folder, file_name)
        output_file_path = os.path.join(output_folder, file_name.rsplit('.', 1)[0] + '.txt')

        print(f"[{file_idx}/{total_files}] Processing: {file_name}")

        try:
            # Extract content from the PDF
            pages_content = extract_pdf_content(pdf_path)
            print(f"  Extracted {len(pages_content)} page(s)")

            # Translate the content
            translated_texts = []
            for page_num, (text, _) in enumerate(pages_content, 1):
                print(f"  Translating page {page_num}/{len(pages_content)}...")
                translated_texts.append(translate_text(text))

            # Save the translated content to a text file
            save_translated_text_as_file(output_file_path, pages_content, translated_texts)
            print(f"  Saved: {output_file_path}\n")

        except Exception as e:
            print(f"  Error processing '{file_name}': {e}\n")
            continue

    print("Done.")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(base_dir, 'input_pdfs')
    output_folder = os.path.join(base_dir, 'output_texts')
    process_pdfs(input_folder, output_folder)

if __name__ == "__main__":
    main()
