# ui/file_viewer.py
# This module defines a reusable dialog for displaying text files (Markdown or Plain Text) with support for external images. It uses a custom QTextBrowser to handle image loading. 
# The BadgeCacheWorker runs in a background thread to download badge images and update the HTML content without freezing the UI.    

import re
import urllib.request
import sys
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
from PySide6.QtCore import Qt, QUrl, QThread, Signal
from pathlib import Path


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


class BadgeCacheWorker(QThread):
    """Background thread to download badge images so the UI doesn't freeze"""
    finished = Signal(str) 

    def __init__(self, html_content: str):
        super().__init__()
        self.html_content = html_content

    def run(self):
        # FIX: Robust regex that finds src="url" NO MATTER the order of attributes
        pattern = r'(<img\s[^>]*?)src="(https?://[^"]+)"'
        
        # Use local badges folder first (in resources/badges/)
        local_badges_dir = Path(get_resource_path("resources")) / "badges"
        cache_dir = Path(get_resource_path("resources")) / "badge_cache"
        
        # Create directories if they don't exist
        local_badges_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        def get_local_badge_path(url):
            """Extract filename from URL and check local badges folder first"""
            filename = url.split("/")[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
            
            if not filename.endswith('.svg') and not filename.endswith('.png'):
                filename += '.svg'
            
            # Check local badges folder first (shipped with app)
            local_path = local_badges_dir / filename
            if local_path.exists():
                return local_path
            
            # Check cache folder next (previously downloaded)
            cache_path = cache_dir / filename
            if cache_path.exists():
                return cache_path
            
            # Not found locally
            return None
        
        def download_and_replace(match):
            full_tag_start = match.group(1)
            url = match.group(2)
            
            # Try to get local badge first
            local_path = get_local_badge_path(url)
            
            if local_path and local_path.exists():
                # Use local badge (no download needed)
                local_url = QUrl.fromLocalFile(str(local_path.absolute())).toString()
                return f'{full_tag_start}src="{local_url}"'
            
            # Not found locally, download it
            filename = url.split("/")[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
            
            if not filename.endswith('.svg') and not filename.endswith('.png'):
                filename += '.svg'
            
            local_path = cache_dir / filename
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    with open(local_path, 'wb') as f:
                        f.write(response.read())
                print(f"[Cache] Downloaded badge: {filename}")
                local_url = QUrl.fromLocalFile(str(local_path.absolute())).toString()
                return f'{full_tag_start}src="{local_url}"'
            except Exception as e:
                print(f"[Cache] Failed to download {url} - Error: {e}")
                return match.group(0)  # Keep original internet URL if it fails

        updated_html = re.sub(pattern, download_and_replace, self.html_content)
        self.finished.emit(updated_html)


class FileViewerDialog(QDialog):
    """Reusable dialog to display text files (Markdown or Plain Text)"""
    
    def __init__(self, title: str, file_names: list, is_markdown: bool = False, size: tuple = (600, 450), parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(size[0], size[1])  
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True) 
        
        self.load_file(file_names, is_markdown)
        layout.addWidget(self.text_browser)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def load_file(self, possible_names: list, is_markdown: bool):
        base_dir = Path(get_resource_path("."))
        content = f"<i>File not found. Searched for: {', '.join(possible_names)}</i>"
        
        for name in possible_names:
            path = base_dir / name
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8")
                    break
                except Exception:
                    content = f"<i>Error reading file: {name}</i>"
                    
        if is_markdown:
            self.text_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #FFFFFF;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 6px;
                    padding: 15px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 13px;
                }
            """)
            import markdown
            html = markdown.markdown(content, extensions=['extra', 'fenced_code', 'codehilite'])
            
            # 1. Show text IMMEDIATELY (no hang). Badges will just be blank for a microsecond.
            self.text_browser.setHtml(html)
            
            # 2. Start background thread to check local badges and download if needed
            self.cache_worker = BadgeCacheWorker(html)
            self.cache_worker.finished.connect(self.on_badges_cached)
            self.cache_worker.start()
            
        else:
            self.text_browser.setStyleSheet("""
                QTextBrowser {
                    background-color: #F5F5F5;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 6px;
                    padding: 15px;
                    font-family: Consolas, 'Courier New', monospace;
                    font-size: 12px;
                }
            """)
            self.text_browser.setPlainText(content)

    def on_badges_cached(self, updated_html: str):
        """Slot called by the background thread when downloads are complete"""
        # Preserve the user's scroll position so it doesn't jump to the top
        scroll_pos = self.text_browser.verticalScrollBar().value()
        
        # Inject the HTML with the local image paths
        self.text_browser.setHtml(updated_html)
        
        # Restore scroll position
        self.text_browser.verticalScrollBar().setValue(scroll_pos)
        