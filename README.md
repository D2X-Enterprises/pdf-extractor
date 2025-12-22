# 📄 Concurrent PDF OCR Extractor

<div align="center">

**Transform unsearchable PDFs into actionable text with AI-powered extraction**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tesseract](https://img.shields.io/badge/OCR-Tesseract-orange.svg)](https://github.com/tesseract-ocr/tesseract)

</div>

---

## 🎯 Overview

A powerful, production-ready Python tool designed for **writers**, **researchers**, **journalists**, and the **OSINT community** who need to quickly and accurately extract text from large volumes of scanned or image-based PDF documents.

By leveraging **concurrent processing**, **high-DPI rendering**, and **batch directory processing**, this tool transforms unsearchable PDFs into usable, indexed text for analysis and citation—complete with AI-powered name detection and comprehensive word analytics.

---

## ✨ Features

### 🚀 **Performance & Reliability**
- **⚡ Concurrent Processing** — Utilizes multiple CPU cores to process pages simultaneously, dramatically reducing extraction time
- **📁 Batch Directory Processing** — Process entire folders of PDFs automatically with uninterrupted workflow
- **🔄 Resume Capability** — Automatically detects partial output and allows resuming from the last successfully completed page
- **🎯 High Accuracy** — Renders PDF pages to high-resolution PNGs (default 300 DPI) for superior OCR results
- **🛡️ Robust Error Handling** — Continues processing even if individual files fail, with detailed error logging

### 📊 **Advanced Analytics**
- **📈 Word Count Analysis** — Generates comprehensive CSV reports with:
  - Total document word count
  - Per-page word counts
  - Individual word occurrence tracking with page numbers
  
- **👤 AI-Powered Name Detection** — Uses Named Entity Recognition (NER) to identify and track person names:
  - Occurrence counts for each name
  - Page numbers where each name appears
  - Exported to CSV for easy analysis

### 🛠️ **User-Friendly Interface**
- **💻 Command-Line Interface (CLI)** — Easy configuration via command-line arguments
- **📦 Output Consolidation** — Merges all extracted text into a single `combined_output.txt` file
- **🌍 Multi-Language Support** — Process documents in multiple languages simultaneously
- **📝 Detailed Logging** — Automatic error logging for failed documents with timestamps

---

## 📋 Prerequisites

### 🐍 **1. Python 3**

Requires **Python 3.8 or newer**

```bash
python3 --version  # Verify your Python version
```

### 🔍 **2. Tesseract OCR Engine**

Tesseract is the core OCR engine used by this script.

#### **Installation:**

**macOS** (using Homebrew):
```bash
brew install tesseract
```

**Linux** (using apt):
```bash
sudo apt install tesseract-ocr
```

**Windows**:
- Download the installer from the [Tesseract GitHub](https://github.com/tesseract-ocr/tesseract)
- Note the installation path for the `--tesseract-path` argument

#### **Language Packs:**
For languages other than English, install the corresponding Tesseract language packs:
```bash
# Example: French
sudo apt install tesseract-ocr-fra

# Example: German
sudo apt install tesseract-ocr-deu
```

### 📚 **3. Required Python Libraries**

All dependencies are listed in `requirements.txt`:

- **PyMuPDF** (fitz) — PDF rendering
- **Pillow/pytesseract** — OCR processing
- **spaCy** — Named Entity Recognition (proper name detection)

---

## 🚀 Installation & Setup

### **Option 1: Automated Setup** ⭐ **(Recommended)**

Run the installation script to automatically set up everything:

```bash
chmod +x install.sh
./install.sh
```

**This script will:**
- ✅ Check for Python and Tesseract
- ✅ Create a virtual environment
- ✅ Install all dependencies from `requirements.txt`
- ✅ Download the spaCy language model

---

### **Option 2: Manual Setup**

#### **Step 1: Clone the Repository**

```bash
git clone <repository-url>
cd pdf-extractor
```

#### **Step 2: Create Virtual Environment**

It is **highly recommended** to use a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows (CMD):
venv\Scripts\activate

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

#### **Step 3: Install Dependencies**

```bash
# Install Python packages
pip install -r requirements.txt

# Download spaCy language model for name detection
python -m spacy download en_core_web_sm
```

---

## 💻 Usage

### **Basic Execution**

#### **Single PDF File:**
Run the script with the path to your PDF file:

```bash
python pdf_extractor.py path/to/your/document.pdf
```

**The script will:**
1. ✅ Check for previous progress
2. ✅ Prompt you to process all pages, resume, or select a specific range

#### **Directory of PDFs (Batch Mode):** 🆕
Process all PDFs in a directory automatically:

```bash
python pdf_extractor.py path/to/pdf_folder/
```

**In batch mode, the script will:**
1. ✅ Automatically detect all PDF files in the directory
2. ✅ Process each PDF with ALL pages (no prompts)
3. ✅ Continue processing even if individual files fail
4. ✅ Log errors to `error_log.txt` in the source directory
5. ✅ Provide a comprehensive summary at completion

---

### **Resume an Interrupted Job**

If processing was interrupted, simply rerun the command:

```bash
python pdf_extractor.py my_long_report.pdf
```

**Example output:**
```
Found existing files. Last successfully processed page was 50 of 100.
Enter 'r' to resume at page 51, 'a' for all, 'n' for a new range, or 'q' to quit: r
```

> **Note:** Resume capability is available for single PDF files only. In batch mode, each PDF starts fresh.

---

### **⚙️ Advanced Arguments**

Customize processing with these optional flags:

| Argument | Default | Description |
|----------|---------|-------------|
| **`[PDF_PATH]`** | *Required* | Path to input PDF file **OR** directory containing PDFs |
| `--output-dir` | `.` | Base directory where processing folders will be created |
| `--dpi` | `300` | Rendering quality (DPI). Higher = better OCR but slower |
| `--lang` | `eng` | Tesseract language code(s). Use `+` to combine (e.g., `eng+deu`) |
| `--tesseract-path` | `/usr/bin/tesseract` | Full path to Tesseract executable (crucial for Windows) |

---

### **📝 Command Examples**

#### **1. Single PDF - High-Quality Processing (600 DPI) with Multiple Languages:**

```bash
python pdf_extractor.py thesis.pdf --dpi 600 --lang eng+fra
```

When prompted:
```
Enter 'a' for all pages, 'n' for a new range (e.g., 5-10), or 'q' to quit: n
Enter page range (e.g., 5-10): 1-50
```

#### **2. Batch Processing - Entire Directory:**

```bash
python pdf_extractor.py ./research_papers/ --dpi 300 --lang eng
```

**Output:**
```
======================================================================
BATCH PROCESSING MODE
======================================================================
Found 5 PDF file(s) in directory: ./research_papers/
Processing mode: ALL PAGES (automatic for batch mode)
======================================================================

Processing PDF 1/5: paper_001.pdf
[Processing details...]
✓ SUCCESS: paper_001.pdf completed successfully

Processing PDF 2/5: paper_002.pdf
[Processing details...]
✓ SUCCESS: paper_002.pdf completed successfully
...
```

#### **3. Windows with Custom Tesseract Path:**

```bash
python pdf_extractor.py my_doc.pdf --tesseract-path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

#### **4. Batch Processing with Custom Output Directory:**

```bash
python pdf_extractor.py ./invoices/ --output-dir ./processed_invoices --dpi 300
```

---

## 📂 Output Structure

### **Single PDF Output:**

A new directory named `<pdf_name>_processed` will be created:

```
<pdf_name>_processed/
├── 📄 combined_output.txt          # Final merged text document
├── 📊 word_count_report.csv        # Word count analysis
├── 👤 proper_names_report.csv      # AI-detected person names
├── 🖼️  png_images/
│   ├── 0001.png
│   ├── 0002.png
│   └── ...
└── 📝 text_files/
    ├── 0001.txt                    # Text output for page 1
    ├── 0002.txt                    # Text output for page 2
    └── ...
```

### **Batch Processing Output:**

When processing a directory, each PDF gets its own output folder:

```
output_directory/
├── document1_processed/
│   ├── combined_output.txt
│   ├── word_count_report.csv
│   ├── proper_names_report.csv
│   ├── png_images/
│   └── text_files/
├── document2_processed/
│   └── ...
└── document3_processed/
    └── ...
```

### **Error Logging (Batch Mode):** 🆕

If any PDFs fail during batch processing, errors are logged in the source directory:

```
source_directory/
├── document1.pdf
├── document2.pdf
├── corrupted.pdf
└── error_log.txt              # ← Detailed error information
```

**Error log format:**
```
======================================================================
[2024-12-21 14:30:45] ERROR processing: corrupted.pdf
----------------------------------------------------------------------
PyPdfError: EOF marker not found
======================================================================
```

> **💡 Note:** If a page fails OCR, its `.txt` file will contain an "OCR FAILED" marker with the error message. Failed pages are automatically skipped during consolidation.

---

## 📊 CSV Reports

The extractor automatically generates two powerful CSV reports for analysis:

### **1. 📈 Word Count Report** (`word_count_report.csv`)

Provides comprehensive word statistics:

#### **Document Summary Section:**
- 📖 Total word count across all pages
- 📄 Number of pages analyzed
- 🔤 Count of unique words

#### **Per-Page Word Counts:**
- 📊 Individual word count for each page

#### **Word Occurrence Details:**
- 🔍 Every unique word (3+ characters)
- 🔢 Total occurrences
- 📍 All page numbers where it appears

**Example:**
```csv
Word,Total Occurrences,Pages
dog,75,"3, 36, 73, 89, 102"
cat,42,"5, 12, 89"
research,156,"1, 2, 5, 8, 12, 15, 23, 45, 67, 89"
```

---

### **2. 👤 Proper Names Report** (`proper_names_report.csv`)

Identifies person names using **AI-powered Named Entity Recognition**:

#### **Contents:**
- 👥 Person names detected in the document
- 🔢 Total occurrences for each name
- 📍 All page numbers where the name appears
- 📊 Sorted by frequency (most common first)

**Example:**
```csv
Name,Total Occurrences,Pages
John Smith,92,"254, 340, 533, 678"
Jane Doe,45,"12, 89, 234, 456"
Dr. Sarah Johnson,23,"5, 67, 89"
```

> **⚠️ Note:** Proper name detection requires spaCy and the English language model. If not installed, this feature will be skipped with a warning message.

---

## 🔄 Batch Processing Workflow

### **Example Scenario:**

You have a folder of 50 scanned research papers that need OCR processing.

```bash
# Step 1: Organize PDFs
mkdir research_papers
cp *.pdf research_papers/

# Step 2: Run batch processing
python pdf_extractor.py research_papers/ --dpi 300 --output-dir ./extracted

# Step 3: Review results
ls extracted/
# Shows: paper1_processed/, paper2_processed/, etc.

# Step 4: Check for errors (if any)
cat research_papers/error_log.txt
```

### **Batch Processing Features:**

✅ **Automatic Processing** — No manual intervention required  
✅ **Error Resilience** — Failed PDFs don't stop the batch  
✅ **Detailed Logging** — Know exactly what succeeded and what failed  
✅ **Progress Tracking** — See real-time progress for each PDF  
✅ **Summary Report** — Comprehensive statistics at completion  

---

## 🐛 Troubleshooting

### **Q: What happens if one PDF in a batch is corrupted?**
**A:** The script logs the error to `error_log.txt` in the source directory and continues processing the remaining PDFs. You can review the error log after completion and re-process failed files individually if needed.

### **Q: Can I resume a failed batch?**
**A:** Simply re-run the same command. The script will skip PDFs that already have complete output directories, effectively resuming where it left off.

### **Q: How do I process only specific pages in batch mode?**
**A:** Batch mode always processes ALL pages automatically. For page-specific processing, process files individually instead.

### **Q: Where do error logs go?**
**A:** Error logs are saved as `error_log.txt` in the **source directory** (where the PDFs are located), not in the output directory.

### **Q: Can I process subdirectories?**
**A:** Not currently—only PDFs in the specified directory are processed (non-recursive). Subdirectories are not scanned.

### **Q: What if processing is too slow?**
**A:** Try reducing the `--dpi` value (e.g., `--dpi 200`). Lower DPI means faster processing but slightly reduced OCR accuracy.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Tesseract OCR** — Google's powerful open-source OCR engine
- **PyMuPDF** — Fast and efficient PDF rendering
- **spaCy** — Industrial-strength Natural Language Processing

---

<div align="center">

**Made with ❤️ for the research and OSINT community**

⭐ Star this repo if you find it useful!

</div>
