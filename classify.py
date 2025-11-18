# pip install transformers torch
import os
from pathlib import Path
from typing import Iterable, Mapping, Any, Tuple

# CRITICAL: Set environment variables BEFORE importing transformers/huggingface_hub
# The libraries read these on import, so they must be set first.
LOCAL_CACHE_DIR = Path(__file__).resolve().parent / "hf_model_cache"
LOCAL_CACHE_DIR.mkdir(exist_ok=True)

# Set environment variables for Hugging Face cache locations
# HF_HOME is the main cache directory (TRANSFORMERS_CACHE is deprecated)
os.environ["HF_HOME"] = str(LOCAL_CACHE_DIR)
os.environ["HF_HUB_CACHE"] = str(LOCAL_CACHE_DIR)
os.environ["HF_DATASETS_CACHE"] = str(LOCAL_CACHE_DIR)

# Now import after environment variables are set
from colorama import Fore, Style, init as colorama_init
from transformers import pipeline

# Initialise color output (Windows-friendly).
colorama_init(autoreset=True)

# Minimum score required to consider something truly "not safe".
NOT_SAFE_THRESHOLD = 0.81

def load_profanity_terms(csv_path: Path) -> list[str]:
    terms: list[str] = []
    with csv_path.open("r", encoding="utf-8") as f:
        for line in f:
            term = line.strip()
            if term:
                terms.append(term)
    return terms


def _extract_scores(pred: Iterable[Mapping[str, Any]]) -> Tuple[float, float]:
    items = list(pred)
    scores = {p["label"]: float(p["score"]) for p in items if "label" in p and "score" in p}
    return scores.get("not safe", 0.0), scores.get("safe", 0.0)


def _decide_label(not_safe: float, safe: float) -> str:
    if not_safe >= NOT_SAFE_THRESHOLD and not_safe >= safe:
        return "not safe"
    return "safe"


def format_prediction(term: str, pred: Iterable[Mapping[str, Any]]) -> str:
    not_safe, safe = _extract_scores(pred)
    majority_label = _decide_label(not_safe, safe)

    color = Fore.RED if majority_label == "not safe" else Fore.GREEN

    return (
        f"{color}{term}{Style.RESET_ALL}"
        f"  [{majority_label}: not_safe={not_safe:.3f}, safe={safe:.3f}]"
    )


def main() -> None:

    # Initialise the classifier once.

    clf = pipeline(
        "text-classification",
        model="mangalathkedar/profanity-detector-distilbert-multilingual",
        # device_map is omitted because this model does not support `device_map="auto"`
        top_k=None,  # get full label distribution if provided
        truncation=True,
        # cache_dir is handled via environment variables set above
    )

    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir / "profanity_aggregate.csv"
    unsafe_csv_path = base_dir / "vbw.csv"
    log_path = base_dir / "vbw_classify_log.txt"

    terms = load_profanity_terms(csv_path)
    if not terms:
        print(f"No terms found in {csv_path}")
        return

    batch_size = 32

    # Open the unsafe output file and log file once.

    with unsafe_csv_path.open("w", encoding="utf-8", newline="") as unsafe_out, log_path.open("w", encoding="utf-8", newline="") as log_out:
        
        for i in range(0, len(terms), batch_size):
            batch = terms[i : i + batch_size]
            preds = clf(batch)
            for term, pred in zip(batch, preds):
                not_safe, safe = _extract_scores(pred)
                label = _decide_label(not_safe, safe)

                # Write only clearly unsafe terms to vbw.csv
                if label == "not safe":
                    unsafe_out.write(term + "\n")

                # Prepare pretty output line (colour for console, plain text for log).
                formatted = format_prediction(term, pred)
                print(formatted)
        
                # Strip ANSI color codes for the log by removing Fore/Style sequences.
                # Easiest portable approach: log the uncoloured text.
                log_line = f"{term}  [{label}: not_safe={not_safe:.3f}, safe={safe:.3f}]"
                log_out.write(log_line + "\n")


if __name__ == "__main__":
    main()