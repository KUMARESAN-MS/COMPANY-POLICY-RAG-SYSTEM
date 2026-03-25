import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileUp, 
  FileText, 
  Trash2, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Database,
  CloudUpload
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { uploadDocument, listDocuments, deleteDocument, type Document } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

export default function AdminPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [totalVectors, setTotalVectors] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const fetchDocs = async () => {
    try {
      const data = await listDocuments();
      setDocuments(data.documents);
      setTotalVectors(data.total_vectors);
    } catch (error) {
      toast.error('Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleUpload = async (file: File) => {
    if (!file) return;
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      toast.error('Only PDF and DOCX files are supported');
      return;
    }

    setIsUploading(true);
    const toastId = toast.loading(`Indexing ${file.name}...`);

    try {
      await uploadDocument(file);
      toast.success(`${file.name} indexed successfully`, { id: toastId });
      fetchDocs();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed', { id: toastId });
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleUpload(e.target.files[0]);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteDocument(id);
      toast.success('Document marked for deletion');
      fetchDocs();
    } catch (error) {
      toast.error('Failed to delete document');
    }
  };

  return (
    <div className="max-w-6xl mx-auto pt-8 pb-12 px-4 space-y-12">
      <div className="flex items-end justify-between">
        <div className="space-y-1">
          <h1 className="text-4xl font-bold tracking-tight text-glow">Knowledge Base</h1>
          <p className="text-muted-foreground">Manage your company policies and RAG indexing from here.</p>
        </div>
        <div className="flex gap-4">
          <Card className="glass-card px-6 py-3 flex items-center gap-4">
            <Database className="text-primary w-5 h-5" />
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground leading-none mb-1">Total Vectors</p>
              <p className="font-mono text-xl font-bold">{totalVectors.toLocaleString()}</p>
            </div>
          </Card>
          <Card className="glass-card px-6 py-3 flex items-center gap-4">
            <FileText className="text-primary w-5 h-5" />
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground leading-none mb-1">Documents</p>
              <p className="font-mono text-xl font-bold">{documents.filter(d => !d.is_deleted).length}</p>
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-6">
          <h3 className="text-xl font-semibold flex items-center gap-2">
            <CloudUpload className="text-primary w-5 h-5" />
            Upload Policy
          </h3>
          <div 
            className={cn(
              "relative border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center transition-all h-64",
              dragActive ? "border-primary bg-primary/5 scale-[0.98]" : "border-white/10 hover:border-white/20",
              isUploading && "opacity-50 pointer-events-none"
            )}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0]);
            }}
          >
            <input 
              type="file" 
              className="absolute inset-0 opacity-0 cursor-pointer"
              onChange={handleFileChange}
              accept=".pdf,.docx"
            />
            {isUploading ? (
              <div className="space-y-4">
                <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto" />
                <p className="text-sm">Processing & Indexing...</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto">
                  <FileUp className="w-8 h-8 text-muted-foreground" />
                </div>
                <div>
                  <p className="font-medium">Drop policy file here</p>
                  <p className="text-xs text-muted-foreground mt-1">PDF or DOCX (max 20MB)</p>
                </div>
                <Button variant="outline" size="sm" className="bg-white/5 border-white/10">
                  Select File
                </Button>
              </div>
            )}
          </div>
          
          <div className="glass-card p-4 rounded-xl space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Indexing Status</h4>
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> Vector DB</span>
              <span className="text-green-500 font-medium">Ready</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500" /> GEMINI API</span>
              <span className="text-green-500 font-medium">Connected</span>
            </div>
          </div>
        </div>

        <div className="md:col-span-2 space-y-6">
          <h3 className="text-xl font-semibold flex items-center gap-2">
            <FileText className="text-primary w-5 h-5" />
            Indexed Documents
          </h3>
          <div className="space-y-4 h-[500px] overflow-y-auto pr-2 custom-scrollbar">
            <AnimatePresence mode="popLayout">
              {isLoading ? (
                [1, 2, 3].map(i => (
                  <Skeleton key={i} className="h-24 w-full rounded-2xl bg-white/5" />
                ))
              ) : documents.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-center">
                  <AlertCircle className="w-12 h-12 mb-4 opacity-20" />
                  <p>No documents indexed yet.</p>
                  <p className="text-sm">Upload your first policy to get started.</p>
                </div>
              ) : (
                documents.map((doc) => (
                  <motion.div
                    key={doc.id}
                    layout
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className={cn(
                      "glass-card p-6 rounded-2xl flex items-center justify-between transition-all group",
                      doc.is_deleted && "opacity-40 grayscale"
                    )}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                        <FileText className="text-primary w-6 h-6" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-lg">{doc.filename}</h4>
                        <p className="text-xs text-muted-foreground flex items-center gap-2">
                          Uploaded on {new Date(doc.upload_time).toLocaleDateString()}
                          {doc.is_deleted && <span className="text-destructive font-mono uppercase">[Deleted]</span>}
                        </p>
                      </div>
                    </div>
                    {!doc.is_deleted && (
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        onClick={() => handleDelete(doc.id)}
                        className="hover:bg-destructive/20 hover:text-destructive text-muted-foreground opacity-0 group-hover:opacity-100 transition-all"
                      >
                        <Trash2 className="w-5 h-5" />
                      </Button>
                    )}
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
