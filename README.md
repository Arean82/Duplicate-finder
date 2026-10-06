# JSON Duplicate Finder 🔍

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Arean82/json-duplicate-finder)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-yellow.svg)](https://www.python.org/)

## 📖 Overview

**JSON Duplicate Finder** is a desktop application that helps you find duplicate video codes across multiple JSON files. Perfect for managing large video collections and identifying redundant entries.

## ✨ Features

- 🚀 Load multiple JSON files at once
- 🔍 Automatically detect duplicate video codes (format: XXX-123)
- 📊 Clean, modern UI with tabbed views
- 🎯 Filter to show only duplicates
- 💾 Export duplicate reports to text files
- ⌨️ Keyboard shortcuts for quick access
- ⚡ Background threading and parallel processing - UI never freezes

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Steps

```bash
# 1. Clone or download the repository
git clone https://github.com/Arean82/json-duplicate-finder.git
cd json-duplicate-finder

# 2. Install required dependencies
pip install PySide6 markdown

# 3. Run the application
python run.py
```

### Alternative (using requirements.txt)

```bash
pip install -r requirements.txt
python run.py
```

## 📁 File Structure

```
json-duplicate-finder/
│
├── run.py                  # Entry point (run this file)
├── requirements.txt        # Python dependencies (PySide6, markdown)
├── ABOUTUS.md              # About Us content (Help menu)
├── README.md               # This documentation file
├── LICENSE                 # MIT License file
├── build.py                # PyInstaller build script
├── duplicates.db           # SQLite database for caching entries
│
├── application/            # Main application package
│   ├── __init__.py         # Makes it a Python package
│   ├── backend.py          # Business logic, SQLite storage & duplicate detection
│   └── ui_files/           # UI presentation layer
│       ├── frontend.py     # Main window, menus, tables & worker thread
│       └── file_viewer.py  # Markdown viewer dialog
│
└── resources/              # Created automatically
    ├── badges/             # Place your badge images here
    └── badge_cache/        # Downloaded badge images cache
```

## 🚀 Quick Start Guide

1. **Launch the application**
   ```bash
   python run.py
   ```

2. **Load JSON files**
   - Click "Load JSON Files" button or press `Ctrl+O`
   - Select one or multiple JSON files from any folder

3. **View results**
   - **Loaded Files tab** - See all files you've loaded
   - **Duplicates tab** - View all duplicate codes found
   - **All Entries tab** - Browse all entries with filter option

4. **Export report**
   - Click "Export Report" or press `Ctrl+E`
   - Save duplicates to a text file

## 📋 JSON Format Expected

Your JSON files should follow this structure:

```json
{
    "ABC-123": {
        "filename": "video_title.mp4",
        "size_mb": 1024.50
    },
    "DEF-456": {
        "filename": "another_video.mp4",
        "size_mb": 2048.75
    }
}
```

**Requirements:**
- Keys must contain a dash `-` and numbers (e.g., `ABC-123`)
- Each entry must have `filename` or `size_mb` field

## 🎯 Use Cases

- **Media Library Management** - Find duplicate video entries across backup files
- **Data Cleanup** - Identify redundant records in JSON databases
- **Quality Assurance** - Verify no duplicate codes exist in production data
- **Archive Organization** - Consolidate multiple JSON exports

## ⌨️ Keyboard Shortcuts

| **Shortcut** | **Action** |
|----------|--------|
| `Ctrl+O` | Load JSON files |
| `Ctrl+R` | Reset all loaded data |
| `Ctrl+E` | Export duplicate report |
| `Ctrl+Q` | Exit application |
| `F1` | Show About Us |
| `F2` | Show Readme |
| `F3` | Show License |

## 🛠️ Troubleshooting

### Common Issues and Solutions

**Q: No video entries found in my JSON file**
- Ensure your JSON keys follow the format `XXX-123` (contains a dash and numbers)
- Check that each entry has `filename` or `size_mb` fields
- Example valid key: `"ACHJ-038"`

**Q: ImportError: No module named 'application'**
- Make sure you have an empty `__init__.py` file in the `application/` folder
- This file makes Python recognize the folder as a package

**Q: Application appears frozen when loading large files**
- The application uses background threading - it's still working
- Check the progress bar for loading status
- For very large files (>100MB), wait a few seconds

**Q: Badge images not loading in About dialog**
- Images load in background - they will appear shortly
- Place badge images in `resources/badges/` folder for offline use
- Images are cached locally after first download

**Q: "Module not found" error when running**
- Install missing dependencies: `pip install PySide6 markdown`
- Make sure you're using Python 3.7 or higher

## 📝 Menu Bar Options

### File Menu
- **Load JSON Files** (`Ctrl+O`) - Open file dialog to select JSON files
- **Reset All** (`Ctrl+R`) - Clear all loaded data and start over
- **Export Report** (`Ctrl+E`) - Save duplicate report to text file
- **Exit** (`Ctrl+Q`) - Close the application

### Help Menu
- **About Us** (`F1`) - Show application information
- **Readme** (`F2`) - Show this documentation
- **License** (`F3`) - Show MIT License details

## 🏗️ Building Executable

To create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Run the build script
python build.py
```

The executable will be created in the `dist/` folder.

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [PySide6](https://www.qt.io/qt-for-python) (Qt for Python)
- Local embedded database powered by Python's built-in `sqlite3` (WAL mode)
- Markdown rendered with Python-Markdown
- Icons from Unicode emojis
- Inspired by data deduplication needs

---

**Made with ❤️ by Arean Narrayan**

**Version 1.0.0** | **Last Updated: 2026**

