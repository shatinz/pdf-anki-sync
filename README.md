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
7. **Multiple Launch Options:** Run directly via Python, double-click `run_gui.bat`, or use a standalone executable.

---

## Running the Application

### Option 1: Direct Batch Launcher (Recommended - No False Positives)
Double-click **`run_gui.bat`** in the project directory. This launches the application directly using your local Python environment without triggering heuristic antivirus flags.

### Option 2: Command Line
```bash
python gui.py
```

### Option 3: Standalone Executable (`PDF_Anki_Sync.exe`)
Download or build `PDF_Anki_Sync.exe` for single-file execution without needing an open terminal.

> [!NOTE]
> **Antivirus False Positive Notice (`Win32/Sabsik.TE.A!ml`):**  
> Windows Defender's Heuristic Machine Learning engine (`!ml`) frequently flags uncompiled, unsigned PyInstaller single-file binaries as false positives (`Win32/Sabsik`). This occurs because single-file PyInstaller executables compress Python into an un-signed bootloader that extracts to `%TEMP%` at runtime.  
> **Do not assume an antivirus detection is a false positive.** If Defender flags a binary, avoid running it until you have verified its source and inspected the build. Prefer reviewing the Python source, installing dependencies in a virtual environment, and launching `python gui.py`. Do not disable Defender or add blanket antivirus exclusions.

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
1. Run `run_gui.bat` or `python gui.py`.
2. Verify top-right indicator says **`ANKI CONNECTED`**.
3. Select your **Watch Directory** (the folder containing your PDF books).
4. Click **Save Config**, then **Enable Auto-Watch**.
5. Open any PDF in **Microsoft Edge**, highlight vocabulary words, and press **`Ctrl + S`**.
6. The app automatically extracts the words and syncs them to Anki within 2 seconds!

---

## Building the Executable
To build the `.exe` yourself:
```bash
double-click build_exe.bat
```
Output files are generated under `dist/`.

---

## Project status and release checklist

**Status: experimental / source-only.** The README documents intended functionality, not an independently verified release. The app depends on Anki Desktop, AnkiConnect, local PDF annotation compatibility, and optional external services. Do not publish an executable as a trusted release without completing these checks:

- [ ] Run a clean-environment installation and GUI smoke test on supported Windows versions.
- [ ] Test highlight extraction with Edge-saved PDFs, including repeated saves, non-vocabulary highlights, and malformed PDFs.
- [ ] Test AnkiConnect unavailable, API errors, duplicate prevention, and idempotent re-sync.
- [ ] Verify no credentials, private PDFs, or sensitive annotation content are committed or logged.
- [ ] Audit dependency versions and build artifacts; scan and sign any distributed binary.
- [ ] Add automated tests and CI before marking a stable release.

**Privacy:** PDF highlights and surrounding context may contain personal information. Review any AI/API integration before sending document text to external services.
