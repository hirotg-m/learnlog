import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiClient } from "../lib/apiClient";
import type { Qualification, StudyLog } from "../types/api";
import "./StudyLogPanel.css";

type StudyLogPanelProps = {
  qualifications: Qualification[];
  onCreated: () => Promise<void>;
};

function todayString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = `${now.getMonth() + 1}`.padStart(2, "0");
  const day = `${now.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function StudyLogPanel(props: StudyLogPanelProps): JSX.Element {
  const activeQualifications = useMemo(
    () => props.qualifications.filter((item) => item.status === "active"),
    [props.qualifications]
  );
  const [qualificationId, setQualificationId] = useState("");
  const [date, setDate] = useState(todayString());
  const [hours, setHours] = useState("1");
  const [content, setContent] = useState("");
  const [memo, setMemo] = useState("");
  const [logs, setLogs] = useState<StudyLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!qualificationId && activeQualifications.length > 0) {
      setQualificationId(activeQualifications[0].id);
    }
  }, [activeQualifications, qualificationId]);

  useEffect(() => {
    async function loadLogs(): Promise<void> {
      try {
        const result = await apiClient.listStudyLogs();
        setLogs(result.items.slice(0, 25));
      } catch (errorValue) {
        setError(apiClient.errorMessage(errorValue));
      }
    }

    void loadLogs();
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);

    const parsedHours = Number(hours);
    if (Number.isNaN(parsedHours) || parsedHours <= 0 || Math.round(parsedHours * 100) % 25 !== 0) {
      setError("時間は 0.25 刻みで入力してください");
      return;
    }

    setSaving(true);
    try {
      await apiClient.createStudyLog({
        qualificationId,
        date,
        hours: parsedHours,
        content,
        memo: memo.trim() === "" ? null : memo,
      });

      const refreshed = await apiClient.listStudyLogs();
      setLogs(refreshed.items.slice(0, 25));
      setContent("");
      setMemo("");
      await props.onCreated();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    } finally {
      setSaving(false);
    }
  }

  function qualificationLabel(id: string): string {
    const found = props.qualifications.find((item) => item.id === id);
    if (!found) {
      return "未登録の資格";
    }
    return found.abbreviation ?? found.name;
  }

  return (
    <section className="panel studyLogPanel">
      <h2>学習記録入力</h2>
      <form className="studyForm" onSubmit={onSubmit}>
        <select
          value={qualificationId}
          onChange={(event) => setQualificationId(event.target.value)}
          required
        >
          {activeQualifications.map((item) => (
            <option key={item.id} value={item.id}>
              {item.abbreviation ?? item.name}
            </option>
          ))}
        </select>
        <div className="twoCols">
          <input type="date" value={date} onChange={(event) => setDate(event.target.value)} required />
          <input
            type="number"
            step="0.25"
            min="0.25"
            value={hours}
            onChange={(event) => setHours(event.target.value)}
            required
          />
        </div>
        <input
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder="やったこと"
          required
        />
        <textarea
          value={memo}
          onChange={(event) => setMemo(event.target.value)}
          placeholder="メモ (任意)"
          rows={3}
        />
        <button type="submit" disabled={saving || activeQualifications.length === 0}>
          {saving ? "保存中..." : "記録を追加"}
        </button>
      </form>

      {error && <p className="errorText">{error}</p>}

      <ul className="studyLogList">
        {logs.map((log) => (
          <li key={log.id}>
            <p>
              <strong>{qualificationLabel(log.qualificationId)}</strong> / {log.date} / {log.hours}h
            </p>
            <p>{log.content}</p>
            {log.memo && <p className="memo">{log.memo}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
}