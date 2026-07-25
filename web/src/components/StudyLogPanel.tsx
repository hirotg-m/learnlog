import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiClient } from "../lib/apiClient";
import type { Qualification, StudyLog } from "../types/api";
import "./StudyLogPanel.css";

type StudyLogPanelProps = {
  qualification: Qualification;
  onChanged: () => Promise<void>;
};

type DayGroup = {
  date: string;
  totalHours: number;
  items: StudyLog[];
};

function groupByDate(logs: StudyLog[]): DayGroup[] {
  const groups: DayGroup[] = [];
  for (const log of logs) {
    const last = groups[groups.length - 1];
    if (last && last.date === log.date) {
      last.items.push(log);
      last.totalHours += log.hours;
    } else {
      groups.push({ date: log.date, totalHours: log.hours, items: [log] });
    }
  }
  return groups;
}

function todayString(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = `${now.getMonth() + 1}`.padStart(2, "0");
  const day = `${now.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function StudyLogPanel(props: StudyLogPanelProps): JSX.Element {
  const { qualification } = props;
  const isClosed = qualification.status === "close";

  const [date, setDate] = useState(todayString());
  const [hours, setHours] = useState("1");
  const [content, setContent] = useState("");
  const [memo, setMemo] = useState("");
  const [logs, setLogs] = useState<StudyLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDate, setEditDate] = useState("");
  const [editHours, setEditHours] = useState("1");
  const [editContent, setEditContent] = useState("");
  const [editMemo, setEditMemo] = useState("");
  const [editSaving, setEditSaving] = useState(false);

  const groupedLogs = useMemo(() => groupByDate(logs), [logs]);

  async function reload(): Promise<void> {
    try {
      const result = await apiClient.listStudyLogs(qualification.id);
      setLogs(result.items);
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  useEffect(() => {
    void reload();
  }, [qualification.id]);

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
        qualificationId: qualification.id,
        date,
        hours: parsedHours,
        content,
        memo: memo.trim() === "" ? null : memo,
      });

      setContent("");
      setMemo("");
      await reload();
      await props.onChanged();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    } finally {
      setSaving(false);
    }
  }

  function startEdit(log: StudyLog): void {
    setError(null);
    setEditingId(log.id);
    setEditDate(log.date);
    setEditHours(String(log.hours));
    setEditContent(log.content);
    setEditMemo(log.memo ?? "");
  }

  function cancelEdit(): void {
    setEditingId(null);
  }

  async function submitEdit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!editingId) {
      return;
    }
    setError(null);

    const parsedHours = Number(editHours);
    if (
      Number.isNaN(parsedHours) ||
      parsedHours <= 0 ||
      Math.round(parsedHours * 100) % 25 !== 0
    ) {
      setError("時間は 0.25 刻みで入力してください");
      return;
    }

    setEditSaving(true);
    try {
      await apiClient.updateStudyLog(editingId, {
        date: editDate,
        hours: parsedHours,
        content: editContent,
        memo: editMemo.trim() === "" ? null : editMemo,
      });
      setEditingId(null);
      await reload();
      await props.onChanged();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    } finally {
      setEditSaving(false);
    }
  }

  async function deleteLog(log: StudyLog): Promise<void> {
    if (!window.confirm(`${log.date} の記録「${log.content}」を削除しますか？`)) {
      return;
    }
    setError(null);
    try {
      await apiClient.deleteStudyLog(log.id);
      if (editingId === log.id) {
        setEditingId(null);
      }
      await reload();
      await props.onChanged();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  return (
    <section className="studyLogPanel">
      <h3>学習記録</h3>

      {isClosed ? (
        <p className="hintText">クローズ済みの資格には記録を追加できません。</p>
      ) : (
        <form className="studyForm" onSubmit={onSubmit}>
          <div className="twoCols">
            <label className="field">
              <span className="fieldLabel">日付</span>
              <input type="date" value={date} onChange={(event) => setDate(event.target.value)} required />
            </label>
            <label className="field">
              <span className="fieldLabel">時間</span>
              <input
                type="number"
                step="0.25"
                min="0.25"
                value={hours}
                onChange={(event) => setHours(event.target.value)}
                required
              />
            </label>
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
          <button type="submit" disabled={saving}>
            {saving ? "保存中..." : "記録を追加"}
          </button>
        </form>
      )}

      {error && <p className="errorText">{error}</p>}

      <ul className="studyLogList">
        {groupedLogs.length === 0 && <li className="empty">まだ記録がありません。</li>}
        {groupedLogs.map((group) => (
          <li key={group.date}>
            <p className="dayHead">
              <strong>{group.date}</strong>
              <span className="dayTotal">計 {group.totalHours}h</span>
            </p>
            <ul className="dayItems">
              {group.items.map((log) =>
                editingId === log.id ? (
                  <li key={log.id}>
                    <form className="studyEditForm" onSubmit={submitEdit}>
                      <div className="twoCols">
                        <label className="field">
                          <span className="fieldLabel">日付</span>
                          <input
                            type="date"
                            value={editDate}
                            onChange={(event) => setEditDate(event.target.value)}
                            required
                          />
                        </label>
                        <label className="field">
                          <span className="fieldLabel">時間</span>
                          <input
                            type="number"
                            step="0.25"
                            min="0.25"
                            value={editHours}
                            onChange={(event) => setEditHours(event.target.value)}
                            required
                          />
                        </label>
                      </div>
                      <input
                        value={editContent}
                        onChange={(event) => setEditContent(event.target.value)}
                        placeholder="やったこと"
                        required
                      />
                      <textarea
                        value={editMemo}
                        onChange={(event) => setEditMemo(event.target.value)}
                        placeholder="メモ (任意)"
                        rows={3}
                      />
                      <div className="studyEditActions">
                        <button type="submit" disabled={editSaving}>
                          {editSaving ? "保存中..." : "保存"}
                        </button>
                        <button type="button" onClick={cancelEdit} disabled={editSaving}>
                          キャンセル
                        </button>
                      </div>
                    </form>
                  </li>
                ) : (
                  <li key={log.id}>
                    <p className="itemHours">{log.hours}h</p>
                    <p>{log.content}</p>
                    {log.memo && <p className="memo">{log.memo}</p>}
                    <div className="itemActions">
                      <button type="button" className="linkButton" onClick={() => startEdit(log)}>
                        編集
                      </button>
                      <button
                        type="button"
                        className="linkButton danger"
                        onClick={() => void deleteLog(log)}
                      >
                        削除
                      </button>
                    </div>
                  </li>
                )
              )}
            </ul>
          </li>
        ))}
      </ul>
    </section>
  );
}
