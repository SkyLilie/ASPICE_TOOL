PRELIMINARY PROJECT STILL NEEDS A LOT OF WORK

# Agentic AI - ASPICE Compliance Checker

This Python script is designed to automate the process of checking project for compliance with the Automotive SPICE (ASPICE) standard. 
It leverages the capabilities of Google's Gemini Pro AI model to perform a the audits.

The script reads the official ASPICE standard, user's project documents, and generates a structured report that identifies compliance levels, highlights gaps, and provides actionable suggestions for improvement.


## WORKING:-

**Initialization**: The script starts by initializing the Google Gemini AI client using a secure API key.
Document Loading: It prompts the user for the location of two key sets of documents:
  The official ASPICE standards document (in PDF format).
  A folder containing the user's project documents (e.g., system requirements, architecture designs, test plans) in PDF format.

**User Input**: We need to specify the Process Area and Capability Level they want to assess.

**Prompt Engineering**: A highly detailed and structured prompt is constructed. This prompt instructs the AI to act as an ASPICE expert and provides it with:

*   The full text of the relevant ASPICE standard.
*  The content of all user-provided documents.
*  The specific process and level to assess.
*  A strict set of instructions on how to analyze the documents and what format the output must follow (a JSON object containing a Markdown report).

**AI Analysis**: The complete prompt is sent to the Gemini 2.5 Pro model. The model analyzes the user documents against the standard's requirements for the specified Base Practices (BPs) and Generic Practices (GPs).

**Response Parsing & Reporting**: The script receives the AI's response, which is expected in a JSON format. It extracts the Markdown report from the JSON structure.

**Display and Save**: The final, formatted compliance report is printed to the console and saved as a .md file for reference.

## Libraries Used:
* **os**: A standard Python library used for interacting with the operating system. Here, it's used to check if files (os.path.exists) and directories (os.path.isdir) exist before trying to access them.

* **PyPDF2**: A pure-python PDF library capable of splitting, merging, cropping, and transforming the pages of PDF files. In this script, it is used exclusively to extract plain text from the pages of both the standards document and the user's project documents.

* **pathlib**: A modern, object-oriented library for handling filesystem paths. It is used here to easily and robustly scan a directory for all files (Path(dir_path).glob('*')).

* **google.genai**: The official Google Python SDK for the Gemini API. This library handles all the complexity of authenticating and communicating with the Google AI models. It's used to configure the model (genai.Client), set generation parameters (types.GenerateContentConfig), and send the final prompt for analysis.

* **textwrap**: A standard Python library for formatting text. It is used here to clean up the multi-line prompt string (textwrap.dedent), removing any leading whitespace from each line to ensure the prompt sent to the AI is clean and well-structured.

* **json**: A standard Python library for working with JSON data. The script instructs the AI to return its response in a specific JSON format. This library is used to parse that JSON response (json.loads) and extract the report content.

* **KEY.py**: This is a local file you create to securely store your API_KEY. Importing it keeps your secret key out of the main script.

## Setup & Prerequisites:
1. Python 3
2. Libraries Used
   -   os
   -   PyPDF2
   -   from pathlib import Path
   -   import google.genai as genai
   -   from google.genai import types
   -   textwrap
   -   json
3. Google GeminiAI API Key 4Create a new file in the same directory as the script and name it KEY.py, withing store your API key like this:

        API_KEY = "YOUR_GOOGLE_AI_API_KEY"
  (or you can use whatever method you find suitable to use your api keys)

## How to Run:
  Place your project's PDF documents into a single folder. Use clear naming convention.
  Have the path to your ASPICE standards PDF ready.
  - Run the script from your terminal:

    `python ASPICE_AUDITOR_v0.1.py`

  
- Enter the path to ASPICE standards, for efficiency use pdf with only the pages relevant to your domain
- The path to the folder containing your project documents.
- The Process Area you want to check.
- The Capability Level you want to check. 
- The final report will be displayed in the terminal and saved to a .md file.

## Code Breakdown:
1. `class DocumentTools`

    This class acts as a dedicated file handler.

    - load_standards_document(): Loads a single PDF file (the ASPICE standard), performs validation (checks if it exists, is a valid PDF, and contains text), and returns its text content. 

    - load_user_documents(): Scans a given directory, finds all PDF files, extracts the text from each one, and returns the content in a dictionary where keys are filenames and values are the text content.


2. `_construct_prompt()`

    This function is the "prompt engineer." It takes the text from all documents and the user's choices (domain, level) and assembles them into a large, detailed set of instructions for the AI. This is the most critical part for ensuring a high-quality, relevant response.

3. `analyze_compliance()`

    This function manages the interaction with the Gemini API. It sends the constructed prompt, waits for the AI to process it, and handles the response. It includes error handling to decode the expected JSON output and to catch API-related issues.

4. `main()`

    This is the main funciton. It calls the other functions in the correct order, and handles the final output display and file saving. It also handles the errors that can arise during the program.
