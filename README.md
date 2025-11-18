# VBW: Very Bad Words

VBW: Very Bad Words is an AI‑curated multilingual profanity wordlist focused on actual strong profanity and highly abusive language. The wordlist can be used to filter content such as usernames, with less risk of being over‑aggressive.
Uses AI vibe coded processing scripts, but curated by a programmer.

> ⚠️ **Content warning:**  
> This repository contains files with strong profanity, because that is the point.

---
## Why VBW?

Most profanity lists on GitHub are far too over‑inclusive. Even mild terms like 小姐 or real people's names such as Willy or BJ are included. While helpful in some contexts, filtering usernames against these will be way too aggressive and will annoy users when their real name gets blocked.

VBW aims to solve this by:

1. Gathering profanity from various sources, many of which are themselves aggregated lists.  
2. Running the combined list through the `mangalathkedar/profanity-detector-distilbert-multilingual` classifier model. This is a non‑generative AI model that assigns a score from 0 to 1 to sequences of text.  
3. As an extra step, sending the remaining list through a frontier LLM to double‑check for anything that is not strong profanity, and then doing human review on the results.

---
## Usage

VBW is intended to be used as a **wordlist for a profanity filter**.

Note that profanity filtering via a wordlist is inherently flawed. Many things are context‑ or location‑sensitive, and there are embedded terms and gray areas (for example, “analysis” or “gratitude” containing substrings that look profane). Running the full classifier model is usually the best approach for longer strings of text or messages.

However, a full classifier model is also overkill for simpler domains, such as usernames. This wordlist aims to serve those simpler domains.

VBW is licensed under MIT.

---
## Building

Paste your Gemini API key from AI Studio (https://aistudio.google.com/) into api_key.txt.

```
pip install transformers torch google-generativeai
py aggregate.py
py classify.py
py review.py
```

This will read the data sources and collect them into a single profanity_aggregate.csv, then run classifier to filter the easy ones out, then run Gemini 2.5 Flash queries to fully review the results.
It will then filter the reviews by the LLM review, leaving only the very bad words in vbw.csv, not mild ones and definitely not someone's name.

---

## Data Sources

* https://github.com/4troDev/profanity.csv  
* https://github.com/censor-text/profanity-list
