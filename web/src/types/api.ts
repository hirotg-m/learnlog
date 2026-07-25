export type QualificationStatus = "open" | "close";

export type Qualification = {
  id: string;
  name: string;
  abbreviation: string | null;
  color: string;
  status: QualificationStatus;
  createdAt: string;
  updatedAt: string;
  totalHours: number | null;
  studyLogCount: number | null;
  lastStudiedAt: string | null;
};

export type StudyLog = {
  id: string;
  qualificationId: string;
  date: string;
  hours: number;
  content: string;
  memo: string | null;
  createdAt: string;
  updatedAt: string;
};

export type MilestoneStatus = "open" | "close";

export type Milestone = {
  id: string;
  qualificationId: string;
  title: string;
  plannedDate: string | null;
  completedDate: string | null;
  status: MilestoneStatus;
  isOverdue: boolean;
  createdAt: string;
  updatedAt: string;
};

export type CalendarMonthItem = {
  qualificationId: string;
  qualificationName: string;
  abbreviation: string | null;
  color: string;
  hours: number;
};

export type CalendarDay = {
  date: string;
  items: CalendarMonthItem[];
};

export type CalendarMonth = {
  year: number;
  month: number;
  days: CalendarDay[];
};

export type CalendarDetailItem = {
  studyLogId: string;
  qualificationId: string;
  qualificationName: string;
  abbreviation: string | null;
  color: string;
  hours: number;
  content: string;
  memo: string | null;
  createdAt: string;
};

export type CalendarDayDetail = {
  date: string;
  items: CalendarDetailItem[];
};

export type ApiErrorBody = {
  detail?: string;
};