import "./TabNav.css";

export type TabKey = "calendar" | "qualifications";

type TabNavProps = {
  current: TabKey;
  onChange: (tab: TabKey) => void;
};

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: "calendar", label: "カレンダー" },
  { key: "qualifications", label: "資格" },
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