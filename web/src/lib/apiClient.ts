import type {
  ApiErrorBody,
  CalendarDayDetail,
  CalendarMonth,
  Milestone,
  Qualification,
  QualificationStatus,
  StudyLog,
} from "../types/api";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

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
    throw new ApiError(response.status, detail);
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
  errorMessage(error: unknown): string {
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
  listStudyLogs(): Promise<{ items: StudyLog[] }> {
    return request<{ items: StudyLog[] }>("/study-logs?sort=date_desc");
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
  listMilestones(qualificationId?: string): Promise<{ items: Milestone[] }> {
    const query = qualificationId
      ? `?qualificationId=${encodeURIComponent(qualificationId)}`
      : "";
    return request<{ items: Milestone[] }>(`/milestones${query}`);
  },
  createMilestone(payload: {
    qualificationId: string;
    title: string;
    dueDate: string | null;
    isAchieved: boolean;
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
      dueDate: string | null;
      isAchieved: boolean;
    }>
  ): Promise<Milestone> {
    return request<Milestone>(`/milestones/${milestoneId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  getCalendarMonth(year: number, month: number): Promise<CalendarMonth> {
    return request<CalendarMonth>(`/calendar/month?year=${year}&month=${month}`);
  },
  getCalendarDay(date: string): Promise<CalendarDayDetail> {
    return request<CalendarDayDetail>(`/calendar/day?date=${date}`);
  },
};