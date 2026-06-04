# ui_files/file_viewer.py

import re
import urllib.request
import sys
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtCore import Qt, QUrl, QThread, Signal, QFile
from PySide6.QtUiTools import QUiLoader
from pathlib import Path


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    return os.path.join(base_path, relative_path)


class BadgeCacheWorker(QThread):
    """Background thread to download badge images so the UI doesn't freeze"""
    finished = Signal(str) 

    def __init__(self, html_content: str):
        super().__init__()
        self.html_content = html_content

    def run(self):
        pattern = r'(<img\s[^>]*?)src=[\'"](https?://[^\'"]+)[\'"]'
        
        local_badges_dir = Path(get_resource_path("resources")) / "badges"
        cache_dir = Path(get_resource_path("resources")) / "badge_cache"
        
        local_badges_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        def get_local_badge_path(url):
            filename = url.split("/")[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
            
            if not filename.endswith('.svg') and not filename.endswith('.png'):
                filename += '.svg'
            
            local_path = local_badges_dir / filename
            if local_path.exists():
                return local_path
            
            cache_path = cache_dir / filename
            if cache_path.exists():
                return cache_path
            
            return None
        
        def download_and_replace(match):
            full_tag_start = match.group(1)
            url = match.group(2)
            
            local_path = get_local_badge_path(url)
            
            if local_path and local_path.exists():
                local_url = QUrl.fromLocalFile(str(local_path.absolute())).toString()
                return f'{full_tag_start}src="{local_url}"'
            
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
                local_url = QUrl.fromLocalFile(str(local_path.absolute())).toString()
                return f'{full_tag_start}src="{local_url}"'
            except Exception as e:
                return match.group(0)

        updated_html = re.sub(pattern, download_and_replace, self.html_content)
        self.finished.emit(updated_html)


class FileViewerDialog(QDialog):
    """Reusable dialog to display text files (Markdown or Plain Text)"""
    
    def __init__(self, title: str, file_names: list, is_markdown: bool = False, size: tuple = (600, 450), parent=None):
        super().__init__(parent)
        
        loader = QUiLoader()
        ui_file_path = os.path.join(os.path.dirname(__file__), "..", "ui", "file_viewer.ui")
        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        self.setWindowTitle(title)
        self.resize(size[0], size[1])  
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)
        
        self.ui.close_btn.clicked.connect(self.accept)
        self.ui.close_btn.setStyleSheet("""
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
        
        self.load_file(file_names, is_markdown)
    
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
            self.ui.text_browser.setStyleSheet("""
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
            
            self.ui.text_browser.setHtml(html)
            
            self.cache_worker = BadgeCacheWorker(html)
            self.cache_worker.finished.connect(self.on_badges_cached)
            self.cache_worker.start()
            
        else:
            self.ui.text_browser.setStyleSheet("""
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
            self.ui.text_browser.setPlainText(content)

    def on_badges_cached(self, updated_html: str):
        scroll_pos = self.ui.text_browser.verticalScrollBar().value()
        self.ui.text_browser.setHtml(updated_html)
        self.ui.text_browser.verticalScrollBar().setValue(scroll_pos)