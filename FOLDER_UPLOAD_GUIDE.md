# Folder Upload Feature Guide

## Overview
The folder upload feature allows you to upload entire directories with all their files and subdirectories. All files are automatically analyzed based on their type.

## How to Use

### Frontend (Web UI)
1. Click the **"📂 Upload Folder"** button in the main interface
2. Select a folder from your file system
3. All files in the folder and its subdirectories will be uploaded
4. Each file is automatically analyzed based on its type:
   - **JSON files**: Schema detection, statistics, sample data
   - **Text files**: Word count, readability, keyword extraction
   - **Image files**: Dimensions, format, perceptual hash

### Backend API Endpoint
```
POST /upload/folder
Content-Type: multipart/form-data
```

**Request:**
```javascript
const formData = new FormData();
for (const file of files) {
    formData.append('files', file);
}

fetch('http://localhost:8000/upload/folder', {
    method: 'POST',
    body: formData
});
```

**Response:**
```json
{
    "folder_id": "abc123-def456-ghi789",
    "total_files": 15,
    "successful": 14,
    "failed": 1,
    "results": [
        {
            "file_id": "file-id-1",
            "filename": "data.json",
            "file_type": "json",
            "size": 2048,
            "analyzed": true,
            "analysis_preview": {
                "type": "json",
                "status": "success"
            }
        },
        // ... more files
    ],
    "message": "Processed 15 files from folder"
}
```

## Features

### Automatic Analysis
- Files are automatically analyzed during upload
- No need to make separate analysis requests
- Results are immediately available

### Error Handling
- Individual file failures don't stop the entire upload
- Detailed error information for each failed file
- Summary statistics for successful/failed uploads

### Folder Grouping
- All files from the same folder share a `folder_id`
- Easy to identify files that belong together
- Can query by folder_id in the future

### Supported File Types
- **JSON**: `.json`
- **Text**: `.txt`, `.md`, `.csv`, `.log`, `.rtf`
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`

## UI Features

### Summary Card
After upload, a summary card is displayed showing:
- Folder ID (first 8 characters)
- Total files uploaded
- Success/failure counts
- File type breakdown

### Real-time Logging
The reasoning log shows:
- Upload progress
- Analysis status for each file
- Errors and warnings
- Final summary statistics

### File List
All uploaded files appear in the files list with:
- File name and type
- Size and upload timestamp
- View details button for individual analysis

## Example Use Cases

1. **Dataset Upload**: Upload an entire dataset folder with JSON data files
2. **Document Collection**: Upload a folder of markdown or text documents
3. **Image Gallery**: Upload a folder of photos for duplicate detection
4. **Mixed Content**: Upload folders with different file types for comprehensive analysis

## Technical Details

### Backend Processing
1. Each file is assigned a unique `file_id`
2. Files are stored in `data/raw/uploads/`
3. Metadata is saved in `data/processed/metadata/`
4. All files share the same `folder_id` and `uploaded_at` timestamp
5. Analysis is performed synchronously during upload

### Performance
- Large folders may take time to process
- Analysis runs for each file individually
- Progress is reported in real-time via logs
- Failed files don't block other uploads

### Limitations
- Browser folder selection requires `webkitdirectory` support (Chrome, Edge, Safari)
- Very large folders (>1000 files) may take significant time
- Individual file size limits still apply
- All files are analyzed - no selective processing yet

## Future Enhancements
- Batch analysis optimization
- Selective file type filtering
- Progress bar for large uploads
- Pause/resume functionality
- Folder structure preservation in metadata
