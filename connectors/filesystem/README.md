# Enhanced Filesystem MCP Connector

A comprehensive filesystem organizer MCP server with advanced sorting, content analysis, and automation capabilities.

## Features

### 🔧 Foundational Operations
- **move_file** - Move/rename files and directories
- **create_directory** - Create directories with parent support  
- **delete_file** - Delete files with optional trash safety
- **copy_file** - Copy files and directories

### 🛡️ Safety Features
- **set_dry_run_mode** - Enable/disable dry run for all operations
- Comprehensive logging with timestamps
- All operations support individual dry run parameters
- Safe path handling and validation

### 📂 Rule-Based Sorting & Automation
- **sort_by_file_type** - Sort files by extensions into folders
- **sort_by_date** - Sort by creation/modification date (YYYY-MM folders)
- **sort_by_size** - Sort into small/medium/large categories
- **sort_by_pattern** - Sort using regex patterns

### 🔍 Content-Aware Organization
- **search_and_organize_by_content** - Organize by text keywords
- **organize_photos_by_exif** - Sort photos by camera model or date from EXIF

### 🧹 Cleanup & Maintenance
- **find_duplicates** - Find/delete duplicates using SHA-256 hashes
- **cleanup_empty_folders** - Remove empty directories
- **cleanup_temp_files** - Remove temporary files (.tmp, .cache, etc.)

### 📦 Archiving & Compression
- **create_archive** - Create ZIP archives with optional deletion
- **extract_archive** - Extract ZIP files with optional cleanup

### 📊 Operation Management
- **get_operation_log** - View operation history
- **clear_operation_log** - Clear operation log

## Setup

### Option 1: Using run_server.py (Recommended)

Update your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "plawan-fs": {
      "command": "python3",
      "args": ["/path/to/filesystem/run_server.py"],
      "env": {}
    }
  }
}
```

### Option 2: Direct uv command with mcp run

```json
{
  "mcpServers": {
    "plawan-fs": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--with", "mcp[cli]",
        "--with", "Pillow>=10.4.0",
        "mcp",
        "run",
        "/Users/plawanrath/Documents/GitHub-public/plawan-claude-connectors/connectors/filesystem/server.py"
      ],
      "env": {}
    }
  }
}
```

### Option 3: Alternative direct uv command

```json
{
  "mcpServers": {
    "plawan-fs": {
      "command": "uv",
      "args": [
        "run",
        "--with", "mcp[cli]",
        "--with", "Pillow>=10.4.0", 
        "python",
        "/path/to/filesystem/server.py"
      ],
      "env": {}
    }
  }
}
```

## Dependencies

- **mcp** - Model Context Protocol framework
- **Pillow** - For EXIF data processing (optional, graceful fallback)

## Usage Examples

```python
# Enable dry run mode for safety
await set_dry_run_mode(True)

# Sort Downloads folder by file type
await sort_by_file_type("/Users/username/Downloads")

# Find and show duplicates
duplicates = await find_duplicates("/Users/username/Documents")

# Organize photos by EXIF date
await organize_photos_by_exif("/Users/username/Photos", organize_by="date")

# Clean up temporary files
await cleanup_temp_files("/Users/username/Downloads")

# Create archive of old project
await create_archive("/Users/username/OldProject", delete_original=True)
```

## Safety Notes

- **Dry Run Mode**: Always test operations first with dry run enabled
- **Trash System**: Files moved to `.trash` folders instead of permanent deletion
- **Comprehensive Logging**: Every operation tracked with timestamps
- **Error Handling**: Robust exception handling throughout
- **Path Safety**: All paths resolved and validated

## Troubleshooting

If you see "Pillow not available" messages, the EXIF photo organization feature will be disabled, but all other features will work normally.

To install Pillow manually:
```bash
pip install Pillow>=10.4.0
```