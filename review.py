# py -m pip install google-generativeai
from pathlib import Path
import google.generativeai as genai
import csv
import re

# Global flag to control live API calls. Make sure to create an api_key.txt file in the root directory with your API key.
CONNECT_GEMINI_LIVE = True

def ask_llm(input_text: str) -> str:
    """
    Sends a prompt to the Gemini model and returns the response.
    """
    # Note: Use 'gemini-2.5-flash'.
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(input_text)
    return response.text

def load_profanity_terms(csv_path: Path) -> list[str]:
    terms: list[str] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                terms.append(row[0])
    return terms

def parse_words_to_remove(responses: list[str]) -> set[str]:
    """
    Parses Gemini responses to extract words identified as non-extreme.
    """
    words_to_remove = set()
    # Regex to find all content between @@@@ markers.
    # It will produce a flat list like ['WORD1', 'EXPLANATION1', 'WORD2', 'EXPLANATION2', ...]
    pattern = r"@@@@\s*(.*?)\s*@@@@"

    for text in responses:
        if "No non-extreme words found." in text:
            continue
        
        found = re.findall(pattern, text)
        # The words are the 0th, 2nd, 4th, etc. elements in the list.
        words = found[0::2]
        for word in words:
            words_to_remove.add(word.lower())
            
    return words_to_remove

def main() -> None:
    """
    Main function to configure API, load profanity words, log queries, and filter the list.
    """
    if CONNECT_GEMINI_LIVE:
        print("CONNECT_GEMINI_LIVE is True. Attempting to connect to the live API.")
        # API key configuration is required for live connection
        try:
            api_key_path = Path(__file__).resolve().parent / "api_key.txt"
            api_key = api_key_path.read_text().strip()
            if not api_key or api_key == "YOUR_API_KEY_HERE":
                raise ValueError("API key is missing or is a placeholder.")
            genai.configure(api_key=api_key)
            print("Gemini API configured successfully.")
        except (FileNotFoundError, ValueError) as e:
            raise SystemExit(f"Error: API key setup failed. {e}")
    else:
        print("CONNECT_GEMINI_LIVE is False. Running in dummy mode.")

    base_dir = Path(__file__).resolve().parent
    source_path = base_dir / "vbw_classify.csv"
    log_path = base_dir / "vbw_llm_review_log.md"
    output_path = base_dir / "vbw.csv"

    # Clear the log file and add a main header
    log_path.write_text(
        f"# Profanity List Review Log\n\n_Mode: {'Live' if CONNECT_GEMINI_LIVE else 'Dummy'}_ \n\n",
        encoding="utf-8",
    )

    print(f"Loading terms from {source_path}...")
    terms = load_profanity_terms(source_path)
    print(f"Loaded {len(terms)} terms.")

    chunk_size = 100
    chunks = [terms[i : i + chunk_size] for i in range(0, len(terms), chunk_size)]
    print(f"Split into {len(chunks)} chunks. Processing...")

    base_prompt = (
        "Here is a list of profanity words for a profanity filter. "
        "I only want really extreme profanity on this list, not mild ones. "
        "For example, Willy is someone's name so it is fine. Anita is a name too. Vulgar terms like penis or cunt are not fine, but terms like doof or doofus are fine."
        "Can you look through this list and find any that are in the non-extreme category, "
        "if any, and translate them to english and explain? Keep the explanation short and concise."
        "If they are all extreme, then great, the list is empty and we're good.\n"
        "USE THIS FORMAT FOR YOUR RESPONSE: @@@@ WORD @@@@ EXPLANATION @@@@\n"
        "If you don't find any non-extreme words, just say 'No non-extreme words found.'\n"
        "If you find any non-extreme words, list them one by one, with the format above. No other text.\n"
        "Use one formatted response line per word.\n"
    )
    
    all_responses = []
    with log_path.open("a", encoding="utf-8") as log_file:
        for i, chunk in enumerate(chunks):
            print(f"Query Google Gemini for chunk {i+1} / {len(chunks)}")
            word_list_str = ", ".join(chunk)
            query = f"{base_prompt}\n\nHere is the list of words to review:\n[{word_list_str}]"

            response_text: str
            if CONNECT_GEMINI_LIVE:
                try:
                    response_text = ask_llm(query)
                except Exception as e:
                    response_text = f"ERROR CALLING GEMINI API: {e}"
                    print(f"  ERROR on chunk {i+1}: {e}")
            else:
                response_text = "@@@@ Doof @@@@ A mild, silly insult for a foolish person. @@@@" # Dummy response for testing

            all_responses.append(response_text)

            # Write to log file in Markdown format
            log_file.write(f"## Chunk {i+1}/{len(chunks)}\n\n")
            log_file.write("**Query:**\n")
            log_file.write(f"```\n{query}\n```\n\n")
            log_file.write("**Gemini Response:**\n")
            log_file.write(f"```markdown\n{response_text}\n```\n\n")
            log_file.write("---\n\n")

            # break # Uncomment this to stop after the first chunk for testing

    print(f"\nFinished querying. All chunks and responses have been written to {log_path.name}.")
    
    print("\nNow processing results...")
    words_to_remove = parse_words_to_remove(all_responses)
    print(f"Found {len(words_to_remove)} unique non-extreme words to remove.")
    if words_to_remove:
        print(f"Words to remove: {', '.join(sorted(list(words_to_remove)))}")

    # Filter the original list
    final_terms = [term for term in terms if term.lower() not in words_to_remove]
    
    print(f"Writing {len(final_terms)} extreme words to {output_path.name}...")
    with output_path.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.writer(outfile)
        for term in sorted(final_terms):
            writer.writerow([term])

    print("Finished.")


if __name__ == "__main__":
    main()
