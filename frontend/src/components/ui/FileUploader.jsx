import React, { useRef, useState } from 'react';
import { UploadCloud, FileCheck, AlertCircle, Camera, X } from 'lucide-react';

/**
 * FileUploader: Mobile-optimized drag-and-drop or camera file selector
 * for proof-of-pickup, weighment slips, and quality certificates.
 */
export function FileUploader({
  label = 'Upload document or evidence',
  description = 'Supports JPEG, PNG, or PDF up to 10MB',
  accept = 'image/jpeg,image/png,application/pdf',
  capture = null, // e.g. "environment" for back camera on mobile
  onFileSelect,
  maxSizeMB = 10,
  className = '',
  disabled = false,
}) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const handleFiles = (files) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > maxSizeMB) {
      setError(`File size exceeds ${maxSizeMB}MB limit.`);
      return;
    }
    setError(null);
    setSelectedFile(file);
    if (onFileSelect) {
      onFileSelect(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (disabled) return;
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleClear = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
    if (onFileSelect) onFileSelect(null);
  };

  return (
    <div className={`w-full ${className}`}>
      {label && <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>}

      <div
        onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
        onDragOver={(e) => { e.preventDefault(); }}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors ${
          disabled ? 'bg-gray-100 border-gray-200 cursor-not-allowed' :
          dragActive ? 'border-green-500 bg-green-50/50' :
          selectedFile ? 'border-emerald-500 bg-emerald-50/30' :
          'border-gray-300 hover:border-gray-400 bg-gray-50/50'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          capture={capture}
          disabled={disabled}
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />

        {selectedFile ? (
          <div className="flex items-center justify-between gap-3 text-left">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                <FileCheck className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB • Ready for submission</p>
              </div>
            </div>
            {!disabled && (
              <button
                type="button"
                onClick={handleClear}
                className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                aria-label="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-2">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-10 h-10 rounded-full bg-green-100 text-green-700 flex items-center justify-center">
                <UploadCloud className="w-5 h-5" />
              </div>
              {capture && (
                <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center">
                  <Camera className="w-5 h-5" />
                </div>
              )}
            </div>
            <p className="text-sm font-medium text-gray-700">
              Click to browse or take photo
            </p>
            <p className="text-xs text-gray-500 mt-0.5">{description}</p>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-1.5 text-xs text-red-600 mt-1.5">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

export default FileUploader;
