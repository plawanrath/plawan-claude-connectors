# @plawanrath

#!/usr/bin/env python
import os, sys, asyncio, shutil, hashlib, zipfile, datetime, json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool

# Optional Pillow import for EXIF functionality
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("[FilesystemConnector] Pillow not available - EXIF features disabled", file=sys.stderr)                      

# Helper for Claude Desktop logs
def log(msg: str):
    print(f"[FilesystemConnector] {msg}", file=sys.stderr)

mcp = FastMCP("filesystem-connector")

# Global settings
DRY_RUN_MODE = False
OPERATION_LOG = []

def log_operation(operation: str, details: Dict):
    """Log all file operations for safety and debugging"""
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "operation": operation,
        "details": details
    }
    OPERATION_LOG.append(log_entry)
    log(f"Operation: {operation} - {details}")

def safe_path(path: str) -> Path:
    """Convert string path to Path object and resolve it safely"""
    return Path(path).resolve()

# ---------- Tools -----------------------------------------------------------
@mcp.tool(name="list_directory", description="Lists files / sub‑dirs in a directory")
async def list_directory(path: str = ".") -> dict:
    log(f"list_directory({path})")
    if not os.path.isdir(path):
        return {"error": f"'{path}' is not a directory"}
    return {"directory": path, "contents": os.listdir(path)}


@mcp.tool(name="read_files", description="Read up to 8 kB from a file")
async def read_file(path: str) -> dict:
    log(f"read_file({path})")
    if not os.path.isfile(path):
        return {"error": f"File '{path}' not found"}
    with open(path, "r", encoding="utf‑8", errors="ignore") as f:
        return {"file_path": path, "content": f.read(8000)}


@mcp.tool(name="search_files", description="Find files whose *names* contain a keyword (recursive)")
async def search_files(start_path: str = ".", keyword: str = "") -> dict:
    log(f"search_files({start_path}, {keyword})")
    if not os.path.isdir(start_path):
        return {"error": f"'{start_path}' is not a directory"}
    matches = [
        os.path.join(root, f)
        for root, _, files in os.walk(start_path)
        for f in files
        if keyword.lower() in f.lower()
    ]
    return {"start_path": start_path, "keyword": keyword, "matches": matches}


# ---------- Foundational Write Operations ----------------------------------

@mcp.tool(name="set_dry_run_mode", description="Enable/disable dry run mode for safety")
async def set_dry_run_mode(enabled: bool = True) -> dict:
    global DRY_RUN_MODE
    DRY_RUN_MODE = enabled
    log(f"Dry run mode: {'ENABLED' if enabled else 'DISABLED'}")
    return {"dry_run_mode": enabled, "message": f"Dry run mode {'enabled' if enabled else 'disabled'}"}

@mcp.tool(name="move_file", description="Move or rename a file/directory")
async def move_file(source: str, destination: str, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source)
        dest_path = safe_path(destination)
        
        if not src_path.exists():
            return {"error": f"Source '{source}' does not exist"}
        
        if dest_path.exists():
            return {"error": f"Destination '{destination}' already exists"}
        
        # Create parent directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if dry_run:
            log_operation("move_file_dry_run", {"source": str(src_path), "destination": str(dest_path)})
            return {"dry_run": True, "would_move": str(src_path), "to": str(dest_path)}
        
        shutil.move(str(src_path), str(dest_path))
        log_operation("move_file", {"source": str(src_path), "destination": str(dest_path)})
        return {"moved": str(src_path), "to": str(dest_path)}
        
    except Exception as e:
        return {"error": f"Failed to move file: {str(e)}"}

@mcp.tool(name="create_directory", description="Create a new directory (with parent directories if needed)")
async def create_directory(path: str, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        dir_path = safe_path(path)
        
        if dir_path.exists():
            return {"error": f"Directory '{path}' already exists"}
        
        if dry_run:
            log_operation("create_directory_dry_run", {"path": str(dir_path)})
            return {"dry_run": True, "would_create": str(dir_path)}
        
        dir_path.mkdir(parents=True, exist_ok=True)
        log_operation("create_directory", {"path": str(dir_path)})
        return {"created": str(dir_path)}
        
    except Exception as e:
        return {"error": f"Failed to create directory: {str(e)}"}

@mcp.tool(name="delete_file", description="Delete a file or move it to trash (safer)")
async def delete_file(path: str, move_to_trash: bool = True, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        file_path = safe_path(path)
        
        if not file_path.exists():
            return {"error": f"File '{path}' does not exist"}
        
        if dry_run:
            action = "move_to_trash" if move_to_trash else "permanent_delete"
            log_operation(f"{action}_dry_run", {"path": str(file_path)})
            return {"dry_run": True, "would_delete": str(file_path), "method": action}
        
        if move_to_trash:
            # Move to a .trash folder in the same directory
            trash_dir = file_path.parent / ".trash"
            trash_dir.mkdir(exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            trash_path = trash_dir / f"{file_path.name}.{timestamp}"
            shutil.move(str(file_path), str(trash_path))
            log_operation("move_to_trash", {"original": str(file_path), "trash_location": str(trash_path)})
            return {"moved_to_trash": str(trash_path)}
        else:
            if file_path.is_dir():
                shutil.rmtree(str(file_path))
            else:
                file_path.unlink()
            log_operation("permanent_delete", {"path": str(file_path)})
            return {"permanently_deleted": str(file_path)}
        
    except Exception as e:
        return {"error": f"Failed to delete file: {str(e)}"}

@mcp.tool(name="copy_file", description="Copy a file or directory")
async def copy_file(source: str, destination: str, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source)
        dest_path = safe_path(destination)
        
        if not src_path.exists():
            return {"error": f"Source '{source}' does not exist"}
        
        if dest_path.exists():
            return {"error": f"Destination '{destination}' already exists"}
        
        # Create parent directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if dry_run:
            log_operation("copy_file_dry_run", {"source": str(src_path), "destination": str(dest_path)})
            return {"dry_run": True, "would_copy": str(src_path), "to": str(dest_path)}
        
        if src_path.is_dir():
            shutil.copytree(str(src_path), str(dest_path))
        else:
            shutil.copy2(str(src_path), str(dest_path))
        
        log_operation("copy_file", {"source": str(src_path), "destination": str(dest_path)})
        return {"copied": str(src_path), "to": str(dest_path)}
        
    except Exception as e:
        return {"error": f"Failed to copy file: {str(e)}"}


# ---------- Rule-Based Sorting Functions -----------------------------------

@mcp.tool(name="sort_by_file_type", description="Sort files by their extensions into subdirectories")
async def sort_by_file_type(source_dir: str, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source_dir)
        if not src_path.is_dir():
            return {"error": f"'{source_dir}' is not a directory"}
        
        file_types = {}
        operations = []
        
        for file_path in src_path.rglob("*"):
            if file_path.is_file():
                extension = file_path.suffix.lower() or "no_extension"
                if extension not in file_types:
                    file_types[extension] = []
                file_types[extension].append(file_path)
        
        for ext, files in file_types.items():
            type_dir = src_path / f"{ext.replace('.', '')}_files"
            
            for file_path in files:
                dest_path = type_dir / file_path.name
                operations.append({
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "type": ext
                })
        
        if dry_run:
            log_operation("sort_by_file_type_dry_run", {"source_dir": str(src_path), "operations": len(operations)})
            return {"dry_run": True, "planned_operations": operations, "total_files": len(operations)}
        
        moved_count = 0
        for op in operations:
            dest_path = Path(op["destination"])
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(op["source"], str(dest_path))
            moved_count += 1
        
        log_operation("sort_by_file_type", {"source_dir": str(src_path), "files_moved": moved_count})
        return {"sorted": moved_count, "file_types": list(file_types.keys())}
        
    except Exception as e:
        return {"error": f"Failed to sort by file type: {str(e)}"}

@mcp.tool(name="sort_by_date", description="Sort files by creation/modification date into year/month folders")
async def sort_by_date(source_dir: str, use_creation_date: bool = False, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source_dir)
        if not src_path.is_dir():
            return {"error": f"'{source_dir}' is not a directory"}
        
        operations = []
        
        for file_path in src_path.rglob("*"):
            if file_path.is_file():
                if use_creation_date:
                    timestamp = file_path.stat().st_ctime
                else:
                    timestamp = file_path.stat().st_mtime
                
                date_obj = datetime.datetime.fromtimestamp(timestamp)
                year_month = date_obj.strftime("%Y-%m")
                
                dest_dir = src_path / year_month
                dest_path = dest_dir / file_path.name
                
                operations.append({
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "date": year_month
                })
        
        if dry_run:
            log_operation("sort_by_date_dry_run", {"source_dir": str(src_path), "operations": len(operations)})
            return {"dry_run": True, "planned_operations": operations, "total_files": len(operations)}
        
        moved_count = 0
        for op in operations:
            dest_path = Path(op["destination"])
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(op["source"], str(dest_path))
            moved_count += 1
        
        log_operation("sort_by_date", {"source_dir": str(src_path), "files_moved": moved_count})
        return {"sorted": moved_count, "date_folders_created": len(set(op["date"] for op in operations))}
        
    except Exception as e:
        return {"error": f"Failed to sort by date: {str(e)}"}

@mcp.tool(name="sort_by_size", description="Sort files by size into small/medium/large folders")
async def sort_by_size(source_dir: str, small_mb: float = 10, large_mb: float = 100, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source_dir)
        if not src_path.is_dir():
            return {"error": f"'{source_dir}' is not a directory"}
        
        operations = []
        size_categories = {"small": [], "medium": [], "large": []}
        
        for file_path in src_path.rglob("*"):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                
                if size_mb < small_mb:
                    category = "small"
                elif size_mb < large_mb:
                    category = "medium"
                else:
                    category = "large"
                
                dest_dir = src_path / f"{category}_files"
                dest_path = dest_dir / file_path.name
                
                operations.append({
                    "source": str(file_path),
                    "destination": str(dest_path),
                    "category": category,
                    "size_mb": round(size_mb, 2)
                })
                size_categories[category].append(file_path)
        
        if dry_run:
            log_operation("sort_by_size_dry_run", {"source_dir": str(src_path), "operations": len(operations)})
            return {"dry_run": True, "planned_operations": operations, "total_files": len(operations)}
        
        moved_count = 0
        for op in operations:
            dest_path = Path(op["destination"])
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(op["source"], str(dest_path))
            moved_count += 1
        
        log_operation("sort_by_size", {"source_dir": str(src_path), "files_moved": moved_count})
        return {
            "sorted": moved_count,
            "small_files": len(size_categories["small"]),
            "medium_files": len(size_categories["medium"]),
            "large_files": len(size_categories["large"])
        }
        
    except Exception as e:
        return {"error": f"Failed to sort by size: {str(e)}"}

@mcp.tool(name="sort_by_pattern", description="Sort files matching specific patterns into folders")
async def sort_by_pattern(source_dir: str, patterns: Dict[str, str], dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        import re
        src_path = safe_path(source_dir)
        if not src_path.is_dir():
            return {"error": f"'{source_dir}' is not a directory"}
        
        operations = []
        
        for file_path in src_path.rglob("*"):
            if file_path.is_file():
                for folder_name, pattern in patterns.items():
                    if re.search(pattern, file_path.name, re.IGNORECASE):
                        dest_dir = src_path / folder_name
                        dest_path = dest_dir / file_path.name
                        
                        operations.append({
                            "source": str(file_path),
                            "destination": str(dest_path),
                            "pattern": pattern,
                            "folder": folder_name
                        })
                        break
        
        if dry_run:
            log_operation("sort_by_pattern_dry_run", {"source_dir": str(src_path), "operations": len(operations)})
            return {"dry_run": True, "planned_operations": operations, "total_files": len(operations)}
        
        moved_count = 0
        for op in operations:
            dest_path = Path(op["destination"])
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(op["source"], str(dest_path))
            moved_count += 1
        
        log_operation("sort_by_pattern", {"source_dir": str(src_path), "files_moved": moved_count})
        return {"sorted": moved_count, "patterns_used": list(patterns.keys())}
        
    except Exception as e:
        return {"error": f"Failed to sort by pattern: {str(e)}"}


# ---------- Content-Aware Organization -------------------------------------

@mcp.tool(name="search_and_organize_by_content", description="Search files for keywords and organize them")
async def search_and_organize_by_content(source_dir: str, keyword_folders: Dict[str, List[str]], dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source_dir)
        if not src_path.is_dir():
            return {"error": f"'{source_dir}' is not a directory"}
        
        operations = []
        
        for file_path in src_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.pdf', '.doc', '.docx', '.md']:
                try:
                    if file_path.suffix.lower() == '.pdf':
                        continue  # Skip PDF for now - would need PyPDF2
                    
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                    
                    for folder_name, keywords in keyword_folders.items():
                        if any(keyword.lower() in content for keyword in keywords):
                            dest_dir = src_path / folder_name
                            dest_path = dest_dir / file_path.name
                            
                            operations.append({
                                "source": str(file_path),
                                "destination": str(dest_path),
                                "folder": folder_name,
                                "matched_keywords": [kw for kw in keywords if kw.lower() in content]
                            })
                            break
                except Exception:
                    continue
        
        if dry_run:
            log_operation("search_and_organize_by_content_dry_run", {"source_dir": str(src_path), "operations": len(operations)})
            return {"dry_run": True, "planned_operations": operations, "total_files": len(operations)}
        
        moved_count = 0
        for op in operations:
            dest_path = Path(op["destination"])
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(op["source"], str(dest_path))
            moved_count += 1
        
        log_operation("search_and_organize_by_content", {"source_dir": str(src_path), "files_moved": moved_count})
        return {"sorted": moved_count, "folders_used": list(keyword_folders.keys())}
        
    except Exception as e:
        return {"error": f"Failed to organize by content: {str(e)}"}

@mcp.tool(name="organize_photos_by_exif", description="Organize photos by camera model or date from EXIF data")
async def organize_photos_by_exif(source_dir: str, organize_by: str = "date", dry_run: bool = None) -> dict:
    if not PILLOW_AVAILABLE:
        return {"error": "Pillow library not available. Install with: pip install Pillow"}
    
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source_dir)
        if not src_path.is_dir():
            return {"error": f"'{source_dir}' is not a directory"}
        
        operations = []
        image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        
        for file_path in src_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                try:
                    with Image.open(file_path) as img:
                        exif_data = img._getexif()
                        if exif_data:
                            if organize_by == "camera" and 272 in exif_data:  # Camera model
                                camera_model = exif_data[272].replace(" ", "_")
                                dest_dir = src_path / f"Camera_{camera_model}"
                            elif organize_by == "date" and 306 in exif_data:  # DateTime
                                date_str = exif_data[306][:7].replace(":", "-")  # YYYY:MM -> YYYY-MM
                                dest_dir = src_path / date_str
                            else:
                                dest_dir = src_path / "Unknown_EXIF"
                            
                            dest_path = dest_dir / file_path.name
                            operations.append({
                                "source": str(file_path),
                                "destination": str(dest_path),
                                "exif_value": exif_data.get(272 if organize_by == "camera" else 306, "Unknown")
                            })
                except Exception:
                    continue
        
        if dry_run:
            log_operation("organize_photos_by_exif_dry_run", {"source_dir": str(src_path), "operations": len(operations)})
            return {"dry_run": True, "planned_operations": operations, "total_files": len(operations)}
        
        moved_count = 0
        for op in operations:
            dest_path = Path(op["destination"])
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(op["source"], str(dest_path))
            moved_count += 1
        
        log_operation("organize_photos_by_exif", {"source_dir": str(src_path), "files_moved": moved_count})
        return {"sorted": moved_count, "organize_by": organize_by}
        
    except Exception as e:
        return {"error": f"Failed to organize photos by EXIF: {str(e)}"}


# ---------- Cleanup & Maintenance Tools ------------------------------------

@mcp.tool(name="find_duplicates", description="Find duplicate files by comparing file hashes")
async def find_duplicates(source_dir: str, delete_duplicates: bool = False, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source_dir)
        if not src_path.is_dir():
            return {"error": f"'{source_dir}' is not a directory"}
        
        file_hashes = {}
        duplicates = []
        
        for file_path in src_path.rglob("*"):
            if file_path.is_file():
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    if file_hash in file_hashes:
                        duplicates.append({
                            "original": str(file_hashes[file_hash]),
                            "duplicate": str(file_path),
                            "hash": file_hash,
                            "size": file_path.stat().st_size
                        })
                    else:
                        file_hashes[file_hash] = file_path
                except Exception:
                    continue
        
        if not delete_duplicates or dry_run:
            log_operation("find_duplicates", {"source_dir": str(src_path), "duplicates_found": len(duplicates)})
            return {"duplicates": duplicates, "total_duplicates": len(duplicates)}
        
        deleted_count = 0
        for dup in duplicates:
            try:
                Path(dup["duplicate"]).unlink()
                deleted_count += 1
            except Exception:
                continue
        
        log_operation("delete_duplicates", {"source_dir": str(src_path), "deleted": deleted_count})
        return {"duplicates_deleted": deleted_count, "total_duplicates_found": len(duplicates)}
        
    except Exception as e:
        return {"error": f"Failed to find duplicates: {str(e)}"}

@mcp.tool(name="cleanup_empty_folders", description="Find and remove empty folders")
async def cleanup_empty_folders(source_dir: str, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source_dir)
        if not src_path.is_dir():
            return {"error": f"'{source_dir}' is not a directory"}
        
        empty_folders = []
        
        for dir_path in reversed(list(src_path.rglob("*"))):
            if dir_path.is_dir() and dir_path != src_path:
                try:
                    if not any(dir_path.iterdir()):
                        empty_folders.append(str(dir_path))
                except Exception:
                    continue
        
        if dry_run:
            log_operation("cleanup_empty_folders_dry_run", {"source_dir": str(src_path), "empty_folders": len(empty_folders)})
            return {"dry_run": True, "empty_folders": empty_folders, "total": len(empty_folders)}
        
        removed_count = 0
        for folder_path in empty_folders:
            try:
                Path(folder_path).rmdir()
                removed_count += 1
            except Exception:
                continue
        
        log_operation("cleanup_empty_folders", {"source_dir": str(src_path), "removed": removed_count})
        return {"removed_folders": removed_count, "total_empty_found": len(empty_folders)}
        
    except Exception as e:
        return {"error": f"Failed to cleanup empty folders: {str(e)}"}

@mcp.tool(name="cleanup_temp_files", description="Find and remove temporary files (.tmp, .temp, etc.)")
async def cleanup_temp_files(source_dir: str, extensions: List[str] = None, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    if extensions is None:
        extensions = ['.tmp', '.temp', '.cache', '.bak', '.swp', '~']
    
    try:
        src_path = safe_path(source_dir)
        if not src_path.is_dir():
            return {"error": f"'{source_dir}' is not a directory"}
        
        temp_files = []
        
        for file_path in src_path.rglob("*"):
            if file_path.is_file():
                if any(file_path.name.endswith(ext) for ext in extensions):
                    temp_files.append({
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "extension": file_path.suffix
                    })
        
        if dry_run:
            total_size = sum(f["size"] for f in temp_files)
            log_operation("cleanup_temp_files_dry_run", {"source_dir": str(src_path), "temp_files": len(temp_files)})
            return {"dry_run": True, "temp_files": temp_files, "total_files": len(temp_files), "total_size_mb": round(total_size / (1024*1024), 2)}
        
        deleted_count = 0
        total_size_freed = 0
        for temp_file in temp_files:
            try:
                file_path = Path(temp_file["path"])
                total_size_freed += temp_file["size"]
                file_path.unlink()
                deleted_count += 1
            except Exception:
                continue
        
        log_operation("cleanup_temp_files", {"source_dir": str(src_path), "deleted": deleted_count})
        return {"deleted_files": deleted_count, "size_freed_mb": round(total_size_freed / (1024*1024), 2)}
        
    except Exception as e:
        return {"error": f"Failed to cleanup temp files: {str(e)}"}


# ---------- Archiving & Compression ----------------------------------------

@mcp.tool(name="create_archive", description="Create a zip archive of a folder")
async def create_archive(source_path: str, archive_name: str = None, delete_original: bool = False, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        src_path = safe_path(source_path)
        if not src_path.exists():
            return {"error": f"Source '{source_path}' does not exist"}
        
        if archive_name is None:
            archive_name = f"{src_path.name}.zip"
        
        archive_path = src_path.parent / archive_name
        
        if dry_run:
            log_operation("create_archive_dry_run", {"source": str(src_path), "archive": str(archive_path)})
            return {"dry_run": True, "would_create": str(archive_path), "delete_original": delete_original}
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if src_path.is_file():
                zipf.write(src_path, src_path.name)
            else:
                for file_path in src_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(src_path.parent)
                        zipf.write(file_path, arcname)
        
        if delete_original:
            if src_path.is_file():
                src_path.unlink()
            else:
                shutil.rmtree(str(src_path))
        
        log_operation("create_archive", {"source": str(src_path), "archive": str(archive_path), "deleted_original": delete_original})
        return {"archive_created": str(archive_path), "original_deleted": delete_original}
        
    except Exception as e:
        return {"error": f"Failed to create archive: {str(e)}"}

@mcp.tool(name="extract_archive", description="Extract a zip archive")
async def extract_archive(archive_path: str, extract_to: str = None, delete_archive: bool = False, dry_run: bool = None) -> dict:
    if dry_run is None:
        dry_run = DRY_RUN_MODE
    
    try:
        arch_path = safe_path(archive_path)
        if not arch_path.exists() or not arch_path.suffix.lower() == '.zip':
            return {"error": f"Archive '{archive_path}' does not exist or is not a zip file"}
        
        if extract_to is None:
            extract_to = arch_path.parent / arch_path.stem
        else:
            extract_to = safe_path(extract_to)
        
        if dry_run:
            log_operation("extract_archive_dry_run", {"archive": str(arch_path), "extract_to": str(extract_to)})
            return {"dry_run": True, "would_extract": str(arch_path), "to": str(extract_to), "delete_archive": delete_archive}
        
        with zipfile.ZipFile(arch_path, 'r') as zipf:
            zipf.extractall(extract_to)
        
        if delete_archive:
            arch_path.unlink()
        
        log_operation("extract_archive", {"archive": str(arch_path), "extracted_to": str(extract_to), "deleted_archive": delete_archive})
        return {"extracted_to": str(extract_to), "archive_deleted": delete_archive}
        
    except Exception as e:
        return {"error": f"Failed to extract archive: {str(e)}"}


# ---------- Operation Log Management ----------------------------------------

@mcp.tool(name="get_operation_log", description="Get the log of all file operations")
async def get_operation_log(limit: int = 50) -> dict:
    return {"operations": OPERATION_LOG[-limit:], "total_operations": len(OPERATION_LOG)}

@mcp.tool(name="clear_operation_log", description="Clear the operation log")
async def clear_operation_log() -> dict:
    global OPERATION_LOG
    count = len(OPERATION_LOG)
    OPERATION_LOG.clear()
    return {"cleared": count, "message": f"Cleared {count} log entries"}


# ---------- Entrypoint ------------------------------------------------------
if __name__ == "__main__":
    try:
        mcp.run()          # defaults to stdio transport for Claude Desktop
    except KeyboardInterrupt:
        log("Server shutting down.")