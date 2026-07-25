import { useEffect, useMemo, useState } from "react";

import { apiClient } from "../lib/apiClient";
import { getQualificationColor } from "../lib/colors";
import type { CalendarDayDetail, CalendarMonth } from "../types/api";
import { MonthlyHoursChart } from "./MonthlyHoursChart";
import "./CalendarPanel.css";

const weekLabels = ["日", "月", "火", "水", "木", "金", "土"];

function pad2(value: number): string {
  return value.toString().padStart(2, "0");
}

export function CalendarPanel(): JSX.Element {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [monthData, setMonthData] = useState<CalendarMonth | null>(null);
  const [dayDetail, setDayDetail] = useState<CalendarDayDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMonth(): Promise<void> {
      setError(null);
      try {
        const data = await apiClient.getCalendarMonth(year, month);
        setMonthData(data);
      } catch (errorValue) {
        setError(apiClient.errorMessage(errorValue));
      }
    }

    void loadMonth();
  }, [year, month]);

  const mapByDate = useMemo(() => {
    const map = new Map<string, CalendarMonth["days"][number]>();
    for (const item of monthData?.days ?? []) {
      map.set(item.date, item);
    }
    return map;
  }, [monthData]);

  const firstWeekday = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();

  async function onDateClick(day: number): Promise<void> {
    const date = `${year}-${pad2(month)}-${pad2(day)}`;
    setError(null);
    try {
      const detail = await apiClient.getCalendarDay(date);
      setDayDetail(detail);
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  function moveMonth(step: number): void {
    const moved = new Date(year, month - 1 + step, 1);
    setYear(moved.getFullYear());
    setMonth(moved.getMonth() + 1);
    setDayDetail(null);
  }

  return (
    <section className="panel calendarPanel">
      <header className="calendarHeader">
        <button type="button" onClick={() => moveMonth(-1)}>
          ←
        </button>
        <h2>
          {year}年 {month}月
        </h2>
        <button type="button" onClick={() => moveMonth(1)}>
          →
        </button>
      </header>

      <div className="calendarGrid weekLabels">
        {weekLabels.map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>

      <div className="calendarGrid days">
        {Array.from({ length: firstWeekday }).map((_, index) => (
          <div key={`empty-${index}`} className="empty" />
        ))}
        {Array.from({ length: daysInMonth }).map((_, index) => {
          const day = index + 1;
          const date = `${year}-${pad2(month)}-${pad2(day)}`;
          const items = mapByDate.get(date)?.items ?? [];

          return (
            <button key={date} type="button" onClick={() => void onDateClick(day)}>
              <span>{day}</span>
              <div className="dotRow">
                {items.slice(0, 4).map((item) => (
                  <i
                    key={`${date}-${item.qualificationId}`}
                    style={{ backgroundColor: getQualificationColor(item.color) }}
                  />
                ))}
              </div>
            </button>
          );
        })}
      </div>

      {error && <p className="errorText">{error}</p>}

      <section className="dayDetail">
        <h3>{dayDetail ? `${dayDetail.date} の記録` : "日付をタップしてください"}</h3>
        <ul>
          {(dayDetail?.items ?? []).map((item) => (
            <li key={item.studyLogId}>
              <p className="detailHead">
                <span
                  className="colorDot"
                  style={{ backgroundColor: getQualificationColor(item.color) }}
                />
                {item.abbreviation ?? item.qualificationName} / {item.hours}h
              </p>
              <p>{item.content}</p>
              {item.memo && <p className="memo">{item.memo}</p>}
            </li>
          ))}
        </ul>
      </section>

      <MonthlyHoursChart monthData={monthData} />
    </section>
  );
}