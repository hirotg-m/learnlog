import type {
  ApiErrorBody,
  CalendarDayDetail,
  CalendarMonth,
  Milestone,
  MilestoneStatus,
  Qualification,
  QualificationStatus,
  StudyLog,
} from "../types/api";

class ApiError extends Error {
  status: number;
  retryAfterSeconds?: number;

  constructor(status: number, message: string, retryAfterSeconds?: number) {
    super(message);
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

// バックエンドが返す detail 文字列 (英語) を、画面にそのまま出しても違和感のない日本語に変換する
const KNOWN_DETAIL_MESSAGES: Record<string, string> = {
  "invalid pin": "PINが正しくありません",
  "login locked": "PIN入力に複数回失敗したため、しばらくログインできません",
  unauthorized: "ログインが必要です",
  "session expired": "セッションの有効期限が切れました。再度ログインしてください",
  "qualification not found": "資格が見つかりませんでした",
  "milestone not found": "マイルストーンが見つかりませんでした",
  "study log not found": "学習記録が見つかりませんでした",
  "invalid status": "指定されたステータスが不正です",
  "invalid color": "指定された色が不正です",
  "closed qualification cannot accept new logs": "学習終わりの資格には記録を追加できません",
  "date range must be within 12 months": "日付の範囲は12か月以内で指定してください",
};

function getEndpoint(): string {
  const endpoint = import.meta.env.VITE_API_ENDPOINT;
  if (!endpoint) {
    throw new Error("VITE_API_ENDPOINT is required");
  }
  return endpoint;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const endpoint = getEndpoint();
  const response = await fetch(`${endpoint}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `request failed: ${response.status}`;
    try {
      const body = (await response.json()) as ApiErrorBody;
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      detail = `request failed: ${response.status}`;
    }
    const retryAfterHeader = response.headers.get("Retry-After");
    const retryAfterSeconds = retryAfterHeader ? Number(retryAfterHeader) : undefined;
    throw new ApiError(
      response.status,
      detail,
      retryAfterSeconds !== undefined && Number.isFinite(retryAfterSeconds)
        ? retryAfterSeconds
        : undefined
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

type SessionResponse = {
  authenticated: boolean;
  expiresAt: string;
};

type LoginResponse = {
  session: {
    expiresAt: string;
  };
};

export const apiClient = {
  isUnauthorized(error: unknown): boolean {
    return error instanceof ApiError && error.status === 401;
  },
  retryAfterSeconds(error: unknown): number | undefined {
    return error instanceof ApiError ? error.retryAfterSeconds : undefined;
  },
  errorMessage(error: unknown): string {
    if (error instanceof ApiError) {
      const known = KNOWN_DETAIL_MESSAGES[error.message];
      if (known) {
        return known;
      }
      if (error.status >= 500) {
        return "サーバーでエラーが発生しました。時間をおいて再度お試しください。";
      }
      if (error.status === 422) {
        return "入力内容を確認してください。";
      }
      return error.message;
    }
    if (error instanceof TypeError) {
      return "サーバーに接続できませんでした。通信環境を確認してください。";
    }
    if (error instanceof Error) {
      return error.message;
    }
    return "不明なエラーが発生しました";
  },
  login(pin: string): Promise<LoginResponse> {
    return request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ pin }),
    });
  },
  session(): Promise<SessionResponse> {
    return request<SessionResponse>("/auth/session");
  },
  logout(): Promise<void> {
    return request<void>("/auth/logout", {
      method: "POST",
    });
  },
  listQualifications(includeStats: boolean): Promise<{ items: Qualification[] }> {
    return request<{ items: Qualification[] }>(
      `/qualifications?includeStats=${includeStats ? "true" : "false"}`
    );
  },
  createQualification(payload: {
    name: string;
    abbreviation: string | null;
    color: string;
    status: QualificationStatus;
  }): Promise<Qualification> {
    return request<Qualification>("/qualifications", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateQualification(
    qualificationId: string,
    payload: Partial<{
      name: string;
      abbreviation: string | null;
      color: string;
      status: QualificationStatus;
    }>
  ): Promise<Qualification> {
    return request<Qualification>(`/qualifications/${qualificationId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteQualification(qualificationId: string): Promise<void> {
    return request<void>(`/qualifications/${qualificationId}`, {
      method: "DELETE",
    });
  },
  listStudyLogs(qualificationId?: string): Promise<{ items: StudyLog[] }> {
    const query = qualificationId
      ? `&qualificationId=${encodeURIComponent(qualificationId)}`
      : "";
    return request<{ items: StudyLog[] }>(`/study-logs?sort=date_desc${query}`);
  },
  createStudyLog(payload: {
    qualificationId: string;
    date: string;
    hours: number;
    content: string;
    memo: string | null;
  }): Promise<StudyLog> {
    return request<StudyLog>("/study-logs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateStudyLog(
    studyLogId: string,
    payload: Partial<{
      date: string;
      hours: number;
      content: string;
      memo: string | null;
    }>
  ): Promise<StudyLog> {
    return request<StudyLog>(`/study-logs/${studyLogId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteStudyLog(studyLogId: string): Promise<void> {
    return request<void>(`/study-logs/${studyLogId}`, {
      method: "DELETE",
    });
  },
  listMilestones(qualificationId?: string): Promise<{ items: Milestone[] }> {
    const query = qualificationId
      ? `?qualificationId=${encodeURIComponent(qualificationId)}`
      : "";
    return request<{ items: Milestone[] }>(`/milestones${query}`);
  },
  createMilestone(payload: {
    qualificationId: string;
    title: string;
    plannedDate: string | null;
  }): Promise<Milestone> {
    return request<Milestone>("/milestones", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateMilestone(
    milestoneId: string,
    payload: Partial<{
      qualificationId: string;
      title: string;
      plannedDate: string | null;
      completedDate: string | null;
      status: MilestoneStatus;
    }>
  ): Promise<Milestone> {
    return request<Milestone>(`/milestones/${milestoneId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteMilestone(milestoneId: string): Promise<void> {
    return request<void>(`/milestones/${milestoneId}`, {
      method: "DELETE",
    });
  },
  getCalendarMonth(year: number, month: number): Promise<CalendarMonth> {
    return request<CalendarMonth>(`/calendar/month?year=${year}&month=${month}`);
  },
  getCalendarDay(date: string): Promise<CalendarDayDetail> {
    return request<CalendarDayDetail>(`/calendar/day?date=${date}`);
  },
};