import React from "react";
import { useDropzone } from "react-dropzone";
import { getApiBase } from "../../lib/api";

type Item = {
  file: File;
  name: string;
  relPath?: string;
  progress: number;
  status: "pending" | "uploading" | "done" | "error";
  errorMsg?: string;
};

export default function Upload({ onUploaded }: { onUploaded?: () => void }) {
  const [items, setItems] = React.useState<Item[]>([]);
  const [isUploading, setIsUploading] = React.useState(false);

  // Hidden input dedicated to folder selection (not controlled by dropzone)
  const dirInputRef = React.useRef<HTMLInputElement | null>(null);
  React.useEffect(() => {
    if (dirInputRef.current) {
      dirInputRef.current.setAttribute("webkitdirectory", "");
      dirInputRef.current.setAttribute("directory", "");
      dirInputRef.current.setAttribute("mozdirectory", "");
    }
  }, []);

  // Drag & drop (files)
  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    if (!acceptedFiles?.length) return;
    const mapped: Item[] = acceptedFiles.map((f) => ({
      file: f,
      relPath: (f as any).webkitRelativePath || undefined,
      name: f.name,
      progress: 0,
      status: "pending",
    }));
    setItems((prev) => [...prev, ...mapped]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    multiple: true,
    noKeyboard: false,
    noClick: false,
    onDrop,
  });

  // Folder picker handler
  function onFolderPicked(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const mapped: Item[] = files.map((f) => ({
      file: f,
      relPath: (f as any).webkitRelativePath || undefined,
      name: f.name,
      progress: 0,
      status: "pending",
    }));
    setItems((prev) => [...prev, ...mapped]);
    // reset the input so picking the same folder again re-triggers change
    e.target.value = "";
  }

  async function uploadAllSequential() {
    const base = getApiBase();
    if (!base) {
      alert("Set API base first");
      return;
    }
    if (!items.length) {
      alert("Drop files or pick a folder first");
      return;
    }

    setIsUploading(true);
    try {
      for (let i = 0; i < items.length; i++) {
        const it = items[i];
        // mark uploading
        setItems((prev) =>
          prev.map((p, idx) =>
            idx === i ? { ...p, status: "uploading", progress: 0 } : p
          )
        );

        try {
          // 1) presign
          const presignRes = await fetch(base + "/upload/presign", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: it.relPath || it.name }),
          });
          if (!presignRes.ok)
            throw new Error(`Presign failed (${presignRes.status})`);
          const presign = await presignRes.json();

          // 2) upload with progress
          await new Promise<void>((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open("POST", presign.url, true);

            xhr.upload.onprogress = (evt) => {
              if (evt.lengthComputable) {
                const pct = Math.round((evt.loaded / evt.total) * 100);
                setItems((prev) =>
                  prev.map((p, idx) =>
                    idx === i ? { ...p, progress: pct } : p
                  )
                );
              }
            };

            xhr.onload = () => {
              if (xhr.status >= 200 && xhr.status < 300) {
                setItems((prev) =>
                  prev.map((p, idx) =>
                    idx === i ? { ...p, progress: 100, status: "done" } : p
                  )
                );
                resolve();
              } else {
                const msg = `S3 error ${xhr.status} ${xhr.statusText}`;
                setItems((prev) =>
                  prev.map((p, idx) =>
                    idx === i ? { ...p, status: "error", errorMsg: msg } : p
                  )
                );
                reject(new Error(msg));
              }
            };

            xhr.onerror = () => {
              const msg = "Network error during upload";
              setItems((prev) =>
                prev.map((p, idx) =>
                  idx === i ? { ...p, status: "error", errorMsg: msg } : p
                )
              );
              reject(new Error(msg));
            };

            const form = new FormData();
            Object.entries(presign.fields || {}).forEach(([k, v]) =>
              form.append(k, String(v))
            );
            form.append("file", it.file);
            xhr.send(form);
          });
        } catch (err: any) {
          setItems((prev) =>
            prev.map((p, idx) =>
              idx === i
                ? { ...p, status: "error", errorMsg: err?.message || "Error" }
                : p
            )
          );
        }
      }
    } finally {
      setIsUploading(false);
      onUploaded && onUploaded();
    }
  }

  function clearList() {
    setItems([]);
  }

  return (
    <div className="card space-y-3">
      <h2 className="text-lg font-semibold">Upload Folder or Files</h2>

      {/* Drop area for files */}
      <div
        {...getRootProps({
          className:
            "border-2 border-dashed rounded p-6 text-center cursor-pointer " +
            (isDragActive ? "bg-gray-50" : "bg-white"),
        })}
      >
        <input {...getInputProps()} />
        <p className="text-sm text-gray-700">
          Drag & drop files here, or click to pick files.
        </p>
        <p className="text-xs text-gray-500 mt-1">
          To upload a whole folder, use the “Select folder” button below.
        </p>
      </div>

      {/* Hidden directory input + button to trigger it */}
      <div className="flex items-center gap-2">
        <input
          ref={dirInputRef}
          type="file"
          multiple
          onChange={onFolderPicked}
          style={{ display: "none" }}
        />
        <button
          className="btn"
          type="button"
          onClick={() => dirInputRef.current?.click()}
        >
          Select folder
        </button>

        <button
          className="btn btn-primary"
          onClick={uploadAllSequential}
          disabled={!items.length || isUploading}
        >
          {isUploading ? "Uploading…" : "Upload"}
        </button>

        <button
          className="btn"
          type="button"
          onClick={clearList}
          disabled={!items.length || isUploading}
        >
          Clear
        </button>

        <span className="text-sm text-gray-600">
          {items.length
            ? `${items.length} file(s) selected`
            : "No files selected"}
        </span>
      </div>

      {/* File list + progress */}
      {items.length > 0 && (
        <div className="space-y-2 max-h-80 overflow-auto">
          {items.map((it, idx) => (
            <div key={`${it.relPath || it.name}-${idx}`} className="space-y-1">
              <div className="flex justify-between text-sm">
                <div className="truncate">
                  {it.relPath ? it.relPath : it.name}
                  {it.status === "error" && (
                    <span className="ml-2 text-red-600">({it.errorMsg})</span>
                  )}
                </div>
                <div>
                  {it.status === "done"
                    ? "✅ Done"
                    : it.status === "error"
                    ? "❌ Error"
                    : `${it.progress}%`}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded h-2">
                <div
                  className={`h-2 rounded ${
                    it.status === "error" ? "bg-red-500" : "bg-blue-500"
                  }`}
                  style={{ width: `${it.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
