import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiClient } from "../lib/apiClient";
import type { Milestone, Qualification } from "../types/api";
import "./MilestonePanel.css";

type MilestonePanelProps = {
  qualifications: Qualification[];
  onChanged: () => Promise<void>;
};

function toDateInputValue(value: string | null): string {
  if (!value) {
    return "";
  }
  return value;
}

export function MilestonePanel(props: MilestonePanelProps): JSX.Element {
  const [qualificationId, setQualificationId] = useState("");
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [items, setItems] = useState<Milestone[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasQualifications = props.qualifications.length > 0;

  useEffect(() => {
    if (!qualificationId && props.qualifications.length > 0) {
      setQualificationId(props.qualifications[0].id);
    }
  }, [qualificationId, props.qualifications]);

  async function reload(): Promise<void> {
    setError(null);
    try {
      const result = await apiClient.listMilestones(qualificationId || undefined);
      setItems(result.items);
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  useEffect(() => {
    void reload();
  }, [qualificationId]);

  const sortedItems = useMemo(() => {
    return [...items].sort((left, right) => {
      if (left.isAchieved !== right.isAchieved) {
        return left.isAchieved ? 1 : -1;
      }
      if (!left.dueDate && !right.dueDate) {
        return 0;
      }
      if (!left.dueDate) {
        return 1;
      }
      if (!right.dueDate) {
        return -1;
      }
      return left.dueDate.localeCompare(right.dueDate);
    });
  }, [items]);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!qualificationId) {
      setError("資格を選択してください");
      return;
    }
    setError(null);
    setSaving(true);

    try {
      await apiClient.createMilestone({
        qualificationId,
        title,
        dueDate: dueDate === "" ? null : dueDate,
        isAchieved: false,
      });
      setTitle("");
      setDueDate("");
      await reload();
      await props.onChanged();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    } finally {
      setSaving(false);
    }
  }

  async function toggleAchieved(item: Milestone): Promise<void> {
    setError(null);
    try {
      await apiClient.updateMilestone(item.id, {
        isAchieved: !item.isAchieved,
      });
      await reload();
      await props.onChanged();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  function getQualificationLabel(targetId: string): string {
    const found = props.qualifications.find((item) => item.id === targetId);
    if (!found) {
      return "不明な資格";
    }
    return found.abbreviation ?? found.name;
  }

  return (
    <section className="panel milestonePanel">
      <h2>マイルストーン管理</h2>

      <form className="milestoneForm" onSubmit={onSubmit}>
        <select
          value={qualificationId}
          onChange={(event) => setQualificationId(event.target.value)}
          required
          disabled={!hasQualifications}
        >
          {props.qualifications.map((qualification) => (
            <option key={qualification.id} value={qualification.id}>
              {qualification.abbreviation ?? qualification.name}
            </option>
          ))}
        </select>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="目標タイトル"
          required
        />
        <input
          type="date"
          value={dueDate}
          onChange={(event) => setDueDate(event.target.value)}
        />
        <button type="submit" disabled={saving || !hasQualifications}>
          {saving ? "保存中..." : "マイルストーンを追加"}
        </button>
      </form>

      {!hasQualifications && (
        <p className="hintText">学習中の資格がありません。資格タブから追加してください。</p>
      )}

      {error && <p className="errorText">{error}</p>}

      <ul className="milestoneList">
        {sortedItems.map((item) => (
          <li key={item.id}>
            <div className="milestoneHead">
              <strong>{item.title}</strong>
              <button
                type="button"
                className={item.isAchieved ? "badge achieved" : "badge pending"}
                onClick={() => void toggleAchieved(item)}
              >
                {item.isAchieved ? "達成" : "未達成"}
              </button>
            </div>
            <p className="metaLine">
              {getQualificationLabel(item.qualificationId)}
              {item.dueDate ? ` / 期限 ${toDateInputValue(item.dueDate)}` : " / 期限なし"}
              {item.isOverdue && !item.isAchieved ? " / 期限超過" : ""}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
