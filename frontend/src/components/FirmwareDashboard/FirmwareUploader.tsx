// src/components/FirmwareDashboard/FirmwareUploader.tsx

import React, { useRef, useState } from "react";
import APIService from "@/services/apiService";
import "./FirmwareUploader.css";

interface FirmwareUploaderProps {
    onUploadSuccess?: () => void;
    onUploadError?: (message: string) => void;
    acceptExtensions?: string[]; // e.g. [".bin", ".hex"]
    allowMultiple?: boolean;
}

const FirmwareUploader: React.FC<FirmwareUploaderProps> = ({
    onUploadSuccess,
    onUploadError,
    acceptExtensions = [".bin", ".hex", ".fw"],
    allowMultiple = false,
}) => {
    const [files, setFiles] = useState<File[]>([]);
    const [loading, setLoading] = useState(false);
    const dropRef = useRef<HTMLDivElement | null>(null);

    const validateFile = (file: File): boolean =>
        acceptExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));

    const handleFileChange = (inputFiles: FileList | null) => {
        if (!inputFiles) return;
        const list = Array.from(inputFiles);
        const valid = list.filter(validateFile);
        if (valid.length !== list.length) {
            alert("Some files were skipped due to invalid extensions.");
        }
        setFiles(allowMultiple ? valid : valid.slice(0, 1));
    };

    const handleUpload = async () => {
        if (!files.length) return;
        setLoading(true);
        try {
            const formData = new FormData();
            // backend can accept multiple under same field name, or use firmware[] if that's what it expects
            files.forEach((f) => formData.append("firmware", f));

            // Do NOT set Content-Type when sending FormData
            await APIService.apiCallWithRetry("firmware/upload", "POST", formData);

            onUploadSuccess?.();
            alert("Firmware uploaded successfully.");
            setFiles([]);
        } catch (err: any) {
            const msg = err?.message || "Upload failed.";
            console.error("Upload error:", err);
            onUploadError?.(msg);
            alert(msg);
        } finally {
            setLoading(false);
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileChange(e.dataTransfer.files);
            e.dataTransfer.clearData();
        }
        dropRef.current?.classList.remove("drag-over");
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        dropRef.current?.classList.add("drag-over");
    };

    const handleDragLeave = () => {
        dropRef.current?.classList.remove("drag-over");
    };

    return (
        <div
            className="firmware-uploader"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            ref={dropRef}
        >
            <input
                type="file"
                multiple={allowMultiple}
                onChange={(e) => handleFileChange(e.target.files)}
                accept={acceptExtensions.join(",")}
            />

            <div className="firmware-dropzone">
                {files.length > 0 ? (
                    <ul className="file-list">
                        {files.map((f, i) => (
                            <li key={`${f.name}-${f.size}-${i}`}>
                                {f.name} <span className="file-size">({Math.ceil(f.size / 1024)} KB)</span>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p>Drop firmware here or select a file to upload</p>
                )}
            </div>

            <button onClick={handleUpload} disabled={!files.length || loading}>
                {loading ? "Uploading..." : allowMultiple ? "Upload Files" : "Upload Firmware"}
            </button>
        </div>
    );
};

export default FirmwareUploader;
