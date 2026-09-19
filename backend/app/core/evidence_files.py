"""Bounded evidence upload validation shared by trade and grievance workflows."""

import re

from fastapi import HTTPException, UploadFile

MAX_EVIDENCE_SIZE_BYTES = 10 * 1024 * 1024
EVIDENCE_SIGNATURES = {
    "image/jpeg": lambda content: content.startswith(b"\xff\xd8\xff"),
    "image/jpg": lambda content: content.startswith(b"\xff\xd8\xff"),
    "image/png": lambda content: content.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda content: len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP",
    "application/pdf": lambda content: content.startswith(b"%PDF-"),
}


async def read_validated_evidence(file: UploadFile) -> tuple[bytes, str, str]:
    mime_type = (file.content_type or "").lower()
    signature_check = EVIDENCE_SIGNATURES.get(mime_type)
    if not signature_check:
        raise HTTPException(status_code=400, detail="Unsupported evidence file type")

    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_EVIDENCE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Evidence file exceeds the 10 MB limit")
        chunks.append(chunk)
    content = b"".join(chunks)
    if not content or not signature_check(content):
        raise HTTPException(status_code=400, detail="File bytes do not match the declared evidence type")

    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", file.filename or "evidence")[:120] or "evidence"
    return content, mime_type, filename
