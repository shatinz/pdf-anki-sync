import tkinter as tk
import sys
from gui import PDFAnkiSyncGUI

def verify_gui():
    print("Initializing Tkinter root...")
    try:
        root = tk.Tk()
        # Hide window frame during verification to avoid flashing on screen
        root.withdraw()
        
        print("Instantiating PDFAnkiSyncGUI...")
        app = PDFAnkiSyncGUI(root)
        
        print("Updating GUI elements to trigger initial layout and draw...")
        root.update()
        
        print("Destroying root instance...")
        root.destroy()
        
        print("\n[SUCCESS] GUI verification passed! All widgets initialized and laid out correctly without error.")
        return True
    except Exception as e:
        print(f"\n[ERROR] GUI verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_gui()
    sys.exit(0 if success else 1)
