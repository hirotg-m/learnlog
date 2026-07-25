import { useEffect, useState } from "react";

import type { Qualification } from "../types/api";
import { QualificationDetailPanel } from "./QualificationDetailPanel";
import { QualificationPanel } from "./QualificationPanel";
import "./QualificationsView.css";

type QualificationsViewProps = {
  qualifications: Qualification[];
  onRefresh: () => Promise<void>;
};

export function QualificationsView(props: QualificationsViewProps): JSX.Element {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (selectedId && !props.qualifications.some((item) => item.id === selectedId)) {
      setSelectedId(null);
    }
  }, [props.qualifications, selectedId]);

  const selected = props.qualifications.find((item) => item.id === selectedId) ?? null;

  return (
    <div className={`qualificationsView${selected ? " hasSelection" : ""}`}>
      <QualificationPanel
        qualifications={props.qualifications}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onRefresh={props.onRefresh}
      />
      {selected ? (
        <div className="qualificationDetailColumn">
          <button
            type="button"
            className="backToListButton"
            onClick={() => setSelectedId(null)}
          >
            ← 資格一覧に戻る
          </button>
          <QualificationDetailPanel qualification={selected} onChanged={props.onRefresh} />
        </div>
      ) : (
        <section className="panel qualificationDetailEmpty">
          <p>
            資格を選択すると、その資格の学習記録とマイルストーンを表示します。
          </p>
        </section>
      )}
    </div>
  );
}
