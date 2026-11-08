export type LeadStatus = "new" | "contacted" | "closed";
export type ActivityType = "call" | "email" | "note" | "status_change";

export const LeadStatus = {
  NEW: "new",
  CONTACTED: "contacted",
  CLOSED: "closed",
} as const;

export type LeadResponse = {
  id: string;
  name: string;
  email: string;
  phone: string;
  message: string;
  createdAt: string;
  vehicleInterest?: string | null;
  utmSource?: string | null;
  utmMedium?: string | null;
  utmCampaign?: string | null;
  utmContent?: string | null;
  utmTerm?: string | null;
  ref?: string | null;
  status: LeadStatus;
};

export type ActivityResponse = {
  id: string;
  leadId: string;
  type: ActivityType;
  summary: string;
  notes?: string | null;
  createdBy: string;
  createdAt: string;
};

export type LeadDetailResponse = LeadResponse & {
  activities: ActivityResponse[];
};

export type LeadListResponse = {
  items: LeadResponse[];
  total: number;
  limit: number;
  offset: number;
};

export type LeadCreate = {
  name: string;
  email: string;
  phone: string;
  message: string;
  vehicleInterest?: string;
};

export type ActivityCreate = {
  type: ActivityType;
  summary: string;
  notes?: string;
  createdBy?: string;
};
