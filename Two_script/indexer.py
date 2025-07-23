import os
import json
import sys
import textwrap
import pdfplumber
import google.genai as genai
from google.genai import types
from KEY import GEMINI_PRO_API_KEY

API_KEY = GEMINI_PRO_API_KEY


if not API_KEY:
    sys.exit("❌❌ CRITICAL PROBLEMO: API key not found. Please set it in the script ❌❌")

client = genai.Client(api_key=API_KEY)
model_name = "gemini-2.5-pro"
gen_config=types.GenerateContentConfig(
            max_output_tokens=65536,
            top_k=2,
            top_p=0.85,
            temperature=0.65,
            response_mime_type='application/json'
        )

def load_standards_document( filepath: str) -> str:
        #Loads the document in the user provided path
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The path {filepath} you  provided does not exist ")

        try:
            full_content = ""
            #Just reading all the contents
            with pdfplumber.open(filepath) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_content += f"\n\n--- Page {i + 1} Text ---\n"
                        full_content += page_text

                    if not full_content.strip():
                        raise ValueError("Error: Could not extract any text from the PDF. It might be an image-based PDF.")

            print(f"✅ Successfully loaded and read standards document: {os.path.basename(filepath)}")
            return full_content
        except Exception as e:
            raise ValueError(f"An unexpected error occurred while reading the standards PDF: {e}")

def indexer_prompt(standards_text: str) -> str:

    return textwrap.dedent(f"""
    ROLE AND GOAL:
    You are an expert Technical Auditor. Your task is to read the provided Automotive SPICE standard text and convert it into a structured JSON object detailing how you would give ratings for each BP and GP as given in the {standards_text} standards document.

    INSTRUCTIONS:
    1.  Read and understand the {standards_text} PDF.
    2.  For EACH process DOMAIN (like SYS.1, SYS.2, SYS.3, etc.), identify EVERY Base practice (BPs).
    3.  For EACH capability level (1 through 5), identify EVERY Generic Practices (GPs).
    4.  For EACH BP and GP, extract its ID , its title and the direct statement of the practice itself.
    5.  For EACH BP and GP, understand the Key objective, user documents needed to be checked for ensuring compliance.
    6.  For EACH BP and GP, understand HOW ratings [N, P, L, F] are given.
    
    OUTPUT FORMAT STRUCTURE:
    You MUST output a single, valid JSON object. The structure should be as follows: The root of the JSON is an object with a top-level key, which is the name of process area example "SYS.1", "SYS.2", "SYS.3" etc also "CapabilityLevel"
            "Name of DOMAIN": It is a list of Dictionaries with each element has following keys
                    - "BP_ID"
                    - "BP_title"
                    - "BP_statement"
                    - "BP_key_obj"
                    - "BP_user_docs_needed"
                    - "BP_rating_rules" : value of this dictionary are other dictionaries named
                        "F", "L", "P" and "N". The value for each of these rating keys is a list of string outlining how that rating is given.
            
            "CapabilityLevel": It is a dictionary of dictionaries with following keys
                    - "LEVEL to be assessed(1 to 5)"
                    The value for each LEVEL key is an dictionary containing:
                        - "PA_name"
                        - "PA_ID"
                        - "GenericPractices" : It is a list of Dictionaries with each element has following keys
                                - "GP_ID"
                                - "GP_title"
                                - "GP_statement"
                                - "GP_key_obj"
                                - "GP_user_docs_needed"
                                - "GP_rating_rules" : value of this dictionary are other dictionaries named
                                    "F", "L", "P" and "N". The value for each of these rating keys is a list of strings outlining how that rating is given.
    
    Example for output:
    {{
        "SYS.2": [
            {{
                "BP_ID": "BP.1",
                "BP_title": "Specify system requirements",
                "BP_statement": "Use the stakeholder requirements to identify and document the functional and non-functional requirements for the system according to defined characteristics for requirements",
                "BP_key_obj": "Coverage, Elaboration, Quality- Unambiguous, Verifiable, Consistent, Feasible, Complete",
                "BP_user_docs_needed": "Stakeholder Requirements Specification, System Requirements Specification, Requirements Management Plan (RMP), Review Records",
                "BP_rating_rules":
                    {{
                        "F": [
                            "All relevant stakeholder requirements from the StRS are clearly covered by one or more system requirements",
                            "Each system requirement is unambiguous verifiable consistent and feasible",
                            "The verification criteria for each requirement are specific and measurable. also the verification criteria for that requirement is consistent with the practice",
                            "All requirements are explicitly and correctly classified (e.g., as Functional, Non-Functional, Safety) according to the definitions defined in the RMP",
                            "Review records show that a formal quality check was performed and that any issues found were resolved"
                        ],
                        "L": [
                            "The vast majority of stakeholder requirements are covered",
                            "Most system requirements are of high quality but there may be minor issues in a small number of them (e.g. a few requirements could be worded more clearly or some verification criteria are slightly vague but still workable)",
                            "Most contradictions or issues were identified and resolved during reviews",
                            "The overall document is a reliable basis for system design"
                        ],
                        "P": [
                            "There are significant gaps in coverage; numerous stakeholder requirements are not addressed",
                            "A significant number of system requirements are ambiguous (using words like \"fast\" \"easy\") non-verifiable (e.g. verification criteria are missing or just say \"To be tested\") or inconsistent with the requirement in question",
                            "The classification of requirements is often missing or incorrect",
                            "The document is not considered a stable or reliable basis for design work. It would require significant rework"
                        ],
                        "N": [
                            "No System Requirements Specification (SyRS) or RMP document exists",
                            "The SyRS is just a copy-paste of the Stakeholder Requirements without any engineering analysis or refinement",
                            "SyRS is so poor it adds no value to the project"
                        ]
                    }}
    
            }} 
        ],
    }}
        
    "CapabilityLevel": {{
            "2": {{
                "PA_name": "Performance Management",
                "PA_ID": "2.2",
                "GenericPractices": 
                    [
                        {{
                        "GP_ID": "GP.2.2.3",
                        "GP_title": "Identify store and control the work products",
                        "GP_statement": "The work products to be controlled are identified. The work products are stored and controlled in accordance with the requirements. Change control is established for work products. Versioning and baselining of the work products is performed in accordance with the requirements for storage and control of the work products. The work products including the revision status are made available through appropriate mechanisms",
                        "GP_key_obj": "Prevent Chaos, Establish a Single Source of Truth, Provide Stability, Enable Traceability and Audits",
                        "GP_user_docs_needed": "Project Management Plan (PMP) or equivalent , The Monitoring Evidence",
                        "GP_rating_rules": 
                                    {{
                                    "F": [
                                        "All work products of the process are identified and stored in configuration management",
                                        "Each work product has a clear version history",
                                        "Baselines are formally established, timed with project milestones and are clearly identifiable",
                                        "There is a clear record of what constitutes each baseline",
                                        "The change control process for baselined items is defined and followed (linking to GP 2.2.4)",
                                        "The system is 100% reliable; what's in the document matches what's in the Configuration management system."
                                        ],
                                    "L": [
                                        "Actual data is being collected systematically and regularly for process performance",
                                        "Regular comparison of actuals vs. plan is evident (e.g. in weekly status reports or dashboards)",
                                        "The monitoring covers not just the schedule but also effort/cost and quality aspects",
                                        "Relevant stakeholders are demonstrably informed about the project's status based on this data"
                                        ],
                                    "P": [
                                            "A project plan with objectives might exist, but there's little evidence it is being used to track progress",
                                            "Monitoring is ad-hoc (e.g., the project manager asks for status updates informally in the hallway but doesn't record the data)",
                                            "Only one aspect is tracked (e.g., only schedule), while others (effort, quality) are ignored",
                                            "The process generally works and provides a stable basis for other teams."
                                        ],
                                    "N": [
                                            "No Configuration Management Plan exists.",
                                            "Work products are stored on local machines or shared via email.",
                                            "There is no version history",
                                            "The concept of a \"baseline\" is not used",
                                            "It is impossible reactive or based on \"gut feeling\""
                                        ]
                                    }}
                        }}
                    ]
                }}
            }}

    }}
    """)

def generate_knowledge_base(prompt) -> dict:

    print("Generating knowledge base...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type='application/json')
    )
    print("AI analysis complete. Parsing JSON...")

    try:
        response_json = json.loads(response.candidates[0].content.parts[0].text)
        print("Successfully parsed JSON...")
        return response_json
    except:
        print(f"ERROR: Failed to parse JSON...Printing raw response\n\n{response}")
        sys.exit("Generate_knowledge_base failed")



def main():

    standards_path = input("Enter the full path to the ASPICE standards PDF to be indexed: ").strip()
    standards_content = load_standards_document(standards_path)
    prompt = indexer_prompt(standards_content)
    knowledge_base = generate_knowledge_base(prompt)

    output_filename = "aspice_knowledge_base.json"
    with open(output_filename, "w", encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=4)

    print(f" Successfully created and saved knowledge base to: {output_filename}")
    sys.exit(0)


if __name__ == "__main__":
    main()
