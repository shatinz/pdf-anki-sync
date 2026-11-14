import os
import tempfile
import unittest
from unittest.mock import patch

import fitz
import sync


class SyncTests(unittest.TestCase):
    def test_word_filter(self):
        self.assertTrue(sync.is_valid_word_highlight("take off"))
        self.assertFalse(sync.is_valid_word_highlight("This is a long sentence."))
        self.assertFalse(sync.is_valid_word_highlight("one two three four five"))

    def test_clean_word(self):
        self.assertEqual(sync.clean_word_for_lookup("“hello!”"), "hello")

    def test_dry_run_does_not_poison_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = os.path.join(tmp, "sample.pdf")
            cache_path = os.path.join(tmp, "cache.json")
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), "Vocabulary matters.")
            rects = page.search_for("Vocabulary")
            self.assertTrue(rects)
            page.add_highlight_annot(rects)
            doc.save(pdf_path)
            doc.close()
            with patch.object(sync, "CACHE_FILE", cache_path), patch.object(
                sync, "load_config", return_value={
                    "deck_name": "English", "note_type_name": "Test",
                    "gemini_api_key": "", "watch_directory": ""
                }
            ), patch.object(sync, "fetch_definition_free_dict", return_value="<p>definition</p>"):
                first = sync.sync_pdf(pdf_path, dry_run=True)
                second = sync.sync_pdf(pdf_path, dry_run=True)
                self.assertEqual(first, 1)
                self.assertEqual(second, 1)
                self.assertFalse(os.path.exists(cache_path))


if __name__ == "__main__":
    unittest.main()
