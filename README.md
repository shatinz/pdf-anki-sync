# PDF Highlights to Anki Sync Tool

A lightweight, automated desktop application that extracts highlighted vocabulary words from PDF files saved in **Microsoft Edge** and syncs them directly to your **Anki** library. It automatically generates English definitions and fetches the surrounding context sentence from the PDF.

---

## Features

1. **Auto-Watch Mode:** Run the watcher in the background. Every time you save a PDF (`Ctrl + S` in Microsoft Edge), it automatically scans the PDF and syncs new highlights.
2. **Smart Word Filter:** Automatically distinguishes between highlighted vocabulary words/short phrases (1 to 4 words) and highlighted full sentences. It **skips sentence highlights** to keep your deck focused, but still extracts the correct surrounding context sentence for vocabulary words.
3. **Automatic Card Generation:** Automatically creates the deck and a premium, responsive Note Type (`English-PDF-Vocabulary`) in Anki (styled for both Light and Dark mode) if they don't already exist.
4. **Rich Definitions:** Looks up phonetic pronunciation and dictionary meanings using the free English Dictionary API.
5. **Gemini API Integration (Optional):** If you configure a Gemini API key, the tool will use AI to fetch precise, context-aware translations and definitions tailored exactly to how the word was used in the sentence.
6. **Modern Dark-Mode GUI:** An easy-to-use control panel to manage settings, monitor connection state, view live sync logs, and trigger manual files sync.

---

## Setup Instructions

### 1. Configure Anki Desktop
To enable external integration, Anki needs the **AnkiConnect** add-on installed:
1. Open Anki.
2. Go to **Tools -> Add-ons**.
3. Click **Get Add-ons...** on the right.
4. Paste the code: **`2055492159`** and click **OK**.
5. Restart Anki to activate it. Keep Anki running while syncing!

### 2. Install Python Dependencies
Run the setup batch file located in the project directory to install dependencies (`pymupdf` and `requests`):
- Double-click **`setup_env.bat`** (or open terminal in `C:\prj\pdf-anki-sync` and run `pip install pymupdf requests`).

---

## How to Use

### Using the GUI (Recommended)
1. Double-click or run:
   ```bash
   python gui.py
   ```
2. Check the top-right indicator to verify it says **`ANKI CONNECTED`** (ensure Anki Desktop is running).
3. Select your **Watch Directory** (the folder where you save/read your PDF books).
4. Click **Save Config**.
5. Click **Enable Auto-Watch**. The console will report it is monitoring your files.
6. Now, open any PDF inside that folder using **Microsoft Edge**. Highlight any word you want to learn, and press **`Ctrl + S`** in Edge to save the document. 
7. Within 2 seconds, the console in the GUI will report that the word was successfully synced!

### Using the Command Line (CLI)
You can also sync a single PDF file directly via the terminal:
```bash
python sync.py "C:\path\to\your\book.pdf"
```
To run a test scan without uploading to Anki:
```bash
python sync.py "C:\path\to\your\book.pdf" --dry-run
```

---

## How it works

When a highlight annotation is detected:
- **Geometry Overlap:** The engine analyzes the bounding boxes of the highlight and checks which text block (paragraph) on the page it intersects.
- **Context Extraction:** The paragraph text is split into sentences using a regex parser. The sentence containing the highlighted word/phrase is chosen and formatted to bold the target word.
- **Card Format:**
  - **Front of Card:** Highlighted word and the context sentence (with the word bolded).
  - **Back of Card:** Phonetics, definitions (grouped by parts of speech), and the source book/page information.
- **Local Cache:** Synced annotations are cached by page number, text, and bounding-box coordinates in `synced_highlights.json`. If you edit or delete a card inside Anki, it will not be re-added unless you manually delete the cache file.
