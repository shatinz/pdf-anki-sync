# PDF Highlights to Anki Sync Tool

A lightweight, automated desktop application that extracts highlighted vocabulary words from PDF files saved in **Microsoft Edge** and syncs them directly to your **Anki** library. It automatically generates rich English definitions, native Text-to-Speech audio, 2–4 natural collocations, example sentences, and extracts the exact context sentence from the PDF.

---

## Features

1. **Auto-Watch Mode:** Run the watcher in the background. Every time you save a PDF (`Ctrl + S` in Microsoft Edge), it automatically scans the PDF and syncs new highlights.
2. **Deep Pattern Learning:** Automatically generates:
   - **Built-in Text-to-Speech (TTS):** Native audio pronunciation powered by Anki's TTS engine (`{{tts en_US:Word}}`).
   - **2–4 Common Collocations:** Learn how words naturally pair together in English.
   - **Natural Example Sentence:** Contextual usage reinforcement.
   - **Synonyms & Antonyms:** Expand vocabulary families.
3. **Smart Word Filter:** Automatically distinguishes between highlighted vocabulary words/phrases (1 to 4 words) and highlighted full sentences. It **skips sentence highlights** to keep your deck focused.
4. **Automatic Card & Template Sync:** Creates or updates the `English-PDF-Vocabulary` Note Type in Anki (styled for both Light and Dark mode). Updating templates retroactively enables speech and formatting for existing cards.
5. **Gemini API & Free Dictionary Support:** AI-powered context-aware breakdowns via Gemini (`gemini-2.5-flash` with rate-limiting pauses and exponential backoff retry logic), with a seamless fallback to the Free Dictionary API.
6. **Modern Dark-Mode GUI:** Easy-to-use control panel with live activity logs and connection status indicators.
7. **Standalone Windows Executable:** Run directly as a single `.exe` file without needing Python installed.

---

## Quick Start (Standalone Executable)

1. Download **`PDF_Anki_Sync.exe`** from the [Latest GitHub Release](https://github.com/shatinz/pdf-anki-sync/releases).
2. Ensure **Anki Desktop** is running with the **AnkiConnect** add-on installed (code: `2055492159`).
3. Double-click **`PDF_Anki_Sync.exe`** to launch the GUI.

---

## Setup & Anki Configuration

### 1. Configure AnkiConnect (Required for Auto-Sync)
To allow external syncs into Anki:
1. Open Anki Desktop.
2. Go to **Tools -> Add-ons -> Get Add-ons...**
3. Paste code **`2055492159`** and click **OK**.
4. Restart Anki.

### 2. Scientific Retention Settings (FSRS Algorithm)
To achieve optimal scientific memory retention (90% target retention rate with minimal review fatigue):
1. In Anki Desktop, click the gear icon ⚙️ next to your deck (or go to **Deck Options**).
2. Scroll down to **Advanced** or **FSRS**.
3. Toggle **Enable FSRS** to **ON**.
4. Set **Desired retention** to **`0.90`** (90% target retention).
5. Click **Save**.

*Why FSRS?* FSRS (Free Spaced Repetition Scheduler) is scientifically proven to reduce review workload by 20–30% compared to Anki's default SM-2 algorithm while maintaining higher long-term retention.

---

## How to Use

### Using the GUI
1. Run `PDF_Anki_Sync.exe` (or `python gui.py`).
2. Verify top-right indicator says **`ANKI CONNECTED`**.
3. Select your **Watch Directory** (the folder containing your PDF books).
4. Click **Save Config**, then **Enable Auto-Watch**.
5. Open any PDF in **Microsoft Edge**, highlight vocabulary words, and press **`Ctrl + S`**.
6. The app automatically extracts the words and syncs them to Anki within 2 seconds!

### Using Python Source
If running from source:
```bash
pip install pymupdf requests pyinstaller
python gui.py
```

---

## Building the Executable
To build the `.exe` yourself:
```bash
double-click build_exe.bat
```
The output file will be generated in `dist/PDF_Anki_Sync.exe`.
