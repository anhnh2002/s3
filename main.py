import os
import uuid
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

app = FastAPI(
    title="S3-like Storage API",
    description="A simple S3-like storage service for uploading and downloading files",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
STORAGE_PATH = Path("/app/storage")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# In-memory database (in production, use a real database)
file_metadata = {}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "S3-like Storage API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload",
            "download": "GET /files/{file_id}",
            "info": "GET /files/{file_id}/info",
            "list": "GET /files",
            "delete": "DELETE /files/{file_id}"
        }
    }


@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """
    Upload a file to the storage.
    Maximum file size: 50MB
    
    Returns:
        - file_id: Unique identifier for the file
        - filename: Original filename
        - url: Direct download link
        - size: File size in bytes
    """
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot upload empty file"
            )
        
        # Get file extension
        original_filename = file.filename or "unnamed"
        file_extension = Path(original_filename).suffix
        
        # Create storage filename
        storage_filename = f"{file_id}{file_extension}"
        storage_filepath = STORAGE_PATH / storage_filename
        
        # Save file
        async with aiofiles.open(storage_filepath, 'wb') as f:
            await f.write(content)
        
        # Store metadata
        file_metadata[file_id] = {
            "file_id": file_id,
            "original_filename": original_filename,
            "storage_filename": storage_filename,
            "size": file_size,
            "content_type": file.content_type,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        
        # Generate download URL
        base_url = str(request.base_url).rstrip('/')
        download_url = f"{base_url}/files/{file_id}"
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": original_filename,
            "url": download_url,
            "size": file_size,
            "uploaded_at": file_metadata[file_id]["uploaded_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.get("/files/{file_id}")
async def download_file(file_id: str, download: Optional[bool] = False):
    """
    Download or view a file by its ID
    
    Parameters:
        - file_id: Unique file identifier
        - download: If True, forces download. If False (default), displays inline (useful for images in markdown)
    """
    if file_id not in file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    metadata = file_metadata[file_id]
    filepath = STORAGE_PATH / metadata["storage_filename"]
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found on storage")
    
    # Determine Content-Disposition based on download parameter
    # inline: allows browser to display the file (images, PDFs, etc.)
    # attachment: forces download
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Cache-Control": "public, max-age=31536000"
    }
    
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{metadata["original_filename"]}"'
    else:
        headers["Content-Disposition"] = f'inline; filename="{metadata["original_filename"]}"'
    
    return FileResponse(
        path=filepath,
        media_type=metadata.get("content_type", "application/octet-stream"),
        headers=headers
    )


@app.get("/files/{file_id}/info")
async def get_file_info(file_id: str):
    """
    Get file metadata without downloading it
    """
    if file_id not in file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file_metadata[file_id]


@app.get("/files/{file_id}/base64")
async def get_file_as_base64(file_id: str):
    """
    Get file as base64 data URL (useful for embedding in markdown when CSP blocks external URLs)
    Returns a data URL that can be used directly in markdown: ![alt](data:image/png;base64,...)
    """
    if file_id not in file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    metadata = file_metadata[file_id]
    filepath = STORAGE_PATH / metadata["storage_filename"]
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found on storage")
    
    # Read file and convert to base64
    async with aiofiles.open(filepath, 'rb') as f:
        file_content = await f.read()
    
    base64_content = base64.b64encode(file_content).decode('utf-8')
    content_type = metadata.get("content_type", "application/octet-stream")
    
    # Create data URL
    data_url = f"data:{content_type};base64,{base64_content}"
    
    return {
        "file_id": file_id,
        "filename": metadata["original_filename"],
        "content_type": content_type,
        "size": metadata["size"],
        "data_url": data_url
    }


@app.get("/files")
async def list_files(limit: int = 100, offset: int = 0):
    """
    List all uploaded files
    """
    files = list(file_metadata.values())
    total = len(files)
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "files": files[offset:offset + limit]
    }


@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """
    Delete a file by its ID
    """
    if file_id not in file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    metadata = file_metadata[file_id]
    filepath = STORAGE_PATH / metadata["storage_filename"]
    
    # Delete physical file
    if filepath.exists():
        filepath.unlink()
    
    # Delete metadata
    del file_metadata[file_id]
    
    return {
        "success": True,
        "message": f"File {file_id} deleted successfully"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "storage_path": str(STORAGE_PATH),
        "total_files": len(file_metadata)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
