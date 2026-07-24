import { useEffect, useMemo, useState } from "react";

import { CalendarPanel } from "./components/CalendarPanel";
import { MilestonePanel } from "./components/MilestonePanel";
import { PinLogin } from "./components/PinLogin";
import { QualificationPanel } from "./components/QualificationPanel";
import { StudyLogPanel } from "./components/StudyLogPanel";
import { TabNav, type TabKey } from "./components/TabNav";
import { apiClient } from "./lib/apiClient";
import type { Qualification } from "./types/api";
import "./App.css";

export function App(): JSX.Element {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("calendar");
  const [qualifications, setQualifications] = useState<Qualification[]>([]);
  const [error, setError] = useState<string | null>(null);

  const activeQualifications = useMemo(
    () => qualifications.filter((item) => item.status === "active"),
    [qualifications]
  );

  async function refreshQualifications(): Promise<void> {
    setError(null);
    try {
      const result = await apiClient.listQualifications(true);
      setQualifications(result.items);
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
  }

  useEffect(() => {
    async function bootstrap(): Promise<void> {
      try {
        await apiClient.session();
        setIsAuthenticated(true);
        await refreshQualifications();
      } catch (errorValue) {
        if (!apiClient.isUnauthorized(errorValue)) {
          setError(apiClient.errorMessage(errorValue));
        }
        setIsAuthenticated(false);
      } finally {
        setIsCheckingSession(false);
      }
    }

    void bootstrap();
  }, []);

  async function handleLoginSuccess(): Promise<void> {
    setIsAuthenticated(true);
    await refreshQualifications();
  }

  async function handleLogout(): Promise<void> {
    setError(null);
    try {
      await apiClient.logout();
    } catch (errorValue) {
      setError(apiClient.errorMessage(errorValue));
    }
    setIsAuthenticated(false);
    setQualifications([]);
  }

  if (isCheckingSession) {
    return (
      <main className="loadingScreen">
        <p>セッションを確認しています...</p>
      </main>
    );
  }

  if (!isAuthenticated) {
    return <PinLogin onSuccess={() => void handleLoginSuccess()} />;
  }

  return (
    <main className="appShell">
      <header className="appTop">
        <div>
          <p className="appEyebrow">LEARNLOG</p>
          <h1>Study Dashboard</h1>
          <p className="appSub">学習を記録して、積み上げを可視化する</p>
        </div>
        <button type="button" className="logoutButton" onClick={() => void handleLogout()}>
          ログアウト
        </button>
      </header>

      <TabNav current={activeTab} onChange={setActiveTab} />

      {error && <p className="errorText">{error}</p>}

      {activeTab === "calendar" && <CalendarPanel />}
      {activeTab === "qualifications" && (
        <QualificationPanel
          qualifications={qualifications}
          onRefresh={refreshQualifications}
        />
      )}
      {activeTab === "study" && (
        <StudyLogPanel
          qualifications={qualifications}
          onCreated={refreshQualifications}
        />
      )}
      {activeTab === "milestones" && (
        <MilestonePanel
          qualifications={activeQualifications}
          onChanged={refreshQualifications}
        />
      )}
    </main>
  );
}
