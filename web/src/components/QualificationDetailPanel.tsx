import { getQualificationColor } from "../lib/colors";
import { formatQualificationName } from "../lib/qualificationLabel";
import type { Qualification } from "../types/api";
import { MilestonePanel } from "./MilestonePanel";
import { StudyLogPanel } from "./StudyLogPanel";
import "./QualificationDetailPanel.css";

type QualificationDetailPanelProps = {
  qualification: Qualification;
  onChanged: () => Promise<void>;
};

export function QualificationDetailPanel(props: QualificationDetailPanelProps): JSX.Element {
  const { qualification } = props;

  return (
    <section className="panel qualificationDetailPanel">
      <header className="detailHeader">
        <h2
          className="colorChip"
          style={{ backgroundColor: getQualificationColor(qualification.color) }}
        >
          {formatQualificationName(qualification)}
        </h2>
        <p className="detailStats">
          {qualification.totalHours ?? 0}h / {qualification.studyLogCount ?? 0} セッション
        </p>
      </header>

      <div className="detailBody">
        <StudyLogPanel qualification={qualification} onChanged={props.onChanged} />
        <MilestonePanel qualification={qualification} onChanged={props.onChanged} />
      </div>
    </section>
  );
}
