import os
import PyPDF2
from pathlib import Path
import google.genai as genai
from google.genai import types
import textwrap
import json


from KEY import API_KEY

client = genai.Client(api_key=API_KEY)
model_name = "gemini-2.5-pro"
gen_config=types.GenerateContentConfig(
            max_output_tokens=20000,
            top_k=2,
            top_p=0.5,
            temperature=0.5,
            response_mime_type='application/json'
        )


# Tooling Class (Handles File Operations)
class DocumentTools:
    """A class to handle document loading and validation."""

    def load_standards_document(self, filepath: str) -> str:
        """
        Loads the standards PDF, validates it, and extracts text.

        Args:
            filepath: The path to the ASPICE standards PDF.

        Returns:
            The extracted text content of the PDF.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a readable PDF.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Error: The standards file was not found at '{filepath}'")

        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if not reader.pages:
                    raise ValueError("Error: The PDF is empty or corrupted.")

                text_content = ""
                for page in reader.pages:
                    text_content += page.extract_text() or ""

            if not text_content.strip():
                raise ValueError("Error: Could not extract any text from the PDF. It might be an image-based PDF.")

            print(f"✅ Successfully loaded and read standards document: {os.path.basename(filepath)}")
            return text_content
#        except PyPDF2.errors.PdfReadError:
#            raise ValueError(f"Error: '{filepath}' is not a valid or readable PDF file.")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while reading the standards PDF: {e}")

    def load_user_documents(self, dir_path: str) -> dict[str, str]:
        """
        Loads multiple user documents (PDF, TXT) from a specified directory.

        Args:
            dir_path: Path to the directory containing user documents.

        Returns:
            A dictionary where keys are filenames and values are their text content.
        """
        if not os.path.isdir(dir_path):
            print(f"⚠️ Warning: Directory '{dir_path}' not found. No user documents will be loaded.")
            return {}

        user_docs = {}
        print(f"\nScanning for user documents in: {dir_path}")
        for filepath in Path(dir_path).glob('*'):
            if filepath.is_file() and filepath.suffix.lower() in ['.pdf']:
                try:
                    content = ""
                    if filepath.suffix.lower() == '.pdf':
                        with open(filepath, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                content += page.extract_text() or ""

                    if content.strip():
                        user_docs[filepath.name] = content
                        print(f"  - Loaded user document: {filepath.name}")
                    else:
                        print(f"  - ⚠️ Skipped empty or unreadable document: {filepath.name}")

                except Exception as e:
                    print(f"  - ❌ Error loading {filepath.name}: {e}")

        if not user_docs:
            print("⚠️ Warning: No user documents were successfully loaded. The analysis may be inaccurate.")

        return user_docs

def _construct_prompt(standards_text: str, user_docs: dict[str, str], domain: str, level: str) -> str:
        #Constructs the detailed prompt for the AI model.

        user_docs_formatted = "\n\n---\n\n".join([f"DOCUMENT NAME: {name}\n\nCONTENT:\n{content}" for name, content in user_docs.items()])

        prompt = f"""
        ROLE AND GOAL:
        You are an expert Compliance Auditor specializing in the Automotive SPICE (ASPICE) VDA QMC standard. Your task is to perform a detailed compliance check of the user's documents against the standard for a specific process and capability level.

        CONTEXT:
        - Standard: {standards_text}
        - Process to Assess: {domain}
        - Target Capability Level: {level}

        INPUTS:
        1. ASPICE Standard Document: The full text of the ASPICE VDA QMC standard is provided for your reference.
        2. User Documents: A set of documents provided by the user that allegedly describe their processes and work products.

        YOUR TASK:
        1.  Identify Practices: From the provided ASPICE standard text, identify all the Base Practices (BPs) associated with the process '{domain}'. Analyse what documents and what content needs to be checked for completion for that BP
        2.  Identify Generic Practices (GPs): From the standard, identify all the Generic Practices (GPs) required to achieve Capability Level {level}.Analyse what documents and what content needs to be checked for completion for that GP
        3.  For BPs and GPs which you CANNOT check for that are too technical for you to handle or do not have access too like communication artifacts, identify those BPs and GPs and list them at the start of your output along with the reason why you cannot check them. Do not check compliance for those BP/GP and in your final report put a dash in field of score for that BP/GP.
        4.  Analyze and Score: For all Base Practice and Generic Practice applicable:
            a. Meticulously search ALL provided user documents for evidence that the practice is being performed.
            b. Provide a Score: Provide a score according to the rating method provided in the standards document. For ASPICE it is N, L, P, F for Not achieved, Partially achieved, Largely achieved and Fully achieved
            c. Provide Detailed Reasoning: This is the most critical part. Your reasoning MUST be specific.
               - If evidence is found, QUOTE the relevant text directly from the user document(s) and state the document name. Explain HOW this quote satisfies the practice.
               - If evidence is missing or partial, clearly state WHAT is missing and find suggestions for filling the gaps. 
        5.  Gap Analysis: For any practice scoring below 100%, describe the specific gap between the standard's requirement and the user's documentation.
        6.  Provide Suggestions: For each identified gap, give clear, actionable suggestions on what the user needs to create, document, or change to achieve full compliance.

        OUTPUT FORMAT:
        The JSON object must contain a single top-level key named Report, and its value should be a string containing your analysis
        Present your findings in a clear, structured Markdown report. Use the exact following format:

        Report
            Process Assessed: {domain}
            Target Capability Level: {level}

            Base Practices (BPs) for {domain}
                BP.X: [Base Practice Title]
                - Score: [N,L,P,F]
                - Reasoning: [Your detailed explanation, including quotes and document references]
                - Gap Analysis: [Description of all the gaps along with artifact IDs, if any]
                - Suggestions: [Actionable advice to close all the gaps]

            Generic Practices (GPs) for Level {level}
                GP X.Y.Z: [Generic Practice Title]
                - Score: [N,L,P,F]
                - Reasoning: [Your detailed explanation, including quotes and document references]
                - Gap Analysis: [Description of all the gaps along with artifact IDs, if any]
                - Suggestions: [Actionable advice to close the gap]

            Final Summary & Recommendations
            [Provide a tabular data for BP/GP and the achieved score and IDs for all the artifacts in user document which were found incomplete ]

        PROVIDED STANDARDS TEXT FOR YOUR ANALYSIS:
        {standards_text[:50000]}... 

        PROVIDED USER DOCUMENTS FOR YOUR ANALYSIS:
        {user_docs_formatted}
        """
        return textwrap.dedent(prompt)

def analyze_compliance(standards_text: str, user_docs: dict[str, str], domain: str, level: str) -> str:
    #Sends the request to the Gemini model and returns the analysis.
        if not user_docs:
            return "Analysis cannot proceed: No user documents were provided or loaded."

        prompt = _construct_prompt(standards_text, user_docs, domain, level)

        print("\n Requesting AI for analysis... This may take a few moments.")
        try:
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config=gen_config
            )
            print("AI analysis complete")

            if not response.candidates:
                return "Error: The model did not return any content"

        # Try decoding raw JSON from the AI output if it fails print the raw output
            try:
                raw_json_string = response.candidates[0].content.parts[0].text
                data = json.loads(raw_json_string)      #convert to dictionary
                report_content = data.get("Report", "ERROR: Report Key not found")
                if report_content == "ERROR: Report Key not found":         #if the key is not found, print the raw data
                    print(f"\n Printing raw response: {raw_json_string}")
                return report_content               #This variable contains the report of everything runs smoothly

            except json.JSONDecodeError:
                return f"Error: Failed to decode the JSON response from the AI. The model may have returned malformed text. Raw response: {response.candidates[0].content.parts[0].text}"

        except Exception as e:
            return f"An error occurred during AI analysis: {e}"


def main():
    print("=" * 90)
    print("                 Agentic AI - ASPICE Compliance Checker                ")
    print("=" * 90)

    # --- Initialize Tools and AI ---
    try:
        tools = DocumentTools()
        if not API_KEY:
            raise ValueError("Please get your key from Google AI Studio.")

    except (ValueError, RuntimeError) as e:
        print(f"\n❌ CRITICAL ERROR during initialization: {e}")
        return

# Main program flow: Get documents, get domain and area to be checked for, call method to send data to AI for complaince, Save output in a file.
    try:
    #Get standards document path
        standards_path = input("\nEnter the full path to the ASPICE standards PDF: ").strip()
        standards_content = tools.load_standards_document(standards_path)

    #Get user documents path
        user_docs_dir = input("Enter the path to the folder containing your project documents: ").strip()
        user_docs_content = tools.load_user_documents(user_docs_dir)

    #Get domain and level and call function to analyse the documents
        domain = input("Which Process Area/Domain do you want to check? (eg: SYS.1, SYS.2): ").strip()
        level = input("What Capability Level do you want to check against? (e.g., 1, 2): ").strip()

        final_report = analyze_compliance(
            standards_text=standards_content,
            user_docs=user_docs_content,
            domain=domain,
            level=level
        )

    #Display Output
        print("\n\n" + "=" * 45 + " FINAL REPORT " + "=" * 45 + "\n")
        print(final_report)
        print("\n" + "=" * 90)

    # Save the report to a file named like ASPICE_Report_SYS.2_Level2
        report_filename = f"ASPICE_Report_{domain.replace(' ', '_')}_Level{level}.md"
        with open(report_filename, "w", encoding='utf-8') as f:             # w:write
            f.write(final_report)
        print(f"\n📄 Report saved to: {report_filename}")

    #When we run into error
    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ An error occurred: {e}")
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
    except Exception as e:
        print(f"\n❌ An unexpected and critical error occurred: {e}")


if __name__ == "__main__":
    main()
