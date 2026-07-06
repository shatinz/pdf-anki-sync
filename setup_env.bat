@echo off
echo ===================================================
echo Installing dependencies for PDF Highlights to Anki
echo ===================================================
python -m pip install --upgrade pip
pip install pymupdf requests
echo ===================================================
echo Installation complete!
echo ===================================================
pause
