import os
import time
import threading
from sync import sync_pdf, load_config

class PDFWatcher:
    def __init__(self, watch_dir=None, log_callback=None, check_interval=2):
        self.watch_dir = watch_dir
        self.log_callback = log_callback
        self.check_interval = check_interval
        self._stop_event = threading.Event()
        self.thread = None
        self.file_states = {}  # maps absolute path -> (mtime, size)

    def log(self, msg):
        print(msg)
        if self.log_callback:
            self.log_callback(msg)

    def get_watch_directory(self):
        if self.watch_dir and os.path.exists(self.watch_dir):
            return self.watch_dir
        # Fall back to config
        config = load_config()
        return config.get("watch_directory", "")

    def scan_directory(self, directory):
        pdf_files = {}
        if not directory or not os.path.exists(directory):
            return pdf_files
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(".pdf"):
                        abs_path = os.path.join(root, file)
                        try:
                            stat = os.stat(abs_path)
                            pdf_files[abs_path] = (stat.st_mtime, stat.st_size)
                        except OSError:
                            # File might be locked/in use
                            pass
        except Exception as e:
            self.log(f"Error scanning directory: {e}")
        return pdf_files

    def _run(self):
        self.log(f"Starting folder watcher on: '{self.watch_dir}'")
        # Initial scan to populate baseline states
        self.file_states = self.scan_directory(self.watch_dir)
        self.log(f"Baseline established. Monitoring {len(self.file_states)} PDF file(s).")

        # Stable file tracker to handle slow writes (wait 1 cycle after change before syncing)
        pending_syncs = {}

        while not self._stop_event.is_set():
            # Refresh watch directory dynamically in case it changed
            current_dir = self.get_watch_directory()
            if not current_dir or not os.path.exists(current_dir):
                self.log(f"Watch directory invalid or not set: '{current_dir}'. Waiting...")
                time.sleep(5)
                continue
                
            self.watch_dir = current_dir
            current_files = self.scan_directory(self.watch_dir)

            # Check for modified or new files
            for path, (mtime, size) in current_files.items():
                if path not in self.file_states:
                    # New file detected
                    self.log(f"New PDF detected: {os.path.basename(path)}")
                    pending_syncs[path] = (mtime, size, time.time())
                else:
                    old_mtime, old_size = self.file_states[path]
                    if mtime > old_mtime or size != old_size:
                        # Modified file detected
                        pending_syncs[path] = (mtime, size, time.time())

            # Check for deleted files
            deleted_files = [path for path in self.file_states if path not in current_files]
            for path in deleted_files:
                self.log(f"PDF removed from watch folder: {os.path.basename(path)}")
                if path in pending_syncs:
                    del pending_syncs[path]

            # Process pending syncs once they are stable (i.e. size hasn't changed for 2 seconds)
            completed_syncs = []
            for path, (mtime, size, last_change_time) in list(pending_syncs.items()):
                # Check if it has been stable for at least 2 seconds
                if time.time() - last_change_time >= 2:
                    try:
                        # Ensure the file is not currently open/locked for writing by Edge
                        with open(path, 'rb') as _:
                            pass
                        
                        self.log(f"PDF stable. Syncing highlights from {os.path.basename(path)}...")
                        sync_pdf(path, log_callback=self.log)
                        completed_syncs.append(path)
                    except (IOError, PermissionError):
                        # File is still locked (Edge is writing/saving it). Defer sync.
                        self.log(f"File {os.path.basename(path)} is locked. Deferring sync until unlocked...")
                        # Update last change time to defer
                        pending_syncs[path] = (mtime, size, time.time())

            # Clean up processed syncs
            for path in completed_syncs:
                del pending_syncs[path]

            # Update master file state list
            self.file_states = current_files
            
            # Wait for next check or shutdown event
            self._stop_event.wait(self.check_interval)

        self.log("Watcher thread stopped.")

    def start(self):
        watch_dir = self.get_watch_directory()
        if not watch_dir or not os.path.exists(watch_dir):
            self.log(f"Error: Cannot start watcher. Directory '{watch_dir}' does not exist.")
            return False
            
        if self.thread and self.thread.is_alive():
            self.log("Watcher is already running.")
            return True

        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.log("Stopping watcher...")
            self._stop_event.set()
            self.thread.join(timeout=3)
            self.thread = None
            return True
        return False

    def is_running(self):
        return self.thread is not None and self.thread.is_alive()

if __name__ == "__main__":
    import sys
    config = load_config()
    target_dir = sys.argv[1] if len(sys.argv) > 1 else config.get("watch_directory", "")
    
    if not target_dir:
        print("Usage: python watcher.py <directory_to_watch>")
        sys.exit(1)
        
    watcher = PDFWatcher(watch_dir=target_dir)
    try:
        watcher.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
