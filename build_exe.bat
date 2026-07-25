@echo off
echo ===================================================
echo Building PDF Highlights to Anki Executable
echo ===================================================
pyinstaller --noconfirm --clean --onefile --windowed ^
    --exclude-module torch ^
    --exclude-module scipy ^
    --exclude-module pandas ^
    --exclude-module numpy ^
    --exclude-module matplotlib ^
    --exclude-module PIL ^
    --exclude-module lxml ^
    --name PDF_Anki_Sync gui.py
echo ===================================================
echo Build complete! Executable is at dist\PDF_Anki_Sync.exe
echo ===================================================
pause
