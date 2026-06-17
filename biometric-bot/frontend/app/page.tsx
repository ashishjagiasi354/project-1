"use client";

import React, { useState, useRef } from "react";
import { Upload, ShieldCheck, Download, RefreshCw, AlertTriangle } from "lucide-react";

export default function PrivacyBot() {
  const [loading, setLoading] = useState<boolean>(false);
  const [imagePair, setImagePair] = useState<{ original: string; protected: string } | null>(null);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processImage = async (file: File) => {
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("https://biometric-protection-api.onrender.com/protect-biometrics", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Processing failed");

      const blob = await response.blob();
      const combinedImageUrl = URL.createObjectURL(blob);

      const img = new Image();
      img.src = combinedImageUrl;
      img.onload = () => {
        const halfWidth = img.width / 2;
        
        const canvasLeft = document.createElement("canvas");
        canvasLeft.width = halfWidth;
        canvasLeft.height = img.height;
        const ctxLeft = canvasLeft.getContext("2d");
        ctxLeft?.drawImage(img, 0, 0, halfWidth, img.height, 0, 0, halfWidth, img.height);

        const canvasRight = document.createElement("canvas");
        canvasRight.width = halfWidth;
        canvasRight.height = img.height;
        const ctxRight = canvasRight.getContext("2d");
        ctxRight?.drawImage(img, halfWidth, 0, halfWidth, img.height, 0, 0, halfWidth, img.height);

        setImagePair({
          original: canvasLeft.toDataURL("image/jpeg"),
          protected: canvasRight.toDataURL("image/jpeg"),
        });
        setLoading(false);
      };
    } catch (error) {
      console.error("Error updating image:", error);
      alert("An error occurred processing your image. Check your backend server configuration.");
      setLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processImage(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processImage(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const resetScanner = () => {
    setImagePair(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ShieldCheck className="w-8 h-8 text-emerald-400" />
          <span className="font-bold text-xl tracking-wide bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
            Biometric Protection AI
          </span>
        </div>
        <div className="text-xs text-slate-400 font-mono bg-slate-800/60 px-3 py-1.5 rounded-full border border-slate-700/50">
          Status: Hand Tracking Active
        </div>
      </header>

      {/* Main Content View */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col justify-center items-center">
        {!imagePair ? (
          <div className="w-full max-w-2xl flex flex-col items-center">
            {/* Drag & Drop Upload Space */}
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={triggerFileInput}
              className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center w-full min-h-[400px] ${
                dragActive
                  ? "border-emerald-400 bg-emerald-950/20 shadow-[0_0_30px_rgba(16,185,129,0.1)]"
                  : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60"
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                className="hidden"
              />
              
              {loading ? (
                <div className="flex flex-col items-center space-y-4">
                  <RefreshCw className="w-12 h-12 text-emerald-400 animate-spin" />
                  <p className="text-lg font-medium text-slate-200">De-identifying Biometric Patterns...</p>
                  <p className="text-sm text-slate-500">Isolating structural contours & applying filter matrix</p>
                </div>
              ) : (
                <>
                  <div className="p-4 bg-slate-900 rounded-full border border-slate-800 mb-4 shadow-inner">
                    <Upload className="w-8 h-8 text-slate-400" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Upload image for anonymization</h3>
                  <p className="text-sm text-slate-400 max-w-md mb-6">
                    Drag and drop your photograph here, or click to browse. The model automatically localizes finger vectors to blur high-frequency minutiae patterns.
                  </p>
                  <span className="text-xs bg-slate-800 text-slate-300 px-3 py-1.5 rounded-md font-mono border border-slate-700">
                    Supports PNG, JPG, WEBP
                  </span>
                </>
              )}
            </div>

            {/* Terms & Privacy Disclaimer Banner */}
            <div className="mt-6 text-center max-w-lg">
              <p className="text-xs text-slate-500 leading-relaxed">
                By uploading a file, you agree to the usage guidelines. Images are processed entirely in volatile server memory structures and are instantly destroyed post-computation. No biometric markers or user data are saved or logged.
              </p>
            </div>
          </div>
        ) : (
          /* Side-by-Side Verification Screen */
          <div className="w-full space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold tracking-tight">Anonymization Vector Output</h2>
                <p className="text-sm text-slate-400">Review localized adjustments prior to distribution</p>
              </div>
              <button
                onClick={resetScanner}
                className="flex items-center space-x-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 px-4 py-2 rounded-xl transition text-sm font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Upload New Frame</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Left Column: Original with Warning Markers */}
              <div className="bg-slate-900/60 rounded-2xl border border-slate-800 overflow-hidden shadow-lg flex flex-col">
                <div className="px-4 py-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" /> Biometric Signature Vectors Detected
                  </span>
                </div>
                <div className="flex-1 bg-slate-950 p-4 flex items-center justify-center min-h-[350px]">
                  <img
                    src={imagePair.original}
                    alt="Original vector map"
                    className="max-h-[500px] w-auto object-contain rounded-lg shadow-md"
                  />
                </div>
              </div>

              {/* Right Column: Protected Output */}
              <div className="bg-slate-900/60 rounded-2xl border border-slate-800 overflow-hidden shadow-lg flex flex-col">
                <div className="px-4 py-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5" /> Structural Outline Protected
                  </span>
                  <a
                    href={imagePair.protected}
                    download="biometric_shielded_output.jpg"
                    className="flex items-center space-x-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 px-2.5 py-1 rounded-md text-xs font-bold transition shadow-sm"
                  >
                    <Download className="w-3 h-3" />
                    <span>Download</span>
                  </a>
                </div>
                <div className="flex-1 bg-slate-950 p-4 flex items-center justify-center min-h-[350px]">
                  <img
                    src={imagePair.protected}
                    alt="Anonymized output frame"
                    className="max-h-[500px] w-auto object-contain rounded-lg shadow-md"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}