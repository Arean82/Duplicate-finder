# backend.py

import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Tuple
import threading
import sqlite3

class DuplicateFinderBackend:
    """Backend logic for finding duplicate video codes using sqlite3"""
    
    def __init__(self):
        # We will use a local SQLite file
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "duplicates.db")
        self.lock = threading.Lock()
        self.key_pattern = r'.*?-.*\d.*'  # Default pattern: contains a dash and a digit
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def set_key_pattern(self, pattern: str):
        """Update the regex pattern used to identify valid video codes"""
        self.key_pattern = pattern
        
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS entries (
                    code TEXT,
                    filename TEXT,
                    size_mb REAL,
                    source_file TEXT,
                    full_path TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS loaded_files (
                    full_path TEXT PRIMARY KEY
                )
            ''')

    def get_loaded_files(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT full_path FROM loaded_files")
            return [str(row[0]) for row in cursor.fetchall()]

    @property
    def loaded_files(self):
        return self.get_loaded_files()

    def load_json_files(self, file_paths: List[str]) -> Tuple[int, List[str]]:
        """Load multiple JSON files sequentially"""
        total_entries = 0
        all_new_duplicates = []
        
        # Get already loaded files
        loaded = self.get_loaded_files()
        file_paths = [p for p in file_paths if p not in loaded]
        
        if not file_paths:
            return 0, []
            
        with self._get_connection() as conn:
            for file_path in file_paths:
                entries, new_duplicates = self._load_single_file(conn, file_path)
                total_entries += entries
                all_new_duplicates.extend(new_duplicates)
            
        return total_entries, list(set(all_new_duplicates))

    def load_json_files_parallel(self, file_paths: List[str], max_workers: int = 4) -> Tuple[int, List[str]]:
        # Map to sequential to avoid concurrent SQLite write locks
        return self.load_json_files(file_paths)

    def _load_single_file(self, conn: sqlite3.Connection, file_path: str) -> Tuple[int, List[str]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON format in {os.path.basename(file_path)}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error reading {os.path.basename(file_path)}: {str(e)}")
            
        filename = os.path.basename(file_path)
        new_duplicates = []
        entries = self._extract_video_entries(data)
        
        # Check existing codes to find new duplicates
        if entries:
            codes = list(entries.keys())
            batch_size = 900
            existing_codes = set()
            cursor = conn.cursor()
            for i in range(0, len(codes), batch_size):
                batch_codes = codes[i:i+batch_size]
                placeholders = ", ".join(["?"] * len(batch_codes))
                cursor.execute(f"SELECT DISTINCT code FROM entries WHERE code IN ({placeholders})", batch_codes)
                existing_codes.update(str(row[0]) for row in cursor.fetchall())
                
            for code in entries:
                if code in existing_codes:
                    new_duplicates.append(code)
                    
        # Insert entries in batch
        insert_rows = [
            (
                code,
                str(info.get('filename', 'Unknown')),
                float(info.get('size_mb', 0.0) if info.get('size_mb') else 0.0),
                filename,
                file_path
            )
            for code, info in entries.items()
        ]
        
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO entries (code, filename, size_mb, source_file, full_path) VALUES (?, ?, ?, ?, ?)",
            insert_rows
        )
        cursor.execute("INSERT INTO loaded_files (full_path) VALUES (?)", (file_path,))
        return len(entries), new_duplicates

    def _extract_video_entries(self, data: Dict) -> Dict:
        """Extract only video entries from JSON using regex pattern"""
        video_entries = {}
        for key, value in data.items():
            if not isinstance(value, dict):
                continue
            
            try:
                if re.match(self.key_pattern, str(key)):
                    if 'filename' in value or 'size_mb' in value:
                        video_entries[key] = value
            except re.error:
                pass
                
        return video_entries

    def get_duplicates(self) -> Dict[str, List[Dict]]:
        """Get all duplicate codes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT code FROM entries 
                GROUP BY code HAVING COUNT(*) > 1
            """)
            duplicate_codes = [str(row[0]) for row in cursor.fetchall()]
            
            if not duplicate_codes:
                return {}
                
            duplicates = defaultdict(list)
            batch_size = 900
            for i in range(0, len(duplicate_codes), batch_size):
                batch_codes = duplicate_codes[i:i+batch_size]
                placeholders = ", ".join(["?"] * len(batch_codes))
                cursor.execute(f"""
                    SELECT code, filename, size_mb, source_file, full_path 
                    FROM entries WHERE code IN ({placeholders})
                """, batch_codes)
                
                for row in cursor.fetchall():
                    duplicates[str(row[0])].append({
                        'filename': str(row[1]),
                        'size_mb': row[2],
                        'source_file': str(row[3]),
                        'full_path': str(row[4])
                    })
                
            return dict(duplicates)

    def get_all_entries(self) -> Dict[str, List[Dict]]:
        """Get all loaded entries"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT code, filename, size_mb, source_file, full_path FROM entries")
            entries = defaultdict(list)
            for row in cursor.fetchall():
                entries[str(row[0])].append({
                    'filename': str(row[1]),
                    'size_mb': row[2],
                    'source_file': str(row[3]),
                    'full_path': str(row[4])
                })
            return dict(entries)

    def unload_file(self, file_path: str):
        """Unload a specific file from the database"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM entries WHERE full_path = ?", (file_path,))
            conn.execute("DELETE FROM loaded_files WHERE full_path = ?", (file_path,))

    def get_summary(self) -> Dict:
        """Get summary information"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM loaded_files")
            total_files = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT code) FROM entries")
            total_unique = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM (SELECT code FROM entries GROUP BY code HAVING COUNT(*) > 1)")
            duplicate_codes = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT SUM(cnt) FROM (
                    SELECT COUNT(*) as cnt FROM entries GROUP BY code HAVING COUNT(*) > 1
                )
            """)
            row = cursor.fetchone()
            total_duplicate_occurrences = row[0] if row and row[0] is not None else 0
            
            files_list = self.get_loaded_files()
            
            return {
                'total_files': total_files,
                'total_unique_codes': total_unique,
                'duplicate_codes': duplicate_codes,
                'total_duplicate_occurrences': total_duplicate_occurrences,
                'loaded_files': files_list
            }

    def export_report(self, file_path: str) -> None:
        """Export duplicate report to file"""
        duplicates = self.get_duplicates()
        loaded_files = self.get_loaded_files()
        
        if not duplicates:
            raise Exception("No duplicates to export")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("DUPLICATE VIDEO CODES REPORT\n")
            f.write(f"Generated from {len(loaded_files)} JSON files\n")
            f.write("="*80 + "\n\n")
            
            for code, entries in duplicates.items():
                f.write(f"CODE: {code}\n")
                f.write(f"Found in {len(entries)} files:\n")
                for i, entry in enumerate(entries, 1):
                    f.write(f"\n  [{i}] Source: {entry['source_file']}\n")
                    f.write(f"      Filename: {entry['filename']}\n")
                    f.write(f"      Size: {entry['size_mb']} MB\n")
                f.write("\n" + "-"*80 + "\n")
    
    def reset(self) -> None:
        """Reset all loaded data"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM entries")
            conn.execute("DELETE FROM loaded_files")