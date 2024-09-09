# PDF Translator

## Overview

PDF Translator is a Python-based tool designed to extract text from PDF documents, translate it into Sinhala using Google Translator, and save the translated content in a well-structured text file format. This tool is ideal for users who need to convert large volumes of PDF content into another language while preserving the structure of tables and pages.

## Features

- **Text Extraction:** Extracts text from PDF files while preserving layout information.
- **Translation:** Utilizes Google Translator for translating extracted text into Sinhala.
- **Table Identification:** Detects and formats tables from the PDF content.
- **File Management:** Saves translated content into text files, maintaining the structure of the original PDF.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Folder Structure](#folder-structure)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Clone the Repository

```bash
git clone https://github.com/sithulaka/pdf-translator.git
cd pdf-translator
```

### Set Up a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Install Dependencies

Install the required Python packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Usage

1. **Place your PDF files** in the `input_pdfs/` folder.

2. **Run the script** to process the PDFs and generate translated text files:

   ```bash
   python main.py
   ```

3. **Check the output** in the `output_texts/` folder. Each PDF will have a corresponding `.txt` file with the translated content.

### Example

To translate a PDF named `example.pdf`, place it in the `input_pdfs/` folder and run:

```bash
python main.py
```

The translated text will be saved as `example.txt` in the `output_texts/` folder.

## Folder Structure

```
pdf_translator_project/
├── pdf_translator/
│   ├── __init__.py
│   ├── translator.py
├── input_pdfs/
├── output_texts/
├── requirements.txt
├── README.md
└── main.py
```

- **`pdf_translator/`**: Contains the core translation and extraction logic.
- **`input_pdfs/`**: Folder for input PDF files.
- **`output_texts/`**: Folder where the translated text files will be saved.
- **`requirements.txt`**: Lists the dependencies required for the project.
- **`README.md`**: Provides an overview and instructions for the project.
- **`main.py`**: The entry point script for processing PDFs.

## Contributing

We welcome contributions to improve this project. To contribute:

1. **Fork the repository** and create a new branch.
2. **Make your changes** and test them thoroughly.
3. **Submit a pull request** with a description of the changes.

Please ensure that your contributions adhere to the project's coding standards and include tests where applicable.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your improvements or bug fixes.

## Connect with me
<p align="left">
<a href="https://linkedin.com/in/sithulaka" target="blank"><img align="center" src="https://github.com/sithulaka/sithulaka/blob/main/image/icon/linked-in-alt.svg" alt="sithulaka" height="30" width="40" /></a>
<a href="https://twitter.com/sithulaka" target="blank"><img align="center" src="https://github.com/sithulaka/sithulaka/blob/main/image/icon/twitter.svg" alt="sithulaka" height="30" width="40" /></a>
<a href="https://fb.com/senithu.sithulaka.7" target="blank"><img align="center" src="https://github.com/sithulaka/sithulaka/blob/main/image/icon/facebook.svg" alt="sithulaka" height="30" width="40" /></a>
<a href="https://instagram.com/_sithulaka_" target="blank"><img align="center" src="https://github.com/sithulaka/sithulaka/blob/main/image/icon/instagram.svg" alt="sithulaka" height="30" width="40" /></a>
<!-- <a href="https://discord.gg/ugdvth5b6H" target="blank"><img align="center" src="https://github.com/sithulaka/sithulaka/blob/main/image/icon/discord.svg" alt="sithulaka" height="30" width="40" /></a> -->
</p><br>
