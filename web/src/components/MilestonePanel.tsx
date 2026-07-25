import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiClient } from "../lib/apiClient";
import type { Milestone, Qualification } from "../types/api";
import "./MilestonePanel.css";

type MilestonePanelProps = {
  qualification: Qualification;
  onChanged: () => Promise<void>;
};

function toDateInputValue(value: string | null): string {
  if (!value) {
    return "";
  }
  return value;
}

export function MilestonePanel(props: MilestonePanelProps): JSX.Element {
  const { qualification } = props;

  const [title, setTitle] = useState("");
  const [plannedDate, setPlannedDate] = useState("");
  const [items, setItems] = useState<Milestone[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editPlannedDate, setEditPlannedDate] = useState("");
  const [editCompletedDate, setEditCompletedDate] = useState("");
  const [editSaving, setEditSaving] = useState(false);

  async function reload(): Promise<void> {
    setError(null);
    try {
      const result = await apiClient.listMilestones(qualification.id);
      setItems(result.items);
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  useEffect(() => {
    void reload();
  }, [qualification.id]);

  const sortedItems = useMemo(() => {
    return [...items].sort((left, right) => {
      if (left.status !== right.status) {
        return left.status === "close" ? 1 : -1;
      }
      if (!left.plannedDate && !right.plannedDate) {
        return 0;
      }
      if (!left.plannedDate) {
        return 1;
      }
      if (!right.plannedDate) {
        return -1;
      }
      return left.plannedDate.localeCompare(right.plannedDate);
    });
  }, [items]);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setSaving(true);

    try {
      await apiClient.createMilestone({
        qualificationId: qualification.id,
        title,
        plannedDate: plannedDate === "" ? null : plannedDate,
      });
      setTitle("");
      setPlannedDate("");
      await reload();
      await props.onChanged();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    } finally {
      setSaving(false);
    }
  }

  async function toggleStatus(item: Milestone): Promise<void> {
    setError(null);
    try {
      await apiClient.updateMilestone(item.id, {
        status: item.status === "close" ? "open" : "close",
      });
      await reload();
      await props.onChanged();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  function startEdit(item: Milestone): void {
    setError(null);
    setEditingId(item.id);
    setEditTitle(item.title);
    setEditPlannedDate(toDateInputValue(item.plannedDate));
    setEditCompletedDate(toDateInputValue(item.completedDate));
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
    setEditSaving(true);

    try {
      await apiClient.updateMilestone(editingId, {
        title: editTitle,
        plannedDate: editPlannedDate === "" ? null : editPlannedDate,
        completedDate: editCompletedDate === "" ? null : editCompletedDate,
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

  async function deleteMilestone(item: Milestone): Promise<void> {
    if (!window.confirm(`「${item.title}」を削除しますか？`)) {
      return;
    }
    setError(null);
    try {
      await apiClient.deleteMilestone(item.id);
      if (editingId === item.id) {
        setEditingId(null);
      }
      await reload();
      await props.onChanged();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  return (
    <section className="milestonePanel">
      <h3>マイルストーン</h3>

      <form className="milestoneForm" onSubmit={onSubmit}>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="目標タイトル"
          required
        />
        <input
          type="date"
          value={plannedDate}
          onChange={(event) => setPlannedDate(event.target.value)}
        />
        <button type="submit" disabled={saving}>
          {saving ? "保存中..." : "マイルストーンを追加"}
        </button>
      </form>

      {error && <p className="errorText">{error}</p>}

      <ul className="milestoneList">
        {sortedItems.length === 0 && <li className="empty">まだマイルストーンがありません。</li>}
        {sortedItems.map((item) =>
          editingId === item.id ? (
            <li key={item.id}>
              <form className="milestoneEditForm" onSubmit={submitEdit}>
                <input
                  value={editTitle}
                  onChange={(event) => setEditTitle(event.target.value)}
                  placeholder="目標タイトル"
                  required
                />
                <label className="fieldLabel">
                  計画日
                  <input
                    type="date"
                    value={editPlannedDate}
                    onChange={(event) => setEditPlannedDate(event.target.value)}
                  />
                </label>
                <label className="fieldLabel">
                  完了日
                  <input
                    type="date"
                    value={editCompletedDate}
                    onChange={(event) => setEditCompletedDate(event.target.value)}
                  />
                </label>
                <div className="milestoneEditActions">
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
            <li key={item.id}>
              <div className="milestoneHead">
                <strong>{item.title}</strong>
                <button
                  type="button"
                  className={item.status === "close" ? "badge achieved" : "badge pending"}
                  onClick={() => void toggleStatus(item)}
                >
                  {item.status === "close" ? "完了" : "未完了"}
                </button>
              </div>
              <p className="metaLine">
                {item.plannedDate ? `計画日 ${toDateInputValue(item.plannedDate)}` : "計画日なし"}
                {item.completedDate ? ` / 完了日 ${toDateInputValue(item.completedDate)}` : ""}
                {item.isOverdue ? " / 期限超過" : ""}
              </p>
              <div className="milestoneActions">
                <button type="button" className="linkButton" onClick={() => startEdit(item)}>
                  編集
                </button>
                <button
                  type="button"
                  className="linkButton danger"
                  onClick={() => void deleteMilestone(item)}
                >
                  削除
                </button>
              </div>
            </li>
          )
        )}
      </ul>
    </section>
  );
}
