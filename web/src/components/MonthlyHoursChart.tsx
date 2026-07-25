import { useMemo, useState } from "react";

import { getQualificationColor } from "../lib/colors";
import { formatQualificationName } from "../lib/qualificationLabel";
import type { CalendarMonth } from "../types/api";
import "./MonthlyHoursChart.css";

type MonthlyHoursChartProps = {
  monthData: CalendarMonth | null;
};

type Segment = {
  key: string;
  label: string;
  color: string;
  hours: number;
};

const OTHER_CAP = 6;

function formatHours(hours: number): string {
  return Number.isInteger(hours) ? `${hours}` : hours.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}

export function MonthlyHoursChart(props: MonthlyHoursChartProps): JSX.Element {
  const [activeKey, setActiveKey] = useState<string | null>(null);

  const segments = useMemo<Segment[]>(() => {
    const totals = new Map<string, Segment>();
    for (const day of props.monthData?.days ?? []) {
      for (const item of day.items) {
        const existing = totals.get(item.qualificationId);
        if (existing) {
          existing.hours += item.hours;
        } else {
          totals.set(item.qualificationId, {
            key: item.qualificationId,
            label: formatQualificationName({
              name: item.qualificationName,
              abbreviation: item.abbreviation,
            }),
            color: item.color,
            hours: item.hours,
          });
        }
      }
    }

    const sorted = [...totals.values()].sort((a, b) => b.hours - a.hours);
    if (sorted.length <= OTHER_CAP) {
      return sorted;
    }
    const head = sorted.slice(0, OTHER_CAP - 1);
    const tailHours = sorted
      .slice(OTHER_CAP - 1)
      .reduce((sum, item) => sum + item.hours, 0);
    return [...head, { key: "__other__", label: "その他", color: "gray", hours: tailHours }];
  }, [props.monthData]);

  const totalHours = useMemo(
    () => segments.reduce((sum, item) => sum + item.hours, 0),
    [segments]
  );

  const title = props.monthData
    ? `${props.monthData.year}年${props.monthData.month}月の学習時間`
    : "月間学習時間";

  return (
    <section className="monthlyHoursChart">
      <h3>{title}</h3>

      {totalHours === 0 ? (
        <p className="hintText">この月の記録はまだありません。</p>
      ) : (
        <>
          <p className="chartTotal">合計 {formatHours(totalHours)}h</p>

          <div className="stackedBar">
            {segments.map((segment) => (
              <button
                key={segment.key}
                type="button"
                className={`segment${segment.key === activeKey ? " isActive" : ""}`}
                style={{
                  flexGrow: segment.hours,
                  backgroundColor: getQualificationColor(segment.color),
                }}
                title={`${segment.label}: ${formatHours(segment.hours)}h`}
                aria-label={`${segment.label}: ${formatHours(segment.hours)}時間`}
                onPointerEnter={() => setActiveKey(segment.key)}
                onPointerLeave={() => setActiveKey(null)}
                onFocus={() => setActiveKey(segment.key)}
                onBlur={() => setActiveKey(null)}
              />
            ))}
          </div>

          <ul className="chartLegend">
            {segments.map((segment) => (
              <li
                key={segment.key}
                className={segment.key === activeKey ? "isActive" : ""}
                onPointerEnter={() => setActiveKey(segment.key)}
                onPointerLeave={() => setActiveKey(null)}
              >
                <span
                  className="legendSwatch"
                  style={{ backgroundColor: getQualificationColor(segment.color) }}
                />
                <span className="legendLabel">{segment.label}</span>
                <span className="legendValue">
                  {formatHours(segment.hours)}h ({Math.round((segment.hours / totalHours) * 100)}%)
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
