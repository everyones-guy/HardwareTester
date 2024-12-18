import pdfplumber
import csv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def parse_pdf(file_path):
    """
    Parse a test plan PDF and extract structured data.
    :param file_path: Path to the PDF file.
    :return: List of steps extracted from the PDF.
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {"error": "File not found"}

    steps = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.splitlines():
                        steps.append(line.strip())
        logging.info(f"Parsed {len(steps)} steps from PDF: {file_path}")
        return steps
    except Exception as e:
        logging.error(f"Error parsing PDF: {e}")
        return {"error": str(e)}

def parse_csv(file_path):
    """
    Parse a test plan CSV and extract structured data.
    :param file_path: Path to the CSV file.
    :return: List of steps extracted from the CSV.
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {"error": "File not found"}

    steps = []
    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                steps.append(row)
        logging.info(f"Parsed {len(steps)} steps from CSV: {file_path}")
        return steps
    except Exception as e:
        logging.error(f"Error parsing CSV: {e}")
        return {"error": str(e)}

def parse_text(file_path):
    """
    Parse a test plan in plain text format.
    :param file_path: Path to the text file.
    :return: List of steps extracted from the text file.
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {"error": "File not found"}

    steps = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            steps = [line.strip() for line in file.readlines()]
        logging.info(f"Parsed {len(steps)} steps from text file: {file_path}")
        return steps
    except Exception as e:
        logging.error(f"Error parsing text file: {e}")
        return {"error": str(e)}

def parse_file(file_path):
    """
    Generic file parser that selects the correct parser based on file extension.
    :param file_path: Path to the file.
    :return: Parsed data from the file.
    """
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return parse_pdf(file_path)
    elif extension == ".csv":
        return parse_csv(file_path)
    elif extension in [".txt", ".log"]:
        return parse_text(file_path)
    else:
        logging.error(f"Unsupported file type: {extension}")
        return {"error": f"Unsupported file type: {extension}"}
