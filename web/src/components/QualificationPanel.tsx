import { FormEvent, MouseEvent as ReactMouseEvent, useMemo, useState } from "react";

import { apiClient } from "../lib/apiClient";
import { getQualificationColor } from "../lib/colors";
import type { Qualification } from "../types/api";
import "./QualificationPanel.css";

type QualificationPanelProps = {
  qualifications: Qualification[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRefresh: () => Promise<void>;
};

const colors = [
  "red",
  "orange",
  "yellow",
  "green",
  "teal",
  "blue",
  "indigo",
  "pink",
  "brown",
  "gray",
] as const;

export function QualificationPanel(props: QualificationPanelProps): JSX.Element {
  const [showAddForm, setShowAddForm] = useState(false);
  const [name, setName] = useState("");
  const [abbreviation, setAbbreviation] = useState("");
  const [color, setColor] = useState<(typeof colors)[number]>("blue");
  const [status, setStatus] = useState<"open" | "close">("open");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editAbbreviation, setEditAbbreviation] = useState("");
  const [editColor, setEditColor] = useState<(typeof colors)[number]>("blue");
  const [editStatus, setEditStatus] = useState<"open" | "close">("open");
  const [editSaving, setEditSaving] = useState(false);

  const openCount = useMemo(
    () => props.qualifications.filter((item) => item.status === "open").length,
    [props.qualifications]
  );

  const sortedQualifications = useMemo(() => {
    return [...props.qualifications].sort((left, right) => {
      if (left.status !== right.status) {
        return left.status === "close" ? 1 : -1;
      }
      // 直近に学習記録があるものを上に、記録が無いものは下に
      if (left.lastStudiedAt === right.lastStudiedAt) {
        return 0;
      }
      if (left.lastStudiedAt === null) {
        return 1;
      }
      if (right.lastStudiedAt === null) {
        return -1;
      }
      return right.lastStudiedAt.localeCompare(left.lastStudiedAt);
    });
  }, [props.qualifications]);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setSaving(true);

    try {
      await apiClient.createQualification({
        name,
        abbreviation: abbreviation.trim() === "" ? null : abbreviation,
        color,
        status,
      });
      setName("");
      setAbbreviation("");
      setColor("blue");
      setStatus("open");
      setShowAddForm(false);
      await props.onRefresh();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    } finally {
      setSaving(false);
    }
  }

  function startEdit(item: Qualification): void {
    setError(null);
    setEditingId(item.id);
    setEditName(item.name);
    setEditAbbreviation(item.abbreviation ?? "");
    setEditColor(item.color as (typeof colors)[number]);
    setEditStatus(item.status);
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
      await apiClient.updateQualification(editingId, {
        name: editName,
        abbreviation: editAbbreviation.trim() === "" ? null : editAbbreviation,
        color: editColor,
        status: editStatus,
      });
      setEditingId(null);
      await props.onRefresh();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    } finally {
      setEditSaving(false);
    }
  }

  async function toggleStatus(event: ReactMouseEvent, item: Qualification): Promise<void> {
    event.stopPropagation();
    setError(null);
    try {
      await apiClient.updateQualification(item.id, {
        status: item.status === "open" ? "close" : "open",
      });
      await props.onRefresh();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  function onStartEditClick(event: ReactMouseEvent, item: Qualification): void {
    event.stopPropagation();
    startEdit(item);
  }

  async function deleteQualification(event: ReactMouseEvent, item: Qualification): Promise<void> {
    event.stopPropagation();
    if (
      !window.confirm(
        `「${item.name}」を削除しますか？\n関連する学習記録・マイルストーンも全て削除されます。`
      )
    ) {
      return;
    }
    setError(null);
    try {
      await apiClient.deleteQualification(item.id);
      if (editingId === item.id) {
        setEditingId(null);
      }
      await props.onRefresh();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  return (
    <section className="panel qualificationPanel">
      <header>
        <h2>資格一覧</h2>
        <p>学習中 {openCount} 件 / 全 {props.qualifications.length} 件</p>
      </header>

      {showAddForm ? (
        <form className="qualificationForm" onSubmit={onSubmit}>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="資格名"
            required
          />
          <input
            value={abbreviation}
            onChange={(event) => setAbbreviation(event.target.value)}
            placeholder="略称 (任意)"
          />
          <div className="inlineFields">
            <select value={color} onChange={(event) => setColor(event.target.value as (typeof colors)[number])}>
              {colors.map((item) => (
                <option value={item} key={item}>
                  {item}
                </option>
              ))}
            </select>
            <select value={status} onChange={(event) => setStatus(event.target.value as "open" | "close")}>
              <option value="open">学習中</option>
              <option value="close">学習終わり</option>
            </select>
          </div>
          <div className="inlineFields">
            <button type="submit" disabled={saving}>
              {saving ? "保存中..." : "資格を追加"}
            </button>
            <button type="button" className="secondaryButton" onClick={() => setShowAddForm(false)}>
              キャンセル
            </button>
          </div>
        </form>
      ) : (
        <button type="button" className="addToggleButton" onClick={() => setShowAddForm(true)}>
          + 資格を追加
        </button>
      )}

      {error && <p className="errorText">{error}</p>}

      <ul className="qualificationList">
        {sortedQualifications.map((item) =>
          editingId === item.id ? (
            <li key={item.id}>
              <form className="qualificationEditForm" onSubmit={submitEdit}>
                <input
                  value={editName}
                  onChange={(event) => setEditName(event.target.value)}
                  placeholder="資格名"
                  required
                />
                <input
                  value={editAbbreviation}
                  onChange={(event) => setEditAbbreviation(event.target.value)}
                  placeholder="略称 (任意)"
                />
                <div className="inlineFields">
                  <select
                    value={editColor}
                    onChange={(event) =>
                      setEditColor(event.target.value as (typeof colors)[number])
                    }
                  >
                    {colors.map((colorItem) => (
                      <option value={colorItem} key={colorItem}>
                        {colorItem}
                      </option>
                    ))}
                  </select>
                  <select
                    value={editStatus}
                    onChange={(event) =>
                      setEditStatus(event.target.value as "open" | "close")
                    }
                  >
                    <option value="open">学習中</option>
                    <option value="close">学習終わり</option>
                  </select>
                </div>
                <div className="qualificationEditActions">
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
            <li
              key={item.id}
              className={`selectable${item.id === props.selectedId ? " isSelected" : ""}`}
              onClick={() => props.onSelect(item.id)}
            >
              <p className="titleLine">
                <strong
                  className="colorChip"
                  style={{ backgroundColor: getQualificationColor(item.color) }}
                >
                  {item.abbreviation ?? item.name}
                </strong>
                <button
                  type="button"
                  className={item.status === "open" ? "open" : "close"}
                  onClick={(event) => void toggleStatus(event, item)}
                >
                  {item.status === "open" ? "学習中" : "学習終わり"}
                </button>
              </p>
              <p
                className="nameLine colorChip"
                style={{ backgroundColor: getQualificationColor(item.color) }}
              >
                {item.name}
              </p>
              <p className="statsLine">
                {item.totalHours ?? 0}h / {item.studyLogCount ?? 0} セッション
              </p>
              <div className="qualificationActions">
                <button
                  type="button"
                  className="linkButton"
                  onClick={(event) => onStartEditClick(event, item)}
                >
                  編集
                </button>
                <button
                  type="button"
                  className="linkButton danger"
                  onClick={(event) => void deleteQualification(event, item)}
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