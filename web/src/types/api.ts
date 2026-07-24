export type QualificationStatus = "active" | "closed";

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
  overdueMilestoneCount: number | null;
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

export type Milestone = {
  id: string;
  qualificationId: string;
  title: string;
  dueDate: string | null;
  isAchieved: boolean;
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