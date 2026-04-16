# frontend.py

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem,
    QLabel, QFileDialog, QMessageBox, QTabWidget, QHeaderView,
    QStatusBar, QProgressBar, QCheckBox, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor, QAction
from application.backend import DuplicateFinderBackend
from application.file_viewer import FileViewerDialog


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
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("JSON Duplicate Finder - Video Code Scanner")
        self.setGeometry(100, 100, 1400, 800)
        
        self.showMaximized() # Maximized window, not full screen
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Top bar with buttons
        top_frame = QWidget()
        top_layout = QHBoxLayout(top_frame)
        
        self.load_btn = QPushButton("📂 Load JSON Files (Select Multiple)")
        self.load_btn.clicked.connect(self.load_files)
        self.load_btn.setMinimumHeight(40)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        
        self.reset_btn = QPushButton("🗑️ Reset All")
        self.reset_btn.clicked.connect(self.reset_all)
        self.reset_btn.setMinimumHeight(40)
        
        self.export_btn = QPushButton("💾 Export Report")
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setMinimumHeight(40)
        
        top_layout.addWidget(self.load_btn)
        top_layout.addWidget(self.reset_btn)
        top_layout.addWidget(self.export_btn)
        top_layout.addStretch()
        
        # Info panel
        self.info_label = QLabel("Ready to scan JSON files")
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        files_tab = self.create_files_tab()
        duplicates_tab = self.create_duplicates_tab()
        all_entries_tab = self.create_all_entries_tab()
        
        self.tab_widget.addTab(files_tab, "📁 Loaded Files")
        self.tab_widget.addTab(duplicates_tab, "⚠️ Duplicates")
        self.tab_widget.addTab(all_entries_tab, "📋 All Entries")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add all to main layout
        main_layout.addWidget(top_frame)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.progress_bar)
        
        # Apply styling
        self.apply_styles()
        
        # Update UI
        self.update_ui()
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # ========== FILE MENU ==========
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
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # ========== HELP MENU ==========
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
    
    def show_about(self):
        """Show About Us dialog"""
        dialog = FileViewerDialog(
            title="About JSON Duplicate Finder",
            file_names=["aboutus.md", "ABOUTUS.md", "about.md", "ABOUT.md"],
            is_markdown=True,
            size=(700, 600)
        )
        dialog.exec()
    
    def show_readme(self):
        """Show Readme dialog"""
        dialog = FileViewerDialog(
            title="Readme - JSON Duplicate Finder",
            file_names=["README.md", "readme.md", "Readme.md"],
            is_markdown=True,
            size=(800, 600)
        )
        dialog.exec()
    
    def show_license(self):
        """Show License dialog"""
        dialog = FileViewerDialog(
            title="License - MIT License",
            file_names=["LICENSE.md", "license.md", "LICENSE"],
            is_markdown=True,
            size=(700, 550)
        )
        dialog.exec()
    
    def create_files_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("📁 Loaded JSON Files:")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.files_list = QListWidget()
        layout.addWidget(label)
        layout.addWidget(self.files_list)
        return widget
    
    def create_duplicates_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header with button
        header = QHBoxLayout()
        label = QLabel("⚠️ Duplicate Codes Found:")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self.export_duplicates_csv)
        
        header.addWidget(label)
        header.addStretch()
        header.addWidget(export_btn)
        
        self.duplicates_table = QTableWidget()
        self.duplicates_table.setColumnCount(5)
        self.duplicates_table.setHorizontalHeaderLabels(
            ["Code", "Occurrences", "Files", "Filenames", "Sizes (MB)"]
        )
        self.duplicates_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.duplicates_table.setAlternatingRowColors(True)
        
        layout.addLayout(header)
        layout.addWidget(self.duplicates_table)
        
        return widget
    
    def create_all_entries_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header with buttons
        header = QHBoxLayout()
        label = QLabel("📋 All Loaded Entries:")
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        export_all_btn = QPushButton("Export All CSV")
        export_all_btn.clicked.connect(self.export_all_entries_csv)
        
        export_dupes_btn = QPushButton("Export Duplicates CSV")
        export_dupes_btn.clicked.connect(self.export_duplicate_entries_csv)
        
        header.addWidget(label)
        header.addStretch()
        header.addWidget(export_all_btn)
        header.addWidget(export_dupes_btn)
        
        # Checkbox
        filter_layout = QHBoxLayout()
        self.show_duplicates_checkbox = QCheckBox("🔍 Show only duplicate entries")
        self.show_duplicates_checkbox.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.show_duplicates_checkbox)
        filter_layout.addStretch()
        
        self.all_entries_table = QTableWidget()
        self.all_entries_table.setColumnCount(4)
        self.all_entries_table.setHorizontalHeaderLabels(
            ["Code", "Source File", "Filename", "Size (MB)"]
        )
        self.all_entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.all_entries_table.setAlternatingRowColors(True)
        
        self.filter_status_label = QLabel("")
        self.filter_status_label.setStyleSheet("QLabel { color: #7f8c8d; font-style: italic; }")
        
        layout.addLayout(header)
        layout.addLayout(filter_layout)
        layout.addWidget(self.all_entries_table)
        layout.addWidget(self.filter_status_label)
        
        return widget
    
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
    
    def on_filter_changed(self, checked):
        """Handle checkbox toggle"""
        self.show_only_duplicates = checked  # checked is True or False
        self.update_all_entries_table()
    
    def load_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select JSON Files", "", "JSON Files (*.json);;All Files (*.*)"
        )
        if not file_paths:
            return
        
        self.load_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_bar.showMessage(f"Loading {len(file_paths)} file(s)...")
        
        self.worker = LoadWorker(self.backend, file_paths)
        self.worker.finished.connect(self.on_files_loaded)
        self.worker.error.connect(self.on_load_error)
        self.worker.start()
    
    def on_files_loaded(self, count, duplicates):
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        if count > 0:
            msg = f"✅ Loaded {count} entries from {len(self.backend.loaded_files)} file(s)"
            if duplicates:
                msg += f" (⚠️ Found {len(duplicates)} new duplicates)"
            self.status_bar.showMessage(msg)
            self.update_ui()
            if duplicates:
                QMessageBox.information(self, "Duplicates Found", 
                    f"Found {len(duplicates)} duplicate code(s)! Check the 'Duplicates' tab.")
        else:
            self.status_bar.showMessage("⚠️ No valid entries found")
    
    def on_load_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.load_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", error_msg)
    
    def update_ui(self):
        self.files_list.clear()
        for file_path in self.backend.loaded_files:
            self.files_list.addItem(file_path)
        
        self.update_duplicates_table()
        self.update_all_entries_table()
        
        summary = self.backend.get_summary()
        self.info_label.setText(
            f"📊 Summary: {summary['total_files']} file(s) | "
            f"{summary['total_unique_codes']} unique codes | "
            f"{summary['duplicate_codes']} duplicates ({summary['total_duplicate_occurrences']} occurrences)"
        )
        self.export_btn.setEnabled(summary['duplicate_codes'] > 0)
    
    def update_duplicates_table(self):
        duplicates = self.backend.get_duplicates()
        self.duplicates_table.setRowCount(len(duplicates))
        
        for row, (code, entries) in enumerate(duplicates.items()):
            self.duplicates_table.setItem(row, 0, QTableWidgetItem(code))
            self.duplicates_table.setItem(row, 1, QTableWidgetItem(str(len(entries))))
            self.duplicates_table.setItem(row, 2, QTableWidgetItem(', '.join(set(e['source_file'] for e in entries))))
            self.duplicates_table.setItem(row, 3, QTableWidgetItem('\n'.join(e['filename'][:50] for e in entries)))
            self.duplicates_table.setItem(row, 4, QTableWidgetItem(', '.join(str(e['size_mb']) for e in entries)))
    
    def update_all_entries_table(self):
        """Update the all entries table with filter support"""
        all_entries = self.backend.get_all_entries()

        # Filter if checkbox is checked
        if self.show_only_duplicates:
            # Only show entries that are duplicates (appear more than once)
            filtered_entries = {}
            for code, entries in all_entries.items():
                if len(entries) > 1:  # This is a duplicate
                    filtered_entries[code] = entries
            filter_text = f"Showing only duplicate entries ({sum(len(entries) for entries in filtered_entries.values())} total occurrences)"
        else:
            filtered_entries = all_entries
            filter_text = f"Showing all entries ({sum(len(entries) for entries in filtered_entries.values())} total occurrences)"

        # Update filter status label
        self.filter_status_label.setText(filter_text)

        # Count total entries for the filtered data
        total_occurrences = sum(len(entries) for entries in filtered_entries.values())

        # Clear and repopulate table
        self.all_entries_table.setRowCount(total_occurrences)

        row = 0
        for code, entries in filtered_entries.items():
            for entry in entries:
                # Code
                self.all_entries_table.setItem(row, 0, QTableWidgetItem(code))
                # Source File
                self.all_entries_table.setItem(row, 1, QTableWidgetItem(entry['source_file']))
                # Filename
                self.all_entries_table.setItem(row, 2, QTableWidgetItem(entry['filename']))
                # Size
                self.all_entries_table.setItem(row, 3, QTableWidgetItem(str(entry['size_mb'])))

                # Highlight duplicates in yellow (only when showing all entries)
                if not self.show_only_duplicates and len(entries) > 1:
                    for col in range(4):
                        self.all_entries_table.item(row, col).setBackground(QColor(255, 255, 200))

                row += 1

    def reset_all(self):
        reply = QMessageBox.question(self, "Confirm Reset", "Reset all loaded files?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.backend.reset()
            self.show_only_duplicates = False
            self.show_duplicates_checkbox.setChecked(False)
            self.update_ui()
            self.status_bar.showMessage("Reset complete")
    
    def export_report(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "duplicates_report.txt", "Text Files (*.txt)")
        if file_path:
            try:
                self.backend.export_report(file_path)
                QMessageBox.information(self, "Success", f"Report saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def export_duplicates_csv(self):
        """Export duplicates table to CSV"""
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
                for row in range(self.duplicates_table.rowCount()):
                    row_data = []
                    for col in range(5):
                        item = self.duplicates_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def export_all_entries_csv(self):
        """Export all entries (current view) to CSV"""
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
                for row in range(self.all_entries_table.rowCount()):
                    row_data = []
                    for col in range(4):
                        item = self.all_entries_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def export_duplicate_entries_csv(self):
        """Export only duplicate entries from backend"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "duplicate_entries.csv", "CSV Files (*.csv)"
        )
        if not file_path:
            return
        try:
            import csv
            duplicates = self.backend.get_duplicates()
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
    window = DuplicateFinderUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()