import os
from pdf_translator.translator import extract_pdf_content, translate_text, save_translated_text_as_file

def process_pdfs(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file_name in os.listdir(input_folder):
        if file_name.endswith('.pdf'):
            pdf_path = os.path.join(input_folder, file_name)
            output_file_path = os.path.join(output_folder, file_name.replace('.pdf', '.txt'))

            # Extract content from the PDF
            pages_content = extract_pdf_content(pdf_path)
            
            # Translate the content
            translated_texts = [translate_text(text) for text, _ in pages_content]
            
            # Save the translated content to a text file
            save_translated_text_as_file(output_file_path, pages_content, translated_texts)
            
            print(f"Translated text file saved to {output_file_path}")

def main():
    input_folder = 'input_pdfs'
    output_folder = 'output_texts'
    process_pdfs(input_folder, output_folder)

if __name__ == "__main__":
    main()
