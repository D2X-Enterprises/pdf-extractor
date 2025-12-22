import os
import pathlib
import fitz # PyMuPDF library for PDF manipulation
import pytesseract # Python wrapper for Tesseract OCR
from PIL import Image # Pillow library for image handling (used by pytesseract)
import time
import sys # Used for exiting the script
import concurrent.futures # Used for multithreaded processing
import argparse # NEW: For command-line arguments
import contextlib # NEW: For suppressing warnings
import csv # For CSV report generation
import re # For word tokenization
from collections import defaultdict # For word occurrence tracking
from datetime import datetime # For timestamping error logs
try:
    import spacy # For Named Entity Recognition (proper names)
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# --- Configuration Defaults (used if not overridden by CLI) ---
DEFAULT_TESSERACT_PATH = '/usr/bin/tesseract' 
DEFAULT_LANGUAGES = 'eng'
DEFAULT_DPI = 300 # Equivalent to zoom=4 (300/72 ~ 4.16)

# Global configuration dictionary populated by argparse and the interactive loop
GLOBAL_CONFIG = {
    'pdf_path': None,
    'output_dir': '.',
    'dpi': DEFAULT_DPI,
    'languages': DEFAULT_LANGUAGES,
    'tesseract_path': DEFAULT_TESSERACT_PATH,
    'start_page': 1,
    'end_page': None,
    'batch_mode': False  # NEW: Flag for directory processing
}

# --- Tesseract Warning Suppression Context Manager (Suggestion 3) ---
@contextlib.contextmanager
def suppress_stderr():
    """Context manager to suppress stderr output (Tesseract warnings)."""
    # Save the current stderr
    original_stderr = sys.stderr
    try:
        # Redirect stderr to /dev/null
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        # Restore the original stderr
        sys.stderr.close()
        sys.stderr = original_stderr


# Function to encapsulate single-page processing for concurrency
def process_page_task(pdf_path: str, page_num: int, output_dir: pathlib.Path, matrix: fitz.Matrix, languages: str) -> tuple[bool, int, str]:
    """
    Handles the PNG extraction and OCR for a single, 0-based page index.
    Returns (success_status, page_index, error_message or None). (Suggestion 1)
    """
    page_index = page_num + 1 # 1-based index for naming and logging
    
    # Directory setup (assuming they exist from process_pdf)
    png_dir = output_dir / "png_images"
    txt_dir = output_dir / "text_files"
    
    png_filepath = png_dir / f"{page_index:04d}.png"
    txt_filepath = txt_dir / f"{page_index:04d}.txt"

    # Optimization: Skip if page is already fully processed
    if png_filepath.exists() and txt_filepath.exists():
        return (True, page_index, None)
    
    doc = None # Initialize outside try
    try:
        # Load page from PDF (must be done inside the thread)
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        
        # --- 1. Extract Page as PNG ---
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pix.save(str(png_filepath))
        
        # --- 2. Convert PNG to TXT using OCR (with warning suppression) ---
        with suppress_stderr(): # Suggestion 3 implemented
            text = pytesseract.image_to_string(str(png_filepath), lang=languages)

        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(text.strip())
        
        return (True, page_index, None)

    except Exception as e:
        # Suggestion 1: Capture specific error details
        error_msg = f"OCR failed: {type(e).__name__}: {str(e)}"
        # Create a failure file for tracking
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(f"OCR FAILED FOR THIS PAGE: {error_msg}")
        return (False, page_index, error_msg)

    finally:
        if doc:
            doc.close()


def get_last_processed_page(output_dir: pathlib.Path) -> int:
    """
    Checks the output directory for existing PNG and TXT files in their respective
    subdirectories to determine the last successfully processed page number.
    Returns 0 if no files are found.
    """
    png_dir = output_dir / "png_images"
    txt_dir = output_dir / "text_files"
    
    if not png_dir.exists() or not txt_dir.exists():
        return 0

    processed_pages = set()
    
    for f in png_dir.iterdir():
        if f.suffix == '.png' and f.stem.isdigit():
            page_num_str = f.stem
            txt_path = txt_dir / f"{page_num_str}.txt"
            
            # A page is considered complete only if both files exist
            if txt_path.exists():
                processed_pages.add(int(page_num_str))

    if not processed_pages:
        return 0
    
    return max(processed_pages)

def generate_word_count_csv(output_dir: pathlib.Path, start_page: int, end_page: int):
    """
    Generates a comprehensive CSV report with word count statistics:
    1. Total document word count
    2. Per-page word counts
    3. Word occurrence tracking with page numbers
    """
    txt_dir = output_dir / "text_files"
    csv_file = output_dir / "word_count_report.csv"
    
    print(f"\n--- Generating Word Count CSV Report ---")
    
    # Data structures for tracking
    total_words = 0
    page_word_counts = {}  # {page_num: word_count}
    word_occurrences = defaultdict(lambda: {'count': 0, 'pages': set()})  # {word: {'count': int, 'pages': set}}
    
    # Process each text file
    for page_index in range(start_page, end_page + 1):
        filename = f"{page_index:04d}.txt"
        filepath = txt_dir / filename
        
        if not filepath.exists():
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Skip failed OCR pages
                if "OCR FAILED" in content:
                    continue
                
                # Extract words using regex (alphanumeric sequences)
                words = re.findall(r'\b[a-zA-Z0-9]+\b', content.lower())
                
                # Filter out very short words (optional, reduces noise)
                words = [w for w in words if len(w) > 2]
                
                # Update page word count
                page_word_count = len(words)
                page_word_counts[page_index] = page_word_count
                total_words += page_word_count
                
                # Track individual word occurrences
                for word in words:
                    word_occurrences[word]['count'] += 1
                    word_occurrences[word]['pages'].add(page_index)
                    
        except Exception as e:
            print(f"Warning: Could not process {filepath.name} for word count: {e}")
            continue
    
    if total_words == 0:
        print("No words found to analyze.")
        return
    
    # Write CSV report
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Section 1: Document Summary
            writer.writerow(['=== DOCUMENT SUMMARY ==='])
            writer.writerow(['Type', 'Value'])
            writer.writerow(['Total Words', total_words])
            writer.writerow(['Total Pages Analyzed', len(page_word_counts)])
            writer.writerow(['Unique Words', len(word_occurrences)])
            writer.writerow([])  # Blank line
            
            # Section 2: Per-Page Word Counts
            writer.writerow(['=== PER-PAGE WORD COUNTS ==='])
            writer.writerow(['Page Number', 'Word Count'])
            for page_num in sorted(page_word_counts.keys()):
                writer.writerow([page_num, page_word_counts[page_num]])
            writer.writerow([])  # Blank line
            
            # Section 3: Word Occurrence Details
            writer.writerow(['=== WORD OCCURRENCE DETAILS ==='])
            writer.writerow(['Word', 'Total Occurrences', 'Pages'])
            
            # Sort by occurrence count (descending)
            sorted_words = sorted(
                word_occurrences.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            
            for word, data in sorted_words:
                pages_str = ', '.join(map(str, sorted(data['pages'])))
                writer.writerow([word, data['count'], pages_str])
        
        print(f"Word count report saved: {csv_file}")
        
    except Exception as e:
        print(f"Error generating word count CSV: {e}")

def generate_proper_names_csv(output_dir: pathlib.Path, start_page: int, end_page: int):
    """
    Uses spaCy NER to identify PERSON entities (proper names) and generates a CSV report
    tracking their occurrences and page locations.
    """
    if not SPACY_AVAILABLE:
        print("\n--- Proper Names Report Skipped ---")
        print("spaCy not installed. Install with: pip install spacy && python -m spacy download en_core_web_sm")
        return
        
    txt_dir = output_dir / "text_files"
    csv_file = output_dir / "proper_names_report.csv"
    
    print(f"\n--- Generating Proper Names CSV Report (AI-Powered) ---")
    
    try:
        # Load spaCy model
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("spaCy model 'en_core_web_sm' not found.")
        print("Install with: python -m spacy download en_core_web_sm")
        return
    
    # Data structure: {name: {'count': int, 'pages': set}}
    person_names = defaultdict(lambda: {'count': 0, 'pages': set()})
    
    # Process each text file
    for page_index in range(start_page, end_page + 1):
        filename = f"{page_index:04d}.txt"
        filepath = txt_dir / filename
        
        if not filepath.exists():
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Skip failed OCR pages
                if "OCR FAILED" in content:
                    continue
                
                # Process with spaCy (chunk large texts if needed)
                # For very large pages, process in chunks to avoid memory issues
                max_length = nlp.max_length  # Default is usually 1,000,000 characters
                
                if len(content) > max_length:
                    # Process in chunks
                    chunks = [content[i:i+max_length] for i in range(0, len(content), max_length)]
                    for chunk in chunks:
                        doc = nlp(chunk)
                        for ent in doc.ents:
                            if ent.label_ == "PERSON":
                                name = ent.text.strip()
                                if name:  # Ignore empty strings
                                    person_names[name]['count'] += 1
                                    person_names[name]['pages'].add(page_index)
                else:
                    doc = nlp(content)
                    for ent in doc.ents:
                        if ent.label_ == "PERSON":
                            name = ent.text.strip()
                            if name:
                                person_names[name]['count'] += 1
                                person_names[name]['pages'].add(page_index)
                    
        except Exception as e:
            print(f"Warning: Could not process {filepath.name} for proper names: {e}")
            continue
    
    if not person_names:
        print("No person names detected.")
        return
    
    # Write CSV report
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            writer.writerow(['=== PROPER NAMES REPORT (AI-Detected) ==='])
            writer.writerow(['Name', 'Total Occurrences', 'Pages'])
            
            # Sort by occurrence count (descending)
            sorted_names = sorted(
                person_names.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            
            for name, data in sorted_names:
                pages_str = ', '.join(map(str, sorted(data['pages'])))
                writer.writerow([name, data['count'], pages_str])
        
        print(f"Proper names report saved: {csv_file}")
        print(f"Total unique names detected: {len(person_names)}")
        
    except Exception as e:
        print(f"Error generating proper names CSV: {e}")


def combine_text_files(output_dir: pathlib.Path, start_page: int, end_page: int):
    """
    Combines all individual text files from the 'text_files' subdirectory 
    into a single 'combined_output.txt' file, skipping pages that failed OCR.
    """
    txt_dir = output_dir / "text_files"
    output_file = output_dir / "combined_output.txt"
    
    print(f"\n--- Combining Text Files ---")
    
    combined_content = []
    skipped_pages = []
    
    for page_index in range(start_page, end_page + 1):
        filename = f"{page_index:04d}.txt"
        filepath = txt_dir / filename
        
        if not filepath.exists():
            skipped_pages.append(page_index)
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check if the page failed OCR
                if "OCR FAILED" in content:
                    skipped_pages.append(page_index)
                    continue
                
                # Add page delimiter and content
                combined_content.append(f"--- Page {page_index} ---\n")
                combined_content.append(content)
                combined_content.append("\n\n")
        except Exception as e:
            print(f"Warning: Could not read {filepath.name}: {e}")
            skipped_pages.append(page_index)
            continue
    
    if not combined_content:
        print("No text content to combine. All pages may have failed OCR.")
        return
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(combined_content)
        print(f"Combined text file saved: {output_file}")
        
        if skipped_pages:
            print(f"Note: {len(skipped_pages)} page(s) were skipped (failed OCR or missing).")
    except Exception as e:
        print(f"Error writing combined output file: {e}")


def process_pdf(config: dict):
    """
    Main processing function: Extracts PNG images and performs OCR 
    for a specified page range using concurrent threading.
    Handles both single page ranges and resume functionality.
    """
    pdf_path = config['pdf_path']
    output_dir = pathlib.Path(config['output_dir'])
    dpi = config['dpi']
    languages = config['languages']
    start_page = config['start_page']
    end_page = config['end_page']
    
    # Tesseract configuration
    pytesseract.pytesseract.tesseract_cmd = config['tesseract_path']
    
    # Create subdirectories for PNGs and text files
    png_dir = output_dir / "png_images"
    txt_dir = output_dir / "text_files"
    png_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate PyMuPDF matrix from DPI
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    
    print(f"\n--- Starting PDF Processing ---")
    print(f"Input: {pdf_path}")
    print(f"Output directory: {output_dir}")
    print(f"DPI: {dpi}")
    print(f"Languages: {languages}")
    print(f"Processing pages {start_page} to {end_page}")
    print(f"Using {os.cpu_count() or 4} CPU cores for concurrent processing.")
    
    try:
        # Generate 0-based indices for pages to process
        pages_to_process_indices = list(range(start_page - 1, end_page))
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
            
            # Submit tasks for each page index
            futures = [
                executor.submit(process_page_task, pdf_path, page_num, output_dir, matrix, languages)
                for page_num in pages_to_process_indices
            ]
            
            # Wait for all futures to complete (Suggestion 1: detailed error logging)
            success_count = 0
            failure_count = 0
            failure_messages = []
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    success, page_index, error_msg = future.result()
                    if success:
                        # Avoid printing success messages from threads, rely on final count
                        if error_msg is None: # Only count as success if it wasn't a skipped, already-processed page
                            success_count += 1 
                        # Print progress for pages that actually needed processing
                        print(f"  [SUCCESS] Page {page_index:04d} processed.")

                    else:
                        failure_count += 1
                        failure_messages.append(f"Page {page_index:04d}: {error_msg}")
                        print(f"  [FAILURE] Page {page_index:04d} failed. See full details below.")
                except Exception as e:
                    print(f"A thread encountered an unexpected execution error: {e}")
                    failure_count += 1

        end_time = time.time()
        duration = end_time - start_time
        print("\n--- Processing Complete ---")
        print(f"Total time: {duration:.2f} seconds.")
        print(f"Pages successful: {success_count}. Pages failed: {failure_count}.")
        
        # Log all specific failures (Suggestion 1 continued)
        if failure_messages:
            print("\n--- DETAILED FAILURE REPORT ---")
            for msg in failure_messages:
                print(f"- {msg}")
            print("-------------------------------\n")


        # Run the combination step only if there were successful extractions
        if success_count > 0:
            combine_text_files(output_dir, start_page, end_page)
            # Generate word count CSV report
            generate_word_count_csv(output_dir, start_page, end_page)
            # Generate proper names CSV report
            generate_proper_names_csv(output_dir, start_page, end_page)

    except Exception as e:
        print(f"\nAn unexpected error occurred during main execution: {e}")
        raise  # Re-raise for batch mode error handling


def log_error_to_file(pdf_path: pathlib.Path, error_message: str):
    """
    Logs error details to error_log.txt in the same directory as the failed PDF.
    """
    log_file = pdf_path.parent / "error_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"[{timestamp}] ERROR processing: {pdf_path.name}\n")
            f.write(f"{'-'*70}\n")
            f.write(f"{error_message}\n")
            f.write(f"{'='*70}\n\n")
    except Exception as e:
        print(f"WARNING: Could not write to error log: {e}")


def process_single_pdf(pdf_path: pathlib.Path, base_output_dir: str, config: dict) -> tuple[bool, str]:
    """
    Process a single PDF file with error handling for batch mode.
    Returns (success: bool, error_message: str or None)
    """
    try:
        safe_name = pdf_path.stem.replace(' ', '_')
        output_dir = pathlib.Path(base_output_dir) / f"{safe_name}_processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get total pages
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        doc.close()
        
        if total_pages == 0:
            return False, "PDF contains 0 pages"
        
        # Set up config for this PDF
        pdf_config = config.copy()
        pdf_config['pdf_path'] = str(pdf_path)
        pdf_config['output_dir'] = str(output_dir)
        pdf_config['start_page'] = 1
        pdf_config['end_page'] = total_pages
        
        # Process the PDF
        process_pdf(pdf_config)
        return True, None
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        return False, error_msg


def process_directory(directory_path: pathlib.Path, config: dict):
    """
    Process all PDF files in a directory sequentially.
    Logs errors and continues processing remaining files.
    """
    # Find all PDF files in the directory
    pdf_files = sorted(list(directory_path.glob("*.pdf")) + list(directory_path.glob("*.PDF")))
    
    if not pdf_files:
        print(f"\nNo PDF files found in directory: {directory_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING MODE")
    print(f"{'='*70}")
    print(f"Found {len(pdf_files)} PDF file(s) in directory: {directory_path}")
    print(f"Processing mode: ALL PAGES (automatic for batch mode)")
    print(f"{'='*70}\n")
    
    # Track results
    results = {
        'successful': [],
        'failed': []
    }
    
    start_time = time.time()
    
    # Process each PDF
    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n{'#'*70}")
        print(f"Processing PDF {idx}/{len(pdf_files)}: {pdf_path.name}")
        print(f"{'#'*70}")
        
        success, error_msg = process_single_pdf(pdf_path, config['output_dir'], config)
        
        if success:
            results['successful'].append(pdf_path.name)
            print(f"\n✓ SUCCESS: {pdf_path.name} completed successfully")
        else:
            results['failed'].append((pdf_path.name, error_msg))
            print(f"\n✗ FAILURE: {pdf_path.name} encountered an error")
            print(f"Error: {error_msg}")
            
            # Log error to file
            log_error_to_file(pdf_path, error_msg)
            print(f"Error details logged to: {pdf_path.parent / 'error_log.txt'}")
    
    # Print summary
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"Total time: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    print(f"Total PDFs processed: {len(pdf_files)}")
    print(f"Successful: {len(results['successful'])}")
    print(f"Failed: {len(results['failed'])}")
    
    if results['successful']:
        print(f"\n✓ Successfully processed files:")
        for filename in results['successful']:
            print(f"  - {filename}")
    
    if results['failed']:
        print(f"\n✗ Failed files:")
        for filename, error in results['failed']:
            print(f"  - {filename}")
            print(f"    Error: {error}")
        print(f"\nDetailed error logs available in: {directory_path / 'error_log.txt'}")
    
    print(f"{'='*70}\n")


def setup_and_run():
    """Handles command-line parsing and main interactive loop."""
    
    # Setup Argument Parser (Suggestion 4: Argparse)
    parser = argparse.ArgumentParser(
        description="Concurrent PDF to PNG and OCR Text Extractor with resume support and batch directory processing.",
        epilog="""Examples:
  Single file:    python pdf_extractor.py my_book.pdf --dpi 600 --lang eng+deu
  Directory:      python pdf_extractor.py /path/to/pdfs/ --dpi 300
  
When processing a directory, all PDFs will be processed automatically with ALL pages.""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        'pdf_path',
        type=str,
        help="Path to the input PDF file OR directory containing PDFs (e.g., 'document.pdf' or '/path/to/pdfs/')."
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help="Base directory for output (default: current directory). Output folder is '<pdf_name>_processed'."
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=DEFAULT_DPI,
        help=f"Rendering quality in DPI (default: {DEFAULT_DPI}). Higher DPI = better OCR but slower processing."
    )
    parser.add_argument(
        '--lang',
        type=str,
        default=DEFAULT_LANGUAGES,
        help=f"Tesseract languages (default: '{DEFAULT_LANGUAGES}'). Use '+' to combine (e.g., 'eng+fra'). Requires language packs to be installed."
    )
    parser.add_argument(
        '--tesseract-path',
        type=str,
        default=DEFAULT_TESSERACT_PATH,
        help=f"Full path to the Tesseract executable (default: '{DEFAULT_TESSERACT_PATH}')."
    )

    args = parser.parse_args()

    # Apply parsed arguments to config
    GLOBAL_CONFIG['pdf_path'] = args.pdf_path
    GLOBAL_CONFIG['output_dir'] = args.output_dir
    GLOBAL_CONFIG['dpi'] = args.dpi
    GLOBAL_CONFIG['languages'] = args.lang
    GLOBAL_CONFIG['tesseract_path'] = args.tesseract_path
    
    # --- File/Directory Checks ---
    input_path = pathlib.Path(GLOBAL_CONFIG['pdf_path'])
    
    if not input_path.exists():
        print(f"Error: Path not found at '{GLOBAL_CONFIG['pdf_path']}'.")
        sys.exit(1)
    
    # Check if input is a directory or file
    if input_path.is_dir():
        # BATCH MODE: Process all PDFs in directory
        GLOBAL_CONFIG['batch_mode'] = True
        process_directory(input_path, GLOBAL_CONFIG)
        
    elif input_path.is_file():
        # SINGLE FILE MODE: Original interactive processing
        if input_path.suffix.lower() != '.pdf':
            print(f"Error: File must be a PDF. Got: {input_path.suffix}")
            sys.exit(1)
        
        pdf_file = input_path
        safe_name = pdf_file.stem.replace(' ', '_')
        output_dir = pathlib.Path(GLOBAL_CONFIG['output_dir']) / f"{safe_name}_processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n--- PDF Extractor Setup ---")
        
        # Get total pages and last processed page
        try:
            doc = fitz.open(GLOBAL_CONFIG['pdf_path'])
            total_pages = len(doc)
            doc.close()
        except Exception as e:
            print(f"Error reading PDF: {e}")
            sys.exit(1)

        GLOBAL_CONFIG['end_page'] = total_pages
        last_page = get_last_processed_page(output_dir)
        
        # Interactive menu for range/resume selection
        if last_page > 0:
            print(f"Found existing files. Last successfully processed page was {last_page} of {total_pages}.")
            mode_prompt = f"Enter 'r' to resume at page {last_page + 1}, 'a' for all, 'n' for a new range, or 'q' to quit: "
        else:
            print(f"PDF contains {total_pages} pages. No existing output found.")
            mode_prompt = "Enter 'a' for all pages, 'r' for a range (e.g., 5-10), or 'q' to quit: "

        
        while True:
            try:
                mode = input(mode_prompt).strip().lower()
                
                start_page = 1
                
                if mode == 'q':
                    print("Exiting script.")
                    sys.exit(0)
                
                elif mode == 'r':
                    if last_page > 0:
                        start_page = last_page + 1
                        if start_page > total_pages:
                            print("All pages already processed!")
                            sys.exit(0)
                        print(f"RESUMING processing from page {start_page} to {total_pages}.")
                        break
                    else:
                        print("No previous progress found. Please choose 'a' or enter a range.")
                        # Fallback to the initial prompt if 'r' is chosen with no history
                        mode_prompt = "Enter 'a' for all pages, 'r' for a range (e.g., 5-10), or 'q' to quit: "
                        continue
                
                elif mode == 'a':
                    start_page = 1
                    print(f"Processing ALL pages: 1 to {total_pages}.")
                    break

                elif mode == 'n' or ('-' in mode and mode != 'r'):
                    if mode == 'n':
                        range_input = input(f"Enter new page range (e.g., '1-{total_pages}'): ").strip()
                    else:
                        range_input = mode
                        
                    start_str, end_str = range_input.split('-')
                    start_page_input = int(start_str)
                    end_page_input = int(end_str)

                    # Validation against PDF limits
                    if not (1 <= start_page_input <= end_page_input <= total_pages):
                        print(f"Error: Invalid page range '{range_input}'. Range must be between 1 and {total_pages}.")
                        continue
                    
                    start_page = start_page_input
                    GLOBAL_CONFIG['end_page'] = end_page_input # Override end_page for this specific range
                    print(f"Processing selected range: Page {start_page} to {end_page_input}.")
                    break

                else:
                    print("Invalid command.")
                    
            except ValueError:
                print("Invalid input for range. Please use format 'START-END' or a command like 'a', 'r', 'n', or 'q'.")
            except Exception as e:
                print(f"An error occurred during setup: {e}")
                sys.exit(1)

        GLOBAL_CONFIG['start_page'] = start_page
        GLOBAL_CONFIG['output_dir'] = str(output_dir)
        
        # Run the main processing function
        process_pdf(GLOBAL_CONFIG)
    
    else:
        print(f"Error: Path is neither a file nor a directory: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    setup_and_run()
