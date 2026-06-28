import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { QuestionForm } from "@/features/ask-question";
import {
  askQuestion,
  listSources,
  uploadSource,
  type AskResponse,
  type SourceSummary,
} from "@/shared/api";
import { Panel } from "@/shared/ui";
import { ArtifactBankPanel, EvidenceList } from "@/widgets/artifact-bank";
import { EvaluationDashboard } from "@/widgets/evaluation-dashboard";
import { GraphView } from "@/widgets/graph-view";

export function AnalysisWorkbench() {
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [artifactError, setArtifactError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState<SourceSummary[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    void refreshSources();
  }, []);

  async function refreshSources() {
    try {
      setArtifactError(null);
      setSources(await listSources());
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "Не удалось загрузить источники");
    }
  }

  async function handleSubmit(question: string) {
    setLoading(true);
    setError(null);
    try {
      setAnswer(await askQuestion(question));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось выполнить запрос");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(file: File) {
    setUploading(true);
    setArtifactError(null);
    try {
      const result = await uploadSource(file);
      await refreshSources();
      if (result.warnings.length > 0) {
        setArtifactError(result.warnings.join(" "));
      }
    } catch (err) {
      setArtifactError(err instanceof Error ? err.message : "Не удалось загрузить источник");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="workbench-grid">
      <div className="stack">
        <Panel title="Вопрос исследователя">
          <QuestionForm disabled={loading} onSubmit={handleSubmit} />
        </Panel>

        <Panel title="Сводка по доказательствам">
          {loading ? (
            <div className="status-pill">
              <Loader2 size={16} />
              Выполняю retrieval и проверку claims
            </div>
          ) : null}
          {error ? (
            <div className="status-pill">
              <AlertTriangle size={16} />
              {error}
            </div>
          ) : null}
          {answer ? (
            <div className="answer-list">
              {answer.answer_summary.map((sentence) => (
                <div className="answer-sentence" key={sentence.sentence}>
                  {sentence.sentence}
                </div>
              ))}
            </div>
          ) : (
            <div className="status-pill">
              <CheckCircle2 size={16} />
              Готово к первому запросу
            </div>
          )}
        </Panel>

        {answer ? (
          <Panel title="Таблица экспериментов">
            <table className="experiment-table">
              <thead>
                <tr>
                  <th>Материал</th>
                  <th>Режим</th>
                  <th>Свойство</th>
                  <th>Эффект</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {answer.experiments.map((experiment) => (
                  <tr key={experiment.experiment_id}>
                    <td>{experiment.material_name}</td>
                    <td>{experiment.regime_summary}</td>
                    <td>{experiment.property_name}</td>
                    <td>
                      {String(experiment.measurement.effect_direction)} ·{" "}
                      {String(experiment.measurement.value)} {String(experiment.measurement.unit)}
                    </td>
                    <td>{experiment.evidence_ids.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        ) : null}
      </div>

      <div className="stack">
        <ArtifactBankPanel
          error={artifactError}
          loading={uploading}
          onUpload={handleUpload}
          sources={sources}
        />
        {answer ? (
          <>
            <EvidenceList evidence={answer.evidence} />
            <GraphView graphPaths={answer.graph_paths} />
            <EvaluationDashboard answer={answer} />
          </>
        ) : (
          <Panel title="Рабочая область">
            <p className="page-caption">
              Первый запрос покажет таблицу экспериментов, evidence cards, графовый путь,
              противоречия, пробелы и проверку неподдержанных claims.
            </p>
          </Panel>
        )}
      </div>
    </div>
  );
}
