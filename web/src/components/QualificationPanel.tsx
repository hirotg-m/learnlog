import { FormEvent, useMemo, useState } from "react";

import { apiClient } from "../lib/apiClient";
import type { Qualification } from "../types/api";
import "./QualificationPanel.css";

type QualificationPanelProps = {
  qualifications: Qualification[];
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
  const [name, setName] = useState("");
  const [abbreviation, setAbbreviation] = useState("");
  const [color, setColor] = useState<(typeof colors)[number]>("blue");
  const [status, setStatus] = useState<"active" | "closed">("active");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const activeCount = useMemo(
    () => props.qualifications.filter((item) => item.status === "active").length,
    [props.qualifications]
  );

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
      setStatus("active");
      await props.onRefresh();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="panel qualificationPanel">
      <header>
        <h2>資格一覧</h2>
        <p>学習中 {activeCount} 件 / 全 {props.qualifications.length} 件</p>
      </header>

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
          <select value={status} onChange={(event) => setStatus(event.target.value as "active" | "closed")}>
            <option value="active">学習中</option>
            <option value="closed">クローズ</option>
          </select>
        </div>
        <button type="submit" disabled={saving}>
          {saving ? "保存中..." : "資格を追加"}
        </button>
      </form>

      {error && <p className="errorText">{error}</p>}

      <ul className="qualificationList">
        {props.qualifications.map((item) => (
          <li key={item.id}>
            <p className="titleLine">
              <strong>{item.abbreviation ?? item.name}</strong>
              <span className={item.status === "active" ? "active" : "closed"}>
                {item.status === "active" ? "学習中" : "クローズ"}
              </span>
            </p>
            <p className="nameLine">{item.name}</p>
            <p className="statsLine">
              {item.totalHours ?? 0}h / {item.studyLogCount ?? 0} セッション / 期限超過 {item.overdueMilestoneCount ?? 0} 件
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}