import os
import sys
import fitz
from sync import sync_pdf, load_config, CACHE_FILE

def create_test_pdf(filename="test_book.pdf"):
    print(f"Generating test PDF: {filename}...")
    doc = fitz.open()
    page = doc.new_page(width=595, height=842) # A4 size
    
    # We will write multiple paragraphs
    p1 = "Technology has made information ubiquitous in modern times, changing how we learn."
    p2 = "Sometimes we need to make ad hoc decisions to solve immediate problems."
    p3 = "This is an entire sentence that has been highlighted by the user to remember the whole idea. It is quite long."
    p4 = "Learning a foreign language requires dedication and persistent practice."
    
    page.insert_text((50, 100), p1, fontsize=11)
    page.insert_text((50, 150), p2, fontsize=11)
    page.insert_text((50, 200), p3, fontsize=11)
    page.insert_text((50, 250), p4, fontsize=11)
    
    # Add highlights by searching for text
    # 1. Single word highlight: "ubiquitous"
    rects1 = page.search_for("ubiquitous")
    if rects1:
        page.add_highlight_annot(rects1[0])
        
    # 2. Phrase highlight: "ad hoc"
    rects2 = page.search_for("ad hoc")
    if rects2:
        page.add_highlight_annot(rects2[0])
        
    # 3. Full sentence highlight (should be filtered out by sync.py)
    rects3 = page.search_for("This is an entire sentence that has been highlighted by the user to remember the whole idea.")
    if rects3:
        page.add_highlight_annot(rects3[0])
        
    # 4. Another single word: "dedication"
    rects4 = page.search_for("dedication")
    if rects4:
        page.add_highlight_annot(rects4[0])
        
    doc.save(filename)
    doc.close()
    print("Test PDF generated successfully.")

def test_sync():
    pdf_file = "test_book.pdf"
    create_test_pdf(pdf_file)
    
    # Remove existing cache if any to start fresh
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        
    print("\nRunning sync_pdf in DRY RUN mode...")
    # Run sync in dry-run mode so it doesn't try to connect to Anki
    new_words = sync_pdf(pdf_file, dry_run=True)
    
    print("\nVerification results:")
    print(f"Total new words synced: {new_words}")
    
    # Read the cache file to see what was cached and what was skipped
    import json
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            
        abs_path = os.path.abspath(pdf_file)
        entries = cache.get(abs_path, [])
        
        print("\nCache Entries:")
        synced_words = []
        skipped_words = []
        for entry in entries:
            word = entry["word"]
            rect = entry["rect"]
            skipped = entry.get("skipped", False)
            if skipped:
                skipped_words.append(word)
                print(f"  [SKIPPED SENTENCE] Text: '{word}'")
            else:
                synced_words.append(word)
                print(f"  [SYNCED WORD]     Text: '{word}'")
                
        # Assertions
        assert "ubiquitous" in synced_words, "Failed to sync 'ubiquitous'"
        assert "ad hoc" in synced_words, "Failed to sync 'ad hoc'"
        assert "dedication" in synced_words, "Failed to sync 'dedication'"
        # Check that the long sentence was skipped
        assert len(skipped_words) == 1, f"Expected 1 skipped sentence, got {len(skipped_words)}"
        print("\n[SUCCESS] Verification passed! Only highlighted words/phrases were synced. Highlighted sentences were successfully skipped.")
    else:
        print("\n[ERROR] Cache file not created!")
        sys.exit(1)

    # Clean up test files
    try:
        os.remove(pdf_file)
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        print("Cleaned up temporary test files.")
    except Exception as e:
        print(f"Error cleaning up test files: {e}")

if __name__ == "__main__":
    test_sync()
