import os
import sys
import json
import re
import requests
import fitz  # PyMuPDF

# Configuration defaults
DEFAULT_CONFIG = {
    "deck_name": "English",
    "note_type_name": "English-PDF-Vocabulary",
    "gemini_api_key": "",
    "watch_directory": ""
}

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synced_highlights.json")

# Styling for Anki cards (Dark and Light responsive)
ANKI_CARD_CSS = """
.card {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
  font-size: 20px;
  text-align: center;
  padding: 25px;
  color: #333333;
  background-color: #ffffff;
  transition: all 0.3s ease;
}
.nightMode.card, .night_mode .card {
  color: #e0e0e0;
  background-color: #1e1e1e;
}
.word {
  font-size: 36px;
  font-weight: 700;
  color: #0077cc;
  margin-bottom: 10px;
  letter-spacing: -0.5px;
}
.nightMode .word, .night_mode .word {
  color: #4fc3f7;
}
.context {
  font-style: italic;
  color: #555555;
  margin-top: 15px;
  padding: 12px 18px;
  border-left: 4px solid #00acc1;
  background-color: #f7f9fa;
  display: inline-block;
  text-align: left;
  border-radius: 6px;
  max-width: 90%;
  line-height: 1.5;
}
.nightMode .context, .night_mode .context {
  color: #b0bec5;
  background-color: #263238;
}
.context b {
  color: #d84315;
  font-weight: 700;
  border-bottom: 2px dashed #d84315;
}
.nightMode .context b, .night_mode .context b {
  color: #ffb74d;
  border-bottom: 2px dashed #ffb74d;
}
.definition-container {
  text-align: left;
  margin-top: 25px;
  padding: 18px;
  border-radius: 8px;
  background-color: #fcfcfc;
  border: 1px solid #eef0f2;
  box-shadow: 0 2px 5px rgba(0,0,0,0.03);
  display: inline-block;
  width: 90%;
  box-sizing: border-box;
}
.nightMode .definition-container, .night_mode .definition-container {
  background-color: #2b2b2b;
  border: 1px solid #383838;
  box-shadow: 0 4px 6px rgba(0,0,0,0.2);
}
.part-of-speech {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: #2e7d32;
  font-weight: 700;
  margin-top: 12px;
  margin-bottom: 4px;
}
.nightMode .part-of-speech, .night_mode .part-of-speech {
  color: #81c784;
}
.definition-container ul {
  margin: 0;
  padding-left: 20px;
}
.definition-container li {
  margin-bottom: 8px;
  line-height: 1.4;
}
.divider {
  border: 0;
  height: 1px;
  background-image: linear-gradient(to right, rgba(0,0,0,0.05), rgba(0,119,204,0.4), rgba(0,0,0,0.05));
  margin: 20px 0;
}
.nightMode .divider, .night_mode .divider {
  background-image: linear-gradient(to right, rgba(255,255,255,0), rgba(79,195,247,0.4), rgba(255,255,255,0));
}
.source {
  font-size: 11px;
  color: #888888;
  margin-top: 25px;
  letter-spacing: 0.5px;
}
"""

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Ensure all keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception as e:
        print(f"Error loading config: {e}. Using defaults.")
        return DEFAULT_CONFIG

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading cache: {e}. Starting fresh.")
        return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4)
    except Exception as e:
        print(f"Error saving cache: {e}")

class AnkiConnectClient:
    def __init__(self, server_url="http://localhost:8765"):
        self.server_url = server_url

    def _send(self, action, params=None):
        payload = {"action": action, "version": 6}
        if params:
            payload["params"] = params
        try:
            response = requests.post(self.server_url, json=payload, timeout=5)
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("error"):
                    print(f"AnkiConnect Error for {action}: {res_json['error']}")
                    return None
                return res_json.get("result")
        except requests.exceptions.ConnectionError:
            print("AnkiConnect Connection Error: Is Anki running with the AnkiConnect add-on installed?")
        except Exception as e:
            print(f"AnkiConnect request failed: {e}")
        return None

    def check_connection(self):
        return self._send("version") is not None

    def create_deck_if_not_exists(self, deck_name):
        decks = self._send("deckNames")
        if decks is not None and deck_name not in decks:
            print(f"Creating deck '{deck_name}'...")
            return self._send("createDeck", {"deck": deck_name})
        return True

    def create_model_if_not_exists(self, model_name):
        models = self._send("modelNames")
        fields = ["Word", "Definition", "Context", "Source"]
        card_templates_dict = {
            "Card 1": {
                "Front": '<div class="word">{{Word}}</div>\n<hr class="divider">\n<div class="context">{{Context}}</div>',
                "Back": '{{FrontSide}}\n<hr class="divider">\n<div class="definition-container">\n  <div class="definition">{{Definition}}</div>\n</div>\n<div class="source">Source: {{Source}}</div>\n<div style="display:none;">{{tts en_US:Word}}</div>'
            }
        }
        
        if models is not None and model_name not in models:
            print(f"Creating note type '{model_name}'...")
            card_templates_list = [
                {
                    "Name": "Card 1",
                    "Front": card_templates_dict["Card 1"]["Front"],
                    "Back": card_templates_dict["Card 1"]["Back"]
                }
            ]
            self._send("createModel", {
                "modelName": model_name,
                "inOrderFields": fields,
                "css": ANKI_CARD_CSS,
                "cardTemplates": card_templates_list
            })
        else:
            # Note type exists - update templates and styling to apply TTS and styling changes!
            print(f"Updating templates and styling for note type '{model_name}' to verify TTS capability...")
            self._send("updateModelTemplates", {
                "model": {
                    "name": model_name,
                    "templates": card_templates_dict
                }
            })
            self._send("updateModelStyling", {
                "model": {
                    "name": model_name,
                    "css": ANKI_CARD_CSS
                }
            })
        return True

    def note_exists(self, word, deck_name, model_name):
        # Escaping quotes for search query
        escaped_word = word.replace('"', '\\"')
        query = f'deck:"{deck_name}" note:"{model_name}" Word:"{escaped_word}"'
        note_ids = self._send("findNotes", {"query": query})
        return bool(note_ids)

    def add_note(self, deck_name, model_name, fields, tags=None):
        note = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck"
            }
        }
        if tags:
            note["tags"] = tags
        return self._send("addNote", {"note": note})

def fetch_definition_free_dict(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.strip()}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                entry = data[0]
                meanings = entry.get("meanings", [])
                phonetics = entry.get("phonetics", [])
                
                phonetic_text = entry.get("phonetic", "")
                if not phonetic_text and phonetics:
                    for ph in phonetics:
                        if ph.get("text"):
                            phonetic_text = ph["text"]
                            break
                
                html = ""
                if phonetic_text:
                    html += f"<p style='font-style: italic; color: #888; margin: 0 0 10px 0;'>Phonetic: {phonetic_text}</p>"
                
                for meaning in meanings:
                    pos = meaning.get("partOfSpeech", "")
                    html += f"<div class='part-of-speech'>{pos}</div><ul>"
                    # Top 3 definitions
                    for d in meaning.get("definitions", [])[:3]:
                        def_text = d.get("definition", "")
                        example = d.get("example", "")
                        html += f"<li>{def_text}"
                        if example:
                            html += f" <br><span style='color: #888; font-style: italic;'>Example: \"{example}\"</span>"
                        html += "</li>"
                    html += "</ul>"
                return html
    except Exception as e:
        print(f"Dictionary API lookup failed for '{word}': {e}")
    return None

def fetch_definition_gemini(word, context, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    prompt = f"""
Provide the English definition, part of speech, and phonetic spelling for the word/phrase "{word}" based on its context.

Context: "{context}"

Format the response as clean HTML to be displayed on the back of an Anki card.
Use the following styling elements:
- Wrap parts of speech in `<div class="part-of-speech">`
- Wrap definition points in `<ul>` and `<li>`
- Keep the phonetic spelling at the top wrapped in `<p style='font-style: italic; color: #888; margin: 0 0 10px 0;'>Phonetic: ...</p>`
Keep it concise and relevant to the meaning in this specific sentence. Do NOT wrap the code in ```html or other markdown blocks. Return raw HTML.
"""
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            html = result['candidates'][0]['content']['parts'][0]['text']
            # Strip markdown code blocks if present
            html = re.sub(r"^```html\s*", "", html, flags=re.IGNORECASE)
            html = re.sub(r"```$", "", html)
            return html.strip()
    except Exception as e:
        print(f"Gemini API lookup failed for '{word}': {e}")
    return None

def clean_text(text):
    if not text:
        return ""
    # Remove hyphens at line endings and combine whitespace
    text = text.replace("-\n", "").replace("\n", " ")
    return " ".join(text.split())

def clean_word_for_lookup(text):
    if not text:
        return ""
    # Strip smart/normal quotes, punctuation, and brackets from start and end
    # but preserve interior ones (like hyphens in 'self-evident' or apostrophes in 'user's')
    text = text.strip()
    text = re.sub(r'^[\W_]+', '', text)
    text = re.sub(r'[\W_]+$', '', text)
    return text.strip()

def get_sentence_containing_word(page, highlight_rect, word_text):
    # Find all text blocks on the page
    blocks = page.get_text("blocks")
    
    target_block_text = ""
    for b in blocks:
        block_rect = fitz.Rect(b[:4])
        # Check if the highlight rectangle intersects this text block
        if block_rect.intersects(highlight_rect):
            target_block_text = b[4]
            break
            
    if not target_block_text:
        # Fallback to the whole page text
        target_block_text = page.get_text("text")
        
    # Clean text
    cleaned_block = clean_text(target_block_text)
    
    # Sentence splitter: splits on . ! ? followed by space and capital letter (or end of line)
    sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'(])')
    sentences = sentence_endings.split(cleaned_block)
    
    # Try finding the exact sentence
    clean_word = word_text.strip().lower()
    for sentence in sentences:
        if clean_word in sentence.lower():
            return sentence.strip()
            
    # Fallback search (match parts of multi-word highlights)
    for sentence in sentences:
        words = [w.lower() for w in clean_word.split() if len(w) > 2]
        if words and any(w in sentence.lower() for w in words):
            return sentence.strip()
            
    # Ultimate fallback: return a reasonable snippet
    return cleaned_block[:250] + "..." if len(cleaned_block) > 250 else cleaned_block

def bold_word_in_sentence(sentence, word):
    # Escape word for regex
    escaped = re.escape(word.strip())
    # Try matching full word first
    pattern = re.compile(rf'\b({escaped})\b', re.IGNORECASE)
    if pattern.search(sentence):
        return pattern.sub(r'<b>\1</b>', sentence)
    
    # Fallback to loose replacement if word boundaries don't align perfectly (e.g. in some PDFs)
    pattern_loose = re.compile(rf'({escaped})', re.IGNORECASE)
    return pattern_loose.sub(r'<b>\1</b>', sentence)

def is_valid_word_highlight(text):
    text_clean = text.strip()
    if not text_clean:
        return False
        
    words = text_clean.split()
    # Filter: Only allow 1 to 4 words
    if len(words) < 1 or len(words) > 4:
        return False
        
    # Filter: Reject highlights with sentence terminators
    if any(term in text_clean for term in ['.', '!', '?']):
        # Exception: abbreviations or decimals (like "U.S." or "1.5")
        if not re.match(r'^[A-Z]\.[A-Z]\.$|^[0-9]+\.[0-9]+$', text_clean):
            return False
            
    return True

def sync_pdf(pdf_path, dry_run=False, log_callback=None):
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_activity.log")

    def log(msg):
        print(msg)
        if log_callback:
            log_callback(msg)
        # Write to local file for persistent debugging logs
        try:
            with open(log_file, "a", encoding="utf-8") as lf:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                lf.write(f"[{timestamp}] {msg}\n")
        except Exception:
            pass

    if not os.path.exists(pdf_path):
        log(f"Error: File not found - {pdf_path}")
        return 0

    log(f"Opening PDF: {os.path.basename(pdf_path)}...")
    config = load_config()
    cache = load_cache()
    
    # Get absolute path key for cache
    abs_pdf_path = os.path.abspath(pdf_path)
    if abs_pdf_path not in cache:
        cache[abs_pdf_path] = []

    synced_coords = {tuple(h["rect"]) for h in cache[abs_pdf_path]}

    # Initialize Anki Client (if not dry run)
    anki = None
    if not dry_run:
        anki = AnkiConnectClient()
        if not anki.check_connection():
            log("[WARNING] Anki is not running or AnkiConnect is not installed. Running in Dry Run / Cache-only mode.")
            dry_run = True
        else:
            anki.create_deck_if_not_exists(config["deck_name"])
            anki.create_model_if_not_exists(config["note_type_name"])

    doc = fitz.open(pdf_path)
    new_highlights_count = 0
    skipped_sentences_count = 0
    pdf_filename = os.path.basename(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        annots = list(page.annots())
        if not annots:
            continue
            
        # Get all words on the page once to check intersections
        words = page.get_text("words")
        
        for annot in annots:
            # Type 8 is Highlight in PyMuPDF
            if annot.type[0] == 8:
                rect = list(annot.rect)
                rect_tuple = tuple(rect)

                # Skip if already synced
                if rect_tuple in synced_coords:
                    continue

                # Extract highlighted text using word-level intersections
                # to prevent adjacent text bleed from character kerning
                highlighted_words = []
                for w in words:
                    word_rect = fitz.Rect(w[:4])
                    intersect = word_rect & annot.rect
                    if not intersect.is_empty:
                        # Check if at least 40% of the word is within the highlight box
                        if intersect.get_area() / word_rect.get_area() > 0.4:
                            highlighted_words.append(w[4])
                
                highlight_text = " ".join(highlighted_words)
                highlight_text = clean_text(highlight_text)

                if not highlight_text:
                    continue

                # Validate highlight is a word/phrase, not a sentence
                if not is_valid_word_highlight(highlight_text):
                    # Silently skip highlighted sentences/paragraphs
                    skipped_sentences_count += 1
                    # Mark as processed in cache anyway to avoid checking it again
                    cache[abs_pdf_path].append({
                        "page": page_num + 1,
                        "word": highlight_text[:30] + "...",
                        "rect": rect,
                        "skipped": True
                    })
                    continue

                # Clean the word for lookups, duplicate checks, and note fields
                clean_word = clean_word_for_lookup(highlight_text)
                if not clean_word:
                    continue

                log(f"Found new highlight: '{highlight_text}' (Cleaned: '{clean_word}') on Page {page_num + 1}")

                # Extract context sentence using the cleaned word
                context_sentence = get_sentence_containing_word(page, annot.rect, clean_word)
                formatted_context = bold_word_in_sentence(context_sentence, clean_word)

                # Fetch definition
                definition = None
                if config["gemini_api_key"]:
                    log(f"Fetching Gemini API definition for '{clean_word}'...")
                    definition = fetch_definition_gemini(clean_word, context_sentence, config["gemini_api_key"])
                
                if not definition:
                    log(f"Fetching Free Dictionary API definition for '{clean_word}'...")
                    definition = fetch_definition_free_dict(clean_word)

                if not definition:
                    definition = f"<p>Definition lookup failed. (Word: {clean_word})</p>"

                # Add to Anki
                success = True
                if not dry_run and anki:
                    # Check for duplicates in Anki deck
                    if anki.note_exists(clean_word, config["deck_name"], config["note_type_name"]):
                        log(f"Note for '{clean_word}' already exists in deck '{config['deck_name']}'. Skipping Anki upload.")
                    else:
                        fields = {
                            "Word": clean_word,
                            "Definition": definition,
                            "Context": formatted_context,
                            "Source": f"{pdf_filename} (Page {page_num + 1})"
                        }
                        note_id = anki.add_note(config["deck_name"], config["note_type_name"], fields)
                        if note_id:
                            log(f"Successfully added '{clean_word}' to Anki (ID: {note_id})")
                        else:
                            log(f"[ERROR] Failed to add '{clean_word}' to Anki.")
                            success = False

                if success:
                    # Add to local cache
                    cache[abs_pdf_path].append({
                        "page": page_num + 1,
                        "word": highlight_text,
                        "rect": rect,
                        "skipped": False
                    })
                    new_highlights_count += 1

    doc.close()

    if new_highlights_count > 0 or skipped_sentences_count > 0:
        save_cache(cache)

    log(f"Sync complete. Added {new_highlights_count} new words. Skipped {skipped_sentences_count} sentence highlights.")
    return new_highlights_count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sync.py <path_to_pdf> [--dry-run]")
        sys.exit(1)
        
    pdf_file = sys.argv[1]
    is_dry = "--dry-run" in sys.argv
    
    sync_pdf(pdf_file, dry_run=is_dry)
