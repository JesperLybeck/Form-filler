import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from collections import Counter
import re
from collections import Counter
load_dotenv()


PROMPT_TEMPLATE = """
Given the following website content, extract as much as possible of the following company information as JSON:
{fields}
---
{chunk}
---
Return only a single valid JSON object. Use double quotes for all keys and string values. Do not use single quotes. Do not include any text, markdown, or explanation before or after the JSON, if no value for a field is found. write null as value.
"""


# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

class FieldExtractor:
    def __init__(self, field_names: list[str], field_descriptions: dict, data_chunks: list[str] = None):
        self.data_chunks = data_chunks or []
        self.field_names = field_names
        self.field_descriptions = field_descriptions or {}
        self.responses = []

    @staticmethod
    def clean_response(response_text):
        """
        Cleans a Gemini/LLM response by removing markdown code block markers
        and parsing the JSON if possible. Returns a Python object or the cleaned string.
        Tries to fix common LLM output issues (e.g., single quotes, trailing commas, None/null).
        """
        
        content = response_text.strip()
        # Remove markdown code block markers
        if content.startswith("```json"):
            content = content[len("```json"):].strip()
        if content.startswith("```"):
            content = content[3:].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
        # Try to parse as JSON
        try:
            return json.loads(content)
        except Exception:
            pass
        # Try to fix common issues: single quotes, None/null, trailing commas
        fixed = content
        # Replace None with null
        fixed = re.sub(r"\bNone\b", "null", fixed)
        # Replace single quotes with double quotes (only for keys/values)
        fixed = re.sub(r"'([^\"']*?)'", r'"\1"', fixed)
        # Remove trailing commas before closing brackets/braces
        fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
        # Try to parse again
        try:
            return json.loads(fixed)
        except Exception:
            print("[clean_response] Could not parse as JSON. Raw response:", content)
            return content  # fallback if not valid JSON
        
    def extract_company_info(self, max_chunks=8):
        fields = "\n".join([f"{name}: {desc}" for name, desc in self.field_descriptions.items()]) if self.field_descriptions else "\n".join(self.field_names)
        results = []
        for i,chunk in enumerate(self.data_chunks[:max_chunks]):
            prompt = PROMPT_TEMPLATE.format(chunk=chunk, fields=fields)
            response = model.generate_content(prompt)
            print("Response on chunk:"+str(i)+":", response.text,'\n\n\n')  # Debugging output
            cleaned = self.clean_response(response.text)  # note self.clean_response
            
            if isinstance(cleaned, dict):
                results.append(cleaned)
            else:
                print("Warning: Could not parse JSON, got string response:", cleaned)
                results.append({})  # or handle differently

        return results


  

    @staticmethod
    def aggregate_results(suggestions):
        for sugg in suggestions:
           print("Suggestion:", sugg)
      
        
    
        if not suggestions:
            return {}

        merged = {}
        # Collect all keys present in any suggestion
        keys = set().union(*[d.keys() for d in suggestions])

        for key in keys:
            # Collect all valid (non-null, non-empty) values for the key
            values = [d.get(key) for d in suggestions if d.get(key) not in [None, '', []]]
            
            if not values:
                merged[key] = None
                continue
            
            # Handle different data types
            if isinstance(values[0], dict):
                # For dictionaries (like socialMedia), merge them
                merged_dict = {}
                for value in values:
                    if isinstance(value, dict):
                        merged_dict.update(value)
                merged[key] = merged_dict if merged_dict else None
            elif isinstance(values[0], list):
                # For lists, combine and deduplicate
                merged_list = []
                for value in values:
                    if isinstance(value, list):
                        merged_list.extend(value)
                merged[key] = list(set(merged_list)) if merged_list else None
            else:
                # For simple types, use Counter to find most common
                try:
                    counts = Counter(values)
                    most_common_value, _ = counts.most_common(1)[0]
                    merged[key] = most_common_value
                except TypeError:
                    # Fallback: just take the first non-null value
                    merged[key] = values[0] if values else None

        return merged


    @staticmethod
    def pretty_print_extracted_data(data):
        print("\n=== EXTRACTED BUSINESS DATA ===")
        
        # Handle both single dict and list of dicts
        if isinstance(data, dict):
            # Single dictionary - print key-value pairs
            for key, value in data.items():
                if value is not None and value != "":
                    print(f"📋 {key}: {value}")
                else:
                    print(f"📋 {key}: (not found)")
        elif isinstance(data, list):
            # List of dictionaries
            for i, item in enumerate(data, 1):
                print(f"\n--- Result {i} ---")
                if isinstance(item, dict):
                    for key, value in item.items():
                        if value is not None and value != "":
                            print(f"📋 {key}: {value}")
                        else:
                            print(f"📋 {key}: (not found)")
                else:
                    print(json.dumps(item, indent=2, ensure_ascii=False))
        else:
            print("Unexpected data format:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        
        print("=" * 40)

