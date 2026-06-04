# ui_files/frontend.py

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox, QInputDialog, 
    QTableWidgetItem, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QSettings, QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QColor, QAction
from application.backend import DuplicateFinderBackend
from application.ui_files.file_viewer import FileViewerDialog

class LoadWorker(QThread):
    """Worker thread for loading files without freezing UI"""
    finished = Signal(int, list)  # count, duplicates
    error = Signal(str)
    
    def __init__(self, backend, file_paths):
        super().__init__()
        self.backend = backend
        self.file_paths = file_paths
    
    def run(self):
        try:
            count, duplicates = self.backend.load_json_files(self.file_paths)
            self.finished.emit(count, duplicates)
        except Exception as e:
            self.error.emit(str(e))

class DuplicateFinderUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = DuplicateFinderBackend()
        self.worker = None
        self.show_only_duplicates = False
        
        # Initialize Settings
        self.settings = QSettings("JSONDuplicateFinder", "App")
        saved_pattern = self.settings.value("key_pattern", r'.*?-.*\d.*')
        self.backend.set_key_pattern(saved_pattern)
        
        # Enable Drag and Drop
        self.setAcceptDrops(True)
        
        self.init_ui()
    
    def init_ui(self):
        # Load the UI file
        loader = QUiLoader()
        ui_file_path = os.path.join(os.path.dirname(__file__), "..", "ui", "mainwindow.ui")
        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        # Apply the loaded widget as central widget
        self.setCentralWidget(self.ui.centralwidget)
        self.setStatusBar(self.ui.statusbar)
        
        self.setWindowTitle("JSON Duplicate Finder - Video Code Scanner")
        self.setGeometry(100, 100, 1400, 800)
        self.showMaximized() 
        
        # Top Frame Buttons
        self.ui.load_btn.clicked.connect(self.load_files)
        self.ui.reset_btn.clicked.connect(self.reset_all)
        self.ui.export_btn.clicked.connect(self.export_report)
        
        # Recreate menu bar programmatically since it was removed from UI file
        self.create_menu_bar()
        
        # Context Menu for loaded files
        self.ui.files_list.customContextMenuRequested.connect(self.show_files_context_menu)
        
        # Tab Buttons
        self.ui.export_duplicates_btn.clicked.connect(self.export_duplicates_csv)
        self.ui.export_all_btn.clicked.connect(self.export_all_entries_csv)
        self.ui.export_dupes_btn.clicked.connect(self.export_duplicate_entries_csv)
        self.ui.clear_search_btn.clicked.connect(self.clear_search)
        
        # Inputs
        self.ui.search_input.textChanged.connect(self.on_search_changed)
        self.ui.show_duplicates_checkbox.toggled.connect(self.on_filter_changed)
        
        # Init table headers
        self.ui.duplicates_table.setHorizontalHeaderLabels(["Code", "Occurrences", "Files", "Filenames", "Sizes (MB)"])
        self.ui.all_entries_table.setHorizontalHeaderLabels(["Code", "Source File", "Filename", "Size (MB)"])
        
        self.apply_styles()
        self.update_ui()
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        json_files = [f for f in files if f.lower().endswith('.json')]
        if json_files:
            self._start_loading(json_files)
            
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("📁 File")
        
        load_action = QAction("📂 Load JSON Files", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_files)
        file_menu.addAction(load_action)
        
        reset_action = QAction("🗑️ Reset All", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self.reset_all)
        file_menu.addAction(reset_action)
        
        export_action = QAction("💾 Export Report", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_report)
        file_menu.addAction(export_action)
        
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        help_menu = menubar.addMenu("❓ Help")
        
        about_action = QAction("📖 About Us", self)
        about_action.setShortcut("F1")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        readme_action = QAction("📄 Readme", self)
        readme_action.setShortcut("F2")
        readme_action.triggered.connect(self.show_readme)
        help_menu.addAction(readme_action)
        
        license_action = QAction("⚖️ License", self)
        license_action.setShortcut("F3")
        license_action.triggered.connect(self.show_license)
        help_menu.addAction(license_action)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QTableWidget { gridline-color: #bdc3c7; }
            QTableWidget::item:selected { background-color: #3498db; color: white; }
            QMenuBar { background-color: #34495e; color: white; }
            QMenuBar::item:selected { background-color: #3498db; }
            QMenu { background-color: #34495e; color: white; }
            QMenu::item:selected { background-color: #3498db; }
        """)
        self.ui.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.ui.info_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        self.ui.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)

    def show_settings(self):
        current_pattern = self.backend.key_pattern
        pattern, ok = QInputDialog.getText(self, "Settings", "Enter Key Regex Pattern:", text=current_pattern)
        if ok and pattern:
            self.backend.set_key_pattern(pattern)
            self.settings.setValue("key_pattern", pattern)
            QMessageBox.information(self, "Settings Saved", "Key pattern updated. Future file loads will use this regex.")
    
    def show_about(self):
        dialog = FileViewerDialog(
            title="About JSON Duplicate Finder",
            file_names=["aboutus.md", "ABOUTUS.md", "about.md", "ABOUT.md"],
            is_markdown=True,
            size=(700, 600)
        )
        dialog.exec()
    
    def show_readme(self):
        dialog = FileViewerDialog(
            title="Readme - JSON Duplicate Finder",
            file_names=["README.md", "readme.md", "Readme.md"],
            is_markdown=True,
            size=(800, 600)
        )
        dialog.exec()
    
    def show_license(self):
        dialog = FileViewerDialog(
            title="License - MIT License",
            file_names=["LICENSE.md", "license.md", "LICENSE"],
            is_markdown=True,
            size=(700, 550)
        )
        dialog.exec()
        
    def show_files_context_menu(self, position):
        item = self.ui.files_list.itemAt(position)
        if item:
            menu = QMenu()
            unload_action = menu.addAction("Unload File")
            action = menu.exec(self.ui.files_list.mapToGlobal(position))
            if action == unload_action:
                file_path = item.text()
                self.backend.unload_file(file_path)
                self.update_ui()
                self.ui.statusbar.showMessage(f"Unloaded {os.path.basename(file_path)}")
    
    def on_filter_changed(self, checked):
        self.show_only_duplicates = checked
        self.update_all_entries_table()
    
    def load_files(self):
        last_dir = self.settings.value("last_dir", "")
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select JSON Files", last_dir, "JSON Files (*.json);;All Files (*.*)"
        )
        if not file_paths:
            return
            
        self.settings.setValue("last_dir", os.path.dirname(file_paths[0]))
        self._start_loading(file_paths)
        
    def _start_loading(self, file_paths):
        self.ui.load_btn.setEnabled(False)
        self.ui.progress_bar.setVisible(True)
        self.ui.progress_bar.setRange(0, 0)
        self.ui.statusbar.showMessage(f"Loading {len(file_paths)} file(s)...")
        
        self.worker = LoadWorker(self.backend, file_paths)
        self.worker.finished.connect(self.on_files_loaded)
        self.worker.error.connect(self.on_load_error)
        self.worker.start()
    
    def on_files_loaded(self, count, duplicates):
        self.ui.progress_bar.setVisible(False)
        self.ui.load_btn.setEnabled(True)
        self.ui.reset_btn.setEnabled(True)
        self.ui.export_btn.setEnabled(True)
        
        if count > 0:
            msg = f"✅ Loaded {count} entries from {len(self.backend.loaded_files)} file(s)"
            if duplicates:
                msg += f" (⚠️ Found {len(duplicates)} new duplicates)"
            self.ui.statusbar.showMessage(msg)
            self.update_ui()
            if duplicates:
                QMessageBox.information(self, "Duplicates Found", 
                    f"Found {len(duplicates)} duplicate code(s)! Check the 'Duplicates' tab.")
        else:
            self.ui.statusbar.showMessage("⚠️ No valid entries found")
            self.update_ui()
    
    def on_load_error(self, error_msg):
        self.ui.progress_bar.setVisible(False)
        self.ui.load_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to load files:\n{error_msg}")
        self.update_ui()
    
    def update_ui(self):
        self.ui.files_list.clear()
        for file_path in self.backend.loaded_files:
            self.ui.files_list.addItem(file_path)
        
        self.update_duplicates_table()
        self.update_all_entries_table()
        
        summary = self.backend.get_summary()
        self.ui.info_label.setText(
            f"📊 Summary: {summary['total_files']} file(s) | "
            f"{summary['total_unique_codes']} unique codes | "
            f"{summary['duplicate_codes']} duplicates ({summary['total_duplicate_occurrences']} occurrences)"
        )
        self.ui.export_btn.setEnabled(summary['duplicate_codes'] > 0)
    
    def update_duplicates_table(self):
        duplicates = self.backend.get_duplicates()
        self.ui.duplicates_table.setRowCount(len(duplicates))
        
        for row, (code, entries) in enumerate(duplicates.items()):
            self.ui.duplicates_table.setItem(row, 0, QTableWidgetItem(code))
            self.ui.duplicates_table.setItem(row, 1, QTableWidgetItem(str(len(entries))))
            self.ui.duplicates_table.setItem(row, 2, QTableWidgetItem(', '.join(set(e['source_file'] for e in entries))))
            self.ui.duplicates_table.setItem(row, 3, QTableWidgetItem('\n'.join(e['filename'][:50] for e in entries)))
            self.ui.duplicates_table.setItem(row, 4, QTableWidgetItem(', '.join(str(e['size_mb']) for e in entries)))
    
    def update_all_entries_table(self):
        all_entries = self.backend.get_all_entries()

        if self.show_only_duplicates:
            filtered_entries = {code: entries for code, entries in all_entries.items() if len(entries) > 1}
        else:
            filtered_entries = all_entries

        search_text = getattr(self, 'current_search_text', '').strip().lower()
        if search_text:
            search_filtered = {}
            for code, entries in filtered_entries.items():
                if search_text in code.lower():
                    search_filtered[code] = entries
            filtered_entries = search_filtered

        total_occurrences = sum(len(entries) for entries in filtered_entries.values())
        filter_text = f"Showing {total_occurrences} entries"
        if self.show_only_duplicates:
            filter_text += " (duplicates only)"
        if search_text:
            filter_text += f" | Search: '{search_text}'"
        self.ui.filter_status_label.setText(filter_text)

        self.ui.all_entries_table.setRowCount(total_occurrences)

        row = 0
        for code, entries in filtered_entries.items():
            for entry in entries:
                self.ui.all_entries_table.setItem(row, 0, QTableWidgetItem(code))
                self.ui.all_entries_table.setItem(row, 1, QTableWidgetItem(entry['source_file']))
                self.ui.all_entries_table.setItem(row, 2, QTableWidgetItem(entry['filename']))
                self.ui.all_entries_table.setItem(row, 3, QTableWidgetItem(str(entry['size_mb'])))

                if search_text and search_text in code.lower():
                    for col in range(4):
                        self.ui.all_entries_table.item(row, col).setBackground(QColor(200, 220, 255))
                elif not self.show_only_duplicates and len(entries) > 1:
                    for col in range(4):
                        self.ui.all_entries_table.item(row, col).setBackground(QColor(255, 255, 200))

                row += 1

    def on_search_changed(self, text):
        self.current_search_text = text
        self.update_all_entries_table()

    def clear_search(self):
        self.ui.search_input.clear()
        self.current_search_text = ""
        self.update_all_entries_table()

    def reset_all(self):
        reply = QMessageBox.question(self, "Confirm Reset", "Reset all loaded files?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.backend.reset()
            self.show_only_duplicates = False
            self.current_search_text = "" 
            self.ui.show_duplicates_checkbox.setChecked(False)
            self.update_ui()
            self.ui.statusbar.showMessage("Reset complete")
    
    def export_report(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "duplicates_report.txt", "Text Files (*.txt)")
        if file_path:
            try:
                self.backend.export_report(file_path)
                QMessageBox.information(self, "Success", f"Report saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def export_duplicates_csv(self):
        if self.ui.duplicates_table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "There are no duplicates to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "duplicates.csv", "CSV Files (*.csv)"
        )
        if not file_path:
            return
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Code", "Occurrences", "Files", "Filenames", "Sizes (MB)"])
                for row in range(self.ui.duplicates_table.rowCount()):
                    row_data = []
                    for col in range(5):
                        item = self.ui.duplicates_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def export_all_entries_csv(self):
        if self.ui.all_entries_table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "There are no entries to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "all_entries.csv", "CSV Files (*.csv)"
        )
        if not file_path:
            return
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Code", "Source File", "Filename", "Size (MB)"])
                for row in range(self.ui.all_entries_table.rowCount()):
                    row_data = []
                    for col in range(4):
                        item = self.ui.all_entries_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def export_duplicate_entries_csv(self):
        duplicates = self.backend.get_duplicates()
        if not duplicates:
            QMessageBox.warning(self, "No Data", "There are no duplicates to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "duplicate_entries.csv", "CSV Files (*.csv)"
        )
        if not file_path:
            return
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Code", "Source File", "Filename", "Size (MB)"])
                for code, entries in duplicates.items():
                    for entry in entries:
                        writer.writerow([code, entry['source_file'], entry['filename'], entry['size_mb']])
            QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DuplicateFinderUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()