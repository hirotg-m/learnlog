import { useEffect, useState } from "react";

import { CalendarPanel } from "./components/CalendarPanel";
import { PinLogin } from "./components/PinLogin";
import { QualificationsView } from "./components/QualificationsView";
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
        <p className="appEyebrow">LEARNLOG</p>
        <div className="appTitleRow">
          <h1>Study Dashboard</h1>
          <button type="button" className="logoutButton" onClick={() => void handleLogout()}>
            ログアウト
          </button>
        </div>
        <p className="appSub">学習を記録して、積み上げを可視化する</p>
      </header>

      <TabNav current={activeTab} onChange={setActiveTab} />

      {error && <p className="errorText">{error}</p>}

      {activeTab === "calendar" && <CalendarPanel />}
      {activeTab === "qualifications" && (
        <QualificationsView qualifications={qualifications} onRefresh={refreshQualifications} />
      )}
    </main>
  );
}
