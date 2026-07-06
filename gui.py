import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
from sync import CONFIG_FILE, load_config, save_cache, sync_pdf, AnkiConnectClient
from watcher import PDFWatcher

# Palette - Modern Dark Theme (inspired by Catppuccin Mocha)
BG_MAIN = "#1e1e2e"       # Base background
BG_PANEL = "#252538"      # Lighter panel background
BG_INPUT = "#313244"      # Input fields background
FG_MAIN = "#cdd6f4"       # Primary text
FG_MUTED = "#a6adc8"      # Subtext / labels
ACCENT_BLUE = "#89b4fa"   # Primary action / blue accent
ACCENT_GREEN = "#a6e3a1"  # Success / active / green
ACCENT_RED = "#f38ba8"    # Warning / stop / red
ACCENT_YELLOW = "#f9e2af" # Warning / highlight yellow
BORDER_COLOR = "#45475a"

class ModernButton(tk.Label):
    def __init__(self, parent, text, command, bg=ACCENT_BLUE, fg="#11111b", height=1, width=15, **kwargs):
        super().__init__(
            parent, 
            text=text, 
            bg=bg, 
            fg=fg, 
            font=("Segoe UI", 10, "bold"),
            padx=10, 
            pady=6,
            relief="flat",
            cursor="hand2",
            anchor="center",
            width=width,
            height=height,
            **kwargs
        )
        self.command = command
        self.bg_color = bg
        self.fg_color = fg
        
        # Hover effect calculations
        self.hover_color = self._adjust_brightness(bg, -20)
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def set_theme_color(self, bg, fg=None):
        self.bg_color = bg
        self.hover_color = self._adjust_brightness(bg, -20)
        config_args = {"bg": bg}
        if fg is not None:
            self.fg_color = fg
            config_args["fg"] = fg
        self.config(**config_args)

    def _adjust_brightness(self, hex_color, percent):
        # Simple brightness adjustment
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            r = max(0, min(255, r + percent))
            g = max(0, min(255, g + percent))
            b = max(0, min(255, b + percent))
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color

    def _on_click(self, event):
        self.command()

    def _on_enter(self, event):
        self.config(bg=self.hover_color)

    def _on_leave(self, event):
        self.config(bg=self.bg_color)

class PDFAnkiSyncGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Highlights to Anki Automator")
        self.root.geometry("900x650")
        self.root.configure(bg=BG_MAIN)
        
        # Set Windows title bar color to match dark mode if supported
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            use_dark = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 
                ctypes.byref(use_dark), ctypes.sizeof(use_dark)
            )
        except Exception:
            pass

        self.config = load_config()
        self.watcher = None
        self.log_queue = queue.Queue()
        
        # Form Variables
        self.deck_var = tk.StringVar(value=self.config.get("deck_name", "English"))
        self.model_var = tk.StringVar(value=self.config.get("note_type_name", "English-PDF-Vocabulary"))
        self.watch_dir_var = tk.StringVar(value=self.config.get("watch_directory", ""))
        self.api_key_var = tk.StringVar(value=self.config.get("gemini_api_key", ""))
        
        self.setup_styles()
        self.create_widgets()
        
        # Start queue processing
        self.root.after(100, self.process_log_queue)
        
        # Periodic Anki Connect status check
        self.check_anki_status()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Style Notebook/Tabs to match dark mode
        style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_PANEL, foreground=FG_MUTED, borderwidth=0, padding=(15, 5))
        style.map("TNotebook.Tab", background=[("selected", BG_MAIN)], foreground=[("selected", ACCENT_BLUE)])

    def create_widgets(self):
        # Header Banner
        header_frame = tk.Frame(self.root, bg=BG_PANEL, height=70, bd=0)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)
        
        header_title = tk.Label(
            header_frame, 
            text="PDF HIGHLIGHTS TO ANKI", 
            font=("Segoe UI Semibold", 18), 
            fg=ACCENT_BLUE, 
            bg=BG_PANEL
        )
        header_title.pack(side="left", padx=25, pady=15)

        # Connection status light
        self.status_indicator = tk.Label(
            header_frame,
            text="ANKI DISCONNECTED",
            font=("Segoe UI", 9, "bold"),
            fg=ACCENT_RED,
            bg=BG_PANEL,
            padx=10,
            pady=4,
            bd=1,
            relief="solid",
            highlightthickness=0
        )
        self.status_indicator.pack(side="right", padx=25, pady=20)

        # Main Layout container
        main_container = tk.Frame(self.root, bg=BG_MAIN, padx=15, pady=15)
        main_container.pack(fill="both", expand=True)

        # Left Column (Settings Panel)
        left_panel = tk.Frame(main_container, bg=BG_PANEL, width=380, padx=20, pady=20)
        left_panel.pack(fill="both", side="left", expand=False)
        left_panel.pack_propagate(False)
        
        self.style_panel_header(left_panel, "Configuration")

        # Deck Name
        self.create_label_entry(left_panel, "Anki Deck Name", self.deck_var)
        
        # Model / Note Type Name
        self.create_label_entry(left_panel, "Anki Card Type Name", self.model_var)
        
        # Gemini API Key (Optional)
        self.create_label_entry(left_panel, "Gemini API Key (Optional, for context meanings)", self.api_key_var, show="*")
        
        # Watch Directory Label & Selector
        watch_label = tk.Label(left_panel, text="Watch Directory (PDF Folder)", font=("Segoe UI", 10, "bold"), fg=FG_MUTED, bg=BG_PANEL)
        watch_label.pack(anchor="w", pady=(15, 5))
        
        dir_frame = tk.Frame(left_panel, bg=BG_PANEL)
        dir_frame.pack(fill="x", pady=0)
        
        dir_entry = tk.Entry(
            dir_frame, 
            textvariable=self.watch_dir_var, 
            bg=BG_INPUT, 
            fg=FG_MAIN, 
            insertbackground=FG_MAIN, 
            bd=1, 
            relief="flat", 
            font=("Segoe UI", 10)
        )
        dir_entry.pack(fill="x", side="left", expand=True, ipady=4)
        
        browse_btn = ModernButton(
            dir_frame, 
            text="Browse", 
            command=self.browse_watch_dir, 
            bg=BG_INPUT, 
            fg=FG_MAIN,
            width=8
        )
        browse_btn.pack(side="right", padx=(8, 0))

        # Action Buttons frame
        actions_frame = tk.Frame(left_panel, bg=BG_PANEL)
        actions_frame.pack(fill="x", pady=(30, 0))

        # Save Settings
        save_btn = ModernButton(actions_frame, text="Save Config", command=self.save_settings, bg=ACCENT_BLUE, fg="#11111b")
        save_btn.pack(fill="x", pady=5)

        # Sync File manually
        sync_manual_btn = ModernButton(actions_frame, text="Sync PDF Manually", command=self.manual_sync_file, bg=ACCENT_BLUE, fg="#11111b")
        sync_manual_btn.pack(fill="x", pady=5)

        # Divider
        div = tk.Frame(left_panel, bg=BORDER_COLOR, height=1)
        div.pack(fill="x", pady=20)

        # Watcher controls
        self.watcher_status_lbl = tk.Label(
            left_panel, 
            text="AUTO-WATCHER: INACTIVE", 
            font=("Segoe UI", 10, "bold"), 
            fg=FG_MUTED, 
            bg=BG_PANEL
        )
        self.watcher_status_lbl.pack(anchor="w", pady=(0, 5))

        self.watch_toggle_btn = ModernButton(
            left_panel, 
            text="Enable Auto-Watch", 
            command=self.toggle_watcher, 
            bg=ACCENT_GREEN, 
            fg="#11111b"
        )
        self.watch_toggle_btn.pack(fill="x", pady=5)

        # Right Column (Logs Console)
        right_panel = tk.Frame(main_container, bg=BG_PANEL, padx=20, pady=20)
        right_panel.pack(fill="both", side="right", expand=True, padx=(15, 0))
        
        self.style_panel_header(right_panel, "Activity Log")

        log_frame = tk.Frame(right_panel, bg=BG_PANEL)
        log_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_frame, bg=BG_PANEL)
        scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(
            log_frame, 
            bg=BG_INPUT, 
            fg=FG_MAIN, 
            insertbackground=FG_MAIN, 
            yscrollcommand=scrollbar.set, 
            font=("Consolas", 10),
            relief="flat",
            wrap="word",
            bd=0
        )
        self.log_text.pack(fill="both", expand=True, side="left")
        scrollbar.config(command=self.log_text.yview)

        # Styling tags inside text area
        self.log_text.tag_config("info", foreground=ACCENT_BLUE)
        self.log_text.tag_config("success", foreground=ACCENT_GREEN)
        self.log_text.tag_config("warning", foreground=ACCENT_YELLOW)
        self.log_text.tag_config("error", foreground=ACCENT_RED)
        
        # Initial greeting
        self.append_log("System initialized. Connect Anki and select a file/directory to get started.", "info")

    def style_panel_header(self, parent, title):
        lbl = tk.Label(parent, text=title, font=("Segoe UI Semibold", 14), fg=FG_MAIN, bg=BG_PANEL)
        lbl.pack(anchor="w", pady=(0, 15))

    def create_label_entry(self, parent, label_text, variable, show=None):
        lbl = tk.Label(parent, text=label_text, font=("Segoe UI", 10, "bold"), fg=FG_MUTED, bg=BG_PANEL)
        lbl.pack(anchor="w", pady=(15, 5))
        
        entry = tk.Entry(
            parent, 
            textvariable=variable, 
            bg=BG_INPUT, 
            fg=FG_MAIN, 
            insertbackground=FG_MAIN, 
            bd=1, 
            relief="flat", 
            font=("Segoe UI", 10),
            show=show
        )
        entry.pack(fill="x", ipady=4)

    def append_log(self, text, tag="info"):
        self.log_queue.put((text, tag))

    def process_log_queue(self):
        while not self.log_queue.empty():
            msg, tag = self.log_queue.get()
            self.log_text.config(state="normal")
            
            # Print timestamped log
            import datetime
            timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
            self.log_text.insert("end", timestamp, "subtext")
            self.log_text.insert("end", msg + "\n", tag)
            self.log_text.config(state="disabled")
            self.log_text.see("end")
            
        self.root.after(100, self.process_log_queue)

    def check_anki_status(self):
        def task():
            anki = AnkiConnectClient()
            connected = anki.check_connection()
            
            # Thread-safe UI update
            self.root.after(0, lambda: self.update_anki_indicator(connected))
            
        threading.Thread(target=task, daemon=True).start()
        # Re-check status every 10 seconds
        self.root.after(10000, self.check_anki_status)

    def update_anki_indicator(self, connected):
        if connected:
            self.status_indicator.config(
                text="ANKI CONNECTED", 
                fg=ACCENT_GREEN, 
                highlightbackground=ACCENT_GREEN
            )
        else:
            self.status_indicator.config(
                text="ANKI DISCONNECTED", 
                fg=ACCENT_RED, 
                highlightbackground=ACCENT_RED
            )

    def browse_watch_dir(self):
        selected_dir = filedialog.askdirectory(initialdir=self.watch_dir_var.get())
        if selected_dir:
            self.watch_dir_var.set(selected_dir)

    def save_settings(self):
        config_data = {
            "deck_name": self.deck_var.get().strip(),
            "note_type_name": self.model_var.get().strip(),
            "gemini_api_key": self.api_key_var.get().strip(),
            "watch_directory": self.watch_dir_var.get().strip()
        }
        
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            self.config = config_data
            self.append_log("Configuration saved successfully.", "success")
            
            # If watcher is running, restart it to apply the new watch directory
            if self.watcher and self.watcher.is_running():
                self.append_log("Restarting auto-watcher to apply new directory...", "info")
                self.watcher.stop()
                self.watcher.watch_dir = self.config["watch_directory"]
                self.watcher.start()
        except Exception as e:
            self.append_log(f"Failed to save configuration: {e}", "error")
            messagebox.showerror("Error", f"Could not save configuration: {e}")

    def manual_sync_file(self):
        selected_file = filedialog.askopenfilename(
            title="Select PDF file to sync",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not selected_file:
            return

        def run_sync():
            self.append_log(f"Starting manual sync for {os.path.basename(selected_file)}...", "info")
            try:
                # Do a quick check if Anki is running
                anki = AnkiConnectClient()
                is_dry = not anki.check_connection()
                
                count = sync_pdf(selected_file, dry_run=is_dry, log_callback=lambda m: self.append_log(m, "info"))
                
                if is_dry:
                    self.append_log(f"Manual Sync Complete (Dry Run / Cached). Extracted {count} words.", "warning")
                else:
                    self.append_log(f"Manual Sync Complete. Synced {count} words directly to Anki.", "success")
            except Exception as e:
                self.append_log(f"Manual Sync Failed: {e}", "error")
                
        threading.Thread(target=run_sync, daemon=True).start()

    def toggle_watcher(self):
        # Ensure watch folder is set
        watch_folder = self.watch_dir_var.get().strip()
        if not watch_folder or not os.path.exists(watch_folder):
            messagebox.showerror("Error", "Please configure and save a valid watch directory before enabling auto-watcher.")
            return

        if self.watcher is None:
            self.watcher = PDFWatcher(
                watch_dir=watch_folder, 
                log_callback=lambda m: self.append_log(m, "info")
            )

        if self.watcher.is_running():
            self.watcher.stop()
            self.watcher_status_lbl.config(text="AUTO-WATCHER: INACTIVE", fg=FG_MUTED)
            self.watch_toggle_btn.config(text="Enable Auto-Watch")
            self.watch_toggle_btn.set_theme_color(ACCENT_GREEN)
            self.append_log("Auto-watcher disabled.", "warning")
        else:
            # Refresh directory key
            self.watcher.watch_dir = watch_folder
            success = self.watcher.start()
            if success:
                self.watcher_status_lbl.config(text="AUTO-WATCHER: RUNNING", fg=ACCENT_GREEN)
                self.watch_toggle_btn.config(text="Disable Auto-Watch")
                self.watch_toggle_btn.set_theme_color(ACCENT_RED)
                self.append_log("Auto-watcher enabled. Saving highlights in Edge (Ctrl+S) will sync them automatically.", "success")
            else:
                self.append_log("Failed to start auto-watcher.", "error")

    def on_closing(self):
        if self.watcher and self.watcher.is_running():
            self.watcher.stop()
        self.root.destroy()

if __name__ == "__main__":
    # Create scratch folder structure if not exists
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    root = tk.Tk()
    app = PDFAnkiSyncGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
