# backend.

import json
import os
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class DuplicateFinderBackend:
    """Backend logic for finding duplicate video codes in JSON files"""
    
    def __init__(self):
        self.all_entries: Dict[str, List[Dict]] = defaultdict(list)
        self.loaded_files: List[str] = []
        self.lock = threading.Lock()  # For thread-safe operations
    
    def load_json_files_parallel(self, file_paths: List[str], max_workers: int = 4) -> Tuple[int, List[str]]:
        """
        Load multiple JSON files in PARALLEL using ThreadPoolExecutor
        Returns: (total_entries, list_of_all_duplicate_codes_found)
        """
        total_entries = 0
        all_new_duplicates = []
        
        def load_single(file_path):
            """Load a single file (runs in parallel)"""
            try:
                entries, new_duplicates = self._load_single_file_threadsafe(file_path)
                return file_path, entries, new_duplicates, None
            except Exception as e:
                return file_path, 0, [], str(e)
        
        # Load files in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(load_single, path): path for path in file_paths}
            
            for future in as_completed(futures):
                file_path, count, duplicates, error = future.result()
                if error:
                    raise Exception(f"Error loading {file_path}: {error}")
                total_entries += count
                all_new_duplicates.extend(duplicates)
        
        return total_entries, list(set(all_new_duplicates))
    
    def _load_single_file_threadsafe(self, file_path: str) -> Tuple[int, List[str]]:
        """Load a single JSON file with thread-safe operations"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        filename = os.path.basename(file_path)
        new_duplicates = []
        
        # Extract video entries
        entries = self._extract_video_entries(data)
        
        # Thread-safe addition to shared dictionaries
        with self.lock:
            for code, info in entries.items():
                if code in self.all_entries:
                    new_duplicates.append(code)
                
                self.all_entries[code].append({
                    'filename': info.get('filename', 'Unknown'),
                    'size_mb': info.get('size_mb', 'Unknown'),
                    'source_file': filename,
                    'full_path': file_path
                })
            
            if file_path not in self.loaded_files:
                self.loaded_files.append(file_path)
        
        return len(entries), list(set(new_duplicates))
    
    def load_json_files(self, file_paths: List[str]) -> Tuple[int, List[str]]:
        """Load multiple JSON files sequentially (original method)"""
        total_entries = 0
        all_new_duplicates = []
        
        for file_path in file_paths:
            try:
                entries, new_duplicates = self._load_single_file(file_path)
                total_entries += entries
                all_new_duplicates.extend(new_duplicates)
            except Exception as e:
                raise Exception(f"Error loading {file_path}: {str(e)}")
        
        return total_entries, list(set(all_new_duplicates))
    
    def _load_single_file(self, file_path: str) -> Tuple[int, List[str]]:
        """Load a single JSON file (sequential version)"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        filename = os.path.basename(file_path)
        new_duplicates = []
        
        # Extract video entries
        entries = self._extract_video_entries(data)
        
        for code, info in entries.items():
            if code in self.all_entries:
                new_duplicates.append(code)
            
            self.all_entries[code].append({
                'filename': info.get('filename', 'Unknown'),
                'size_mb': info.get('size_mb', 'Unknown'),
                'source_file': filename,
                'full_path': file_path
            })
        
        if file_path not in self.loaded_files:
            self.loaded_files.append(file_path)
        
        return len(entries), list(set(new_duplicates))
    
    def _extract_video_entries(self, data: Dict) -> Dict:
        """Extract only video entries from JSON"""
        video_entries = {}
        
        for key, value in data.items():
            if not isinstance(value, dict):
                continue
            
            if '-' in str(key) and any(c.isdigit() for c in str(key)):
                if 'filename' in value or 'size_mb' in value:
                    video_entries[key] = value
        
        return video_entries
    
    def get_duplicates(self) -> Dict[str, List[Dict]]:
        """Get all duplicate codes"""
        return {code: entries for code, entries in self.all_entries.items() 
                if len(entries) > 1}
    
    def get_all_entries(self) -> Dict[str, List[Dict]]:
        """Get all loaded entries"""
        return dict(self.all_entries)
    
    def get_summary(self) -> Dict:
        """Get summary information"""
        duplicates = self.get_duplicates()
        total_duplicate_occurrences = sum(len(entries) for entries in duplicates.values())
        
        return {
            'total_files': len(self.loaded_files),
            'total_unique_codes': len(self.all_entries),
            'duplicate_codes': len(duplicates),
            'total_duplicate_occurrences': total_duplicate_occurrences,
            'loaded_files': self.loaded_files.copy()
        }
    
    def export_report(self, file_path: str) -> None:
        """Export duplicate report to file"""
        duplicates = self.get_duplicates()
        
        if not duplicates:
            raise Exception("No duplicates to export")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("DUPLICATE VIDEO CODES REPORT\n")
            f.write(f"Generated from {len(self.loaded_files)} JSON files\n")
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
        with self.lock:
            self.all_entries.clear()
            self.loaded_files.clear()