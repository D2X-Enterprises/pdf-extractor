# PDF Extractor - Batch Processing Update

## New Features Added

This update adds comprehensive **batch directory processing** capabilities to your PDF extractor tool. Here's what's new:

---

## 🎯 Key Features

### 1. **Directory Processing Mode**
- You can now pass a **directory path** instead of a single PDF file
- The script will automatically detect all PDF files in the directory (both `.pdf` and `.PDF` extensions)
- PDFs are processed sequentially, one at a time

### 2. **Automatic "All Pages" Mode**
- When processing a directory, the script **automatically** processes ALL pages of each PDF
- No interactive prompts for page ranges - fully automated batch processing
- This ensures uninterrupted processing of large batches

### 3. **Comprehensive Error Handling**
- If a PDF fails during processing, the script:
  - ✅ Logs the error details to `error_log.txt` in the **PDF's directory**
  - ✅ Displays an on-screen error message
  - ✅ Continues processing the remaining PDFs without interruption
- Error log includes:
  - Timestamp
  - PDF filename
  - Detailed error message

### 4. **Batch Processing Summary**
- At the end of batch processing, you get a comprehensive summary:
  - Total processing time
  - Number of successful PDFs
  - Number of failed PDFs
  - List of successful files
  - List of failed files with error messages

---

## 📖 Usage Examples

### **Single PDF (Original Behavior)**
```bash
# Interactive mode with page range selection
python pdf_extractor.py document.pdf

# With custom settings
python pdf_extractor.py document.pdf --dpi 600 --lang eng+fra
```

### **Directory of PDFs (NEW!)**
```bash
# Process all PDFs in a directory
python pdf_extractor.py /path/to/pdf_folder/

# With custom settings
python pdf_extractor.py /path/to/pdf_folder/ --dpi 300 --lang eng
```

### **Example Directory Structure**
```
my_pdfs/
├── document1.pdf
├── document2.pdf
├── document3.pdf
└── report.pdf
```

**Command:**
```bash
python pdf_extractor.py my_pdfs/ --output-dir ./processed_output
```

**Result:**
```
processed_output/
├── document1_processed/
│   ├── combined_output.txt
│   ├── word_count_report.csv
│   ├── proper_names_report.csv
│   ├── png_images/
│   └── text_files/
├── document2_processed/
│   └── ...
├── document3_processed/
│   └── ...
└── report_processed/
    └── ...
```

If any PDF fails, you'll find:
```
my_pdfs/
└── error_log.txt  ← Detailed error information
```

---

## 🔍 What Happens During Batch Processing

1. **Discovery**: Script finds all PDF files in the specified directory
2. **Processing**: Each PDF is processed sequentially:
   - All pages are automatically extracted
   - PNG images and OCR text files are generated
   - Combined text file and CSV reports are created
3. **Error Handling**: If a PDF fails:
   - Error is logged to `error_log.txt`
   - On-screen message displays the error
   - Processing continues with the next PDF
4. **Summary**: Final report shows success/failure statistics

---

## 📋 Error Log Format

When errors occur, they're logged in this format:

```
======================================================================
[2024-12-21 14:30:45] ERROR processing: corrupted_file.pdf
----------------------------------------------------------------------
PyPdfError: EOF marker not found
======================================================================
```

This makes it easy to:
- Identify which PDFs had issues
- Understand what went wrong
- Re-process specific failed files later

---

## ⚙️ Command-Line Options (All Modes)

| Option | Default | Description |
|--------|---------|-------------|
| `pdf_path` | *Required* | Path to PDF file OR directory |
| `--output-dir` | `.` | Base directory for all output folders |
| `--dpi` | `300` | Rendering quality (higher = better OCR, slower) |
| `--lang` | `eng` | Tesseract language code(s), combine with `+` |
| `--tesseract-path` | `/usr/bin/tesseract` | Path to Tesseract executable |

---

## 🚀 Batch Processing Output Example

```
======================================================================
BATCH PROCESSING MODE
======================================================================
Found 5 PDF file(s) in directory: /home/user/documents
Processing mode: ALL PAGES (automatic for batch mode)
======================================================================

######################################################################
Processing PDF 1/5: annual_report_2023.pdf
######################################################################
[Processing details...]
✓ SUCCESS: annual_report_2023.pdf completed successfully

######################################################################
Processing PDF 2/5: quarterly_review.pdf
######################################################################
[Processing details...]
✗ FAILURE: quarterly_review.pdf encountered an error
Error: PyPdfError: Invalid PDF structure
Error details logged to: /home/user/documents/error_log.txt

[... continues for all PDFs ...]

======================================================================
BATCH PROCESSING COMPLETE
======================================================================
Total time: 1234.56 seconds (20.58 minutes)
Total PDFs processed: 5
Successful: 4
Failed: 1

✓ Successfully processed files:
  - annual_report_2023.pdf
  - quarterly_review.pdf
  - financial_summary.pdf
  - board_minutes.pdf

✗ Failed files:
  - corrupted_document.pdf
    Error: PyPdfError: EOF marker not found

Detailed error logs available in: /home/user/documents/error_log.txt
======================================================================
```

---

## 🔧 Technical Implementation Details

### Changes Made:

1. **New Functions:**
   - `process_directory()` - Main batch processing orchestrator
   - `process_single_pdf()` - Wrapper for single PDF with error handling
   - `log_error_to_file()` - Error logging utility

2. **Modified Functions:**
   - `setup_and_run()` - Now detects directory vs. file and routes accordingly
   - Added `batch_mode` flag to `GLOBAL_CONFIG`

3. **Error Handling:**
   - Each PDF is processed in a try-except block
   - Errors are captured and logged without stopping the batch
   - Detailed error messages include exception type and description

4. **No Breaking Changes:**
   - Original single-file functionality remains unchanged
   - All existing command-line options work as before
   - Interactive mode still available for single PDFs

---

## 💡 Use Cases

Perfect for:
- **Bulk document digitization** - Process entire folders of scanned PDFs
- **Archive processing** - Convert legacy document collections
- **Research projects** - Extract text from multiple research papers
- **Legal document review** - Process case files in batch
- **OSINT investigations** - Extract text from multiple source documents

---

## ⚠️ Important Notes

1. **Sequential Processing**: PDFs are processed one at a time (not in parallel) to avoid resource exhaustion
2. **Resume Capability**: Not available in batch mode - each PDF starts fresh
3. **Page Selection**: Batch mode always processes ALL pages (no range selection)
4. **Error Logs**: Located in the **source directory** (where the PDFs are), not the output directory

---

## 🐛 Troubleshooting

**Q: What happens if one PDF is corrupted?**
A: The script logs the error and continues with the next PDF. Check `error_log.txt` for details.

**Q: Can I resume a failed batch?**
A: Simply re-run the same command. Already processed PDFs will be skipped (if output exists).

**Q: Where do error logs go?**
A: In the same directory as the source PDFs, in a file called `error_log.txt`.

**Q: Can I process subdirectories?**
A: Not currently - only PDFs in the specified directory (non-recursive).

---

## 📝 Example Workflow

```bash
# Step 1: Organize your PDFs
mkdir my_documents
cp *.pdf my_documents/

# Step 2: Run batch processing
python pdf_extractor.py my_documents/ --dpi 300 --output-dir ./extracted

# Step 3: Review results
ls extracted/
# Shows: doc1_processed/, doc2_processed/, etc.

# Step 4: Check for errors (if any)
cat my_documents/error_log.txt
```

---

## 🎉 Benefits

✅ **Time-saving**: Process dozens or hundreds of PDFs without manual intervention  
✅ **Robust**: Errors don't stop the entire batch  
✅ **Transparent**: Detailed logging of all operations  
✅ **Flexible**: Works with your existing workflow  
✅ **Reliable**: Maintains all original quality settings per PDF  

---

Enjoy your enhanced PDF extractor! 🚀
