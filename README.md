# S3-like Storage API

A simple, self-hosted S3-like storage service built with FastAPI and Docker. Upload files up to 50MB and get direct download links.

## Features

- 📤 **File Upload**: Upload files up to 50MB
- 📥 **File Download**: Download files via direct links
- 📋 **File Listing**: List all uploaded files
- 🗑️ **File Deletion**: Delete files by ID
- 🔍 **File Metadata**: Get file information without downloading
- 🚀 **Fast & Lightweight**: Built with FastAPI
- 🐳 **Docker Ready**: Easy deployment with Docker Compose

## Quick Start

### Prerequisites

- Docker
- Docker Compose

### Installation & Running

1. Clone or navigate to the project directory:
```bash
cd /home/aithucchien/s3
```

2. Build and start the service:
```bash
docker-compose up -d --build
```

3. The API will be available at `http://localhost:8000`

4. Access the interactive API documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Stopping the Service

```bash
docker-compose down
```

## API Endpoints

### 1. Upload File
**POST** `/upload`

Upload a file to the storage (max 50MB).

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/your/file.pdf"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/upload"
files = {"file": open("example.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

**Response:**
```json
{
  "success": true,
  "file_id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "example.pdf",
  "url": "http://localhost:8000/files/123e4567-e89b-12d3-a456-426614174000",
  "size": 1024567,
  "uploaded_at": "2024-01-01T12:00:00.000000"
}
```

### 2. Download File
**GET** `/files/{file_id}`

Download a file by its ID.

**Example:**
```bash
curl -O "http://localhost:8000/files/123e4567-e89b-12d3-a456-426614174000"
```

### 3. Get File Info
**GET** `/files/{file_id}/info`

Get file metadata without downloading.

**Example:**
```bash
curl "http://localhost:8000/files/123e4567-e89b-12d3-a456-426614174000/info"
```

### 4. List Files
**GET** `/files?limit=100&offset=0`

List all uploaded files with pagination.

**Example:**
```bash
curl "http://localhost:8000/files?limit=10&offset=0"
```

### 5. Delete File
**DELETE** `/files/{file_id}`

Delete a file by its ID.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/files/123e4567-e89b-12d3-a456-426614174000"
```

### 6. Health Check
**GET** `/health`

Check service health and status.

**Example:**
```bash
curl "http://localhost:8000/health"
```

## Configuration

### File Size Limit

The default maximum file size is 50MB. To change this, modify the `MAX_FILE_SIZE` variable in `main.py`:

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
```

### Storage Path

Files are stored in the `./storage` directory by default. This is mounted as a Docker volume, so files persist even when the container is restarted.

### Port Configuration

To change the port, modify the `docker-compose.yml` file:

```yaml
ports:
  - "8080:8000"  # Change 8080 to your desired port
```

## Development

### Running without Docker

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Project Structure

```
s3/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker image configuration
├── docker-compose.yml  # Docker Compose configuration
├── .dockerignore       # Docker ignore patterns
├── .gitignore          # Git ignore patterns
├── README.md           # This file
└── storage/            # File storage directory (created automatically)
```

## Notes

- This implementation uses in-memory storage for file metadata. In production, use a real database (PostgreSQL, MongoDB, etc.)
- Files are stored on the local filesystem. For production, consider using actual S3, MinIO, or other object storage
- The API has CORS enabled for all origins. Adjust this in production for security
- No authentication is implemented. Add authentication/authorization for production use

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, modify the port in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"
```

### Permission Issues with Storage Directory

If you encounter permission issues, ensure the storage directory has proper permissions:
```bash
mkdir -p storage
chmod 777 storage
```

### View Container Logs

```bash
docker-compose logs -f s3-api
```

## License

MIT License - Feel free to use this project for any purpose.

