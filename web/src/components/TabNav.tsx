import "./TabNav.css";

export type TabKey = "calendar" | "qualifications" | "study" | "milestones";

type TabNavProps = {
  current: TabKey;
  onChange: (tab: TabKey) => void;
};

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: "calendar", label: "カレンダー" },
  { key: "qualifications", label: "資格" },
  { key: "study", label: "記録" },
  { key: "milestones", label: "目標" },
];

export function TabNav(props: TabNavProps): JSX.Element {
  return (
    <nav className="tabNav" aria-label="メインタブ">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          className={props.current === tab.key ? "isActive" : ""}
          type="button"
          onClick={() => props.onChange(tab.key)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}