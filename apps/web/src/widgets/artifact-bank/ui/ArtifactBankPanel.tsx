import { Database, FileUp, Loader2 } from "lucide-react";
import { type FormEvent, useState } from "react";

import type { SourceSummary } from "@/shared/api";
import { Panel } from "@/shared/ui";

type ArtifactBankPanelProps = {
  sources: SourceSummary[];
  loading: boolean;
  error: string | null;
  onUpload: (file: File) => Promise<void>;
};

export function ArtifactBankPanel({
  sources,
  loading,
  error,
  onUpload,
}: ArtifactBankPanelProps) {
  const [file, setFile] = useState<File | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      return;
    }
    await onUpload(file);
    setFile(null);
    event.currentTarget.reset();
  }

  return (
    <Panel title="Artifact bank">
      <form className="upload-row" onSubmit={handleSubmit}>
        <label className="file-control">
          <FileUp size={16} />
          <span>{file ? file.name : "CSV / Markdown"}</span>
          <input
            accept=".csv,.md,.markdown,.txt,text/csv,text/markdown,text/plain"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            type="file"
          />
        </label>
        <button className="secondary-button" disabled={loading || !file} type="submit">
          {loading ? <Loader2 size={16} /> : <Database size={16} />}
          Ingest
        </button>
      </form>
      {error ? <div className="inline-error">{error}</div> : null}
      <div className="source-list">
        {sources.map((source) => (
          <article className="source-card" key={source.source_id}>
            <div>
              <div className="source-title">{source.title}</div>
              <div className="source-meta">
                {source.document_type} · {source.security_label} · {source.status}
              </div>
            </div>
            <div className="source-counts">
              <span>{source.evidence_count} evidence</span>
              <span>{source.measurement_count} facts</span>
            </div>
          </article>
        ))}
      </div>
    </Panel>
  );
}
