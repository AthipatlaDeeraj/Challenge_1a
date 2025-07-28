YOU CAN PROVIDE YOUR OWN INPUT AND CHECK WITH THE OUTPUT OUR MODEL WILL DO ITS PART 😉 BROH!

# Challenge 1a – PDF Outline Extractor

This project extracts a structured outlines from PDF documents using Python, with support for multilingual content and robust heading detection logic. It is built to work inside a Docker container for secure and consistent execution.

# Our Folder Structure

```
Challenge_1a/
├── sample_dataset/
│   ├── outputs/         # JSON output files (excluded from repo)
│   ├── pdfs/            # Input PDF files (excluded from repo)
│   └── schema/
│       └── output_schema.json
├── Dockerfile
├── requirements.txt
├── process_pdfs.py
└── README.md
```
<img width="361" height="338" alt="image" src="https://github.com/user-attachments/assets/696ffa62-92c6-4684-9ec5-516c5be14e31" />

## DEMO INPUT OUTPUT GENERATED CHECKOUT BROH

![WhatsApp Image 2025-07-28 at 23 02 27_d54da94e](https://github.com/user-attachments/assets/e67dd1e2-e9ef-45be-abbe-99c06d5a83aa)


## Input and Output Formats - As given please provide valid input

-Input PDF files placed inside the `/input` directory.
-Output Extracted outline in JSON format saved inside the `/output` directory.
- The output JSON includes:
  - `"title"`: Title of the document or filename.
  - `"outline"`: A list of headings, each with:
    - `"level"`: Heading level (H1–H6)
    - `"text"`: Heading text
    - `"page"`: Page number (0-indexed)

## Working procedure:

1. The script first tries to extract the document's Table of Contents (TOC) using `PyMuPDF`.
2. If the TOC is insufficient, it analyzes font sizes, formatting, and layout to detect headings.
3. The detection is enhanced using heuristics like boldness, text position, capitalization, and common heading words.
4. Language detection is used to ensure multilingual support.

## Requirements Like models we used

All required libraries are listed in `requirements.txt`, including:
- `PyMuPDF`
- `langdetect`

### Build the Docker Image then you are very simple to use

```bash
docker build -t pdf-processor .
```

### Run the Container using this cmd

Windows (PowerShell):
```powershell
docker run --rm `
  -v ${PWD}\input:/app/input:ro `
  -v ${PWD}\output:/app/output `
  --network none `
  pdf-processor
```

Linux/Mac:
```bash
docker run --rm   -v $(pwd)/input:/app/input:ro   -v $(pwd)/output:/app/output   --network none   pdf-processor
```

## Notes

->This script will process all `.pdf` files inside `/input` and generate matching `.json` outputs in `/output`.
-> It works fully offline and supports Japanese and other multilingual documents.
->Designed for Challenge 1a use case with schema conformance.
