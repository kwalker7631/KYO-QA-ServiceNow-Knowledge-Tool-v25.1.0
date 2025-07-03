# KYO QA ServiceNow Knowledge Tool v26.0.0 - Usage Instructions

## Basic Usage

1. **Launch the application** using `START.bat` (Windows) or run `python run.py`
2. **Select an Excel file** with a "Meta" column to update
3. **Choose PDF files** by either:
   - Selecting a folder containing PDFs
   - Selecting individual PDF files
4. **Click "START"** to begin processing
5. **Monitor progress** with the status indicators, progress bar, and logs
6. *(Optional)* **Enable error reporting** by following the instructions in the [Error Reporting](#error-reporting) section.

## PDF Processing & OCR

The application will:
1. Extract embedded text from PDFs when available
2. Automatically detect image-based PDFs and apply OCR
3. Identify model numbers using pattern matching
4. Update the Excel file with extracted information

### OCR Handling

- The application detects when OCR is needed for image-based PDFs
- OCR is applied using Tesseract with image preprocessing for better results
- OCR-processed files are marked with an "(OCR)" indicator
- For best results, ensure Tesseract OCR is installed or available in the `tesseract` folder

## Pattern Management

1. Click the **"Patterns"** button to open the pattern manager
2. Choose between **"Model Patterns"** or **"QA Patterns"**
3. To add a new pattern:
   - Select text in a document and click **"Suggest from Highlight"**
   - Edit the pattern if needed in the **"Test/Edit Pattern"** box
   - Click **"Add as New"** to add it to the list
4. To test a pattern:
   - Enter or select a pattern from the list
   - Click **"Test Pattern"** to see matches highlighted in the text
5. Click **"Save All Patterns"** to save your changes to `custom_patterns.py`

## Reviewing Files That Need Attention

When the tool cannot find model numbers in a PDF:
1. The file will be marked as **"Needs Review"**
2. It will appear in the **"Files to Review"** list in the main window
3. Select a file from the list and click **"Review Selected"**
4. The text content will be displayed in the pattern management window
5. Create new patterns based on the model numbers found in the text
6. After saving new patterns, use the **"Re-run Flagged"** button to process the files again

## Understanding the Results

The Excel file will be updated with:
- Model numbers found in the "Meta" column
- Author information in the "Author" column
- Status indicators showing which files were processed successfully

Cells are color-coded:
- **Green**: Successfully processed with models found
- **Yellow**: Needs review (no models found)
- **Red**: Failed to process
- **Blue**: Required OCR processing

## Error Reporting

You can forward crashes to Sentry by setting the `SENTRY_DSN` environment variable before launching:

```cmd
set SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
```

## Troubleshooting

### Common Issues

1. **"Excel file is locked" error**
   - Close the Excel file before processing
   - Make sure no other applications have the file open

2. **No models found in PDFs**
   - Use the Pattern Manager to add custom patterns
   - Review the text extracted from the PDF
   - Make sure the PDFs contain readable text or images of text

3. **OCR not working**
   - Ensure Tesseract is installed or available in the `tesseract` folder
   - Check that the image quality is sufficient for OCR

4. **Application crashes**
   - Check the logs in the `logs` folder for error details
   - Make sure all dependencies are installed properly

### Getting Help

If you encounter issues:
1. Check the log files in the `logs` folder
2. Look for text files in the `PDF_TXT/needs_review` folder
3. Contact support with the specific error message and log files
