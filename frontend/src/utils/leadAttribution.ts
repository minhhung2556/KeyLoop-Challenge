import type { LeadResponse } from "../api";

const LEAD_ATTRIBUTION_QUERY_KEYS = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_content",
  "utm_term",
  "ref",
] as const;

const LEAD_ATTRIBUTION_BODY_KEYS: Record<
  (typeof LEAD_ATTRIBUTION_QUERY_KEYS)[number],
  keyof LeadAttributionPayload
> = {
  utm_source: "utmSource",
  utm_medium: "utmMedium",
  utm_campaign: "utmCampaign",
  utm_content: "utmContent",
  utm_term: "utmTerm",
  ref: "ref",
};

const LEAD_ATTRIBUTION_MAX_LENGTH = 200;

export type LeadAttributionPayload = {
  utmSource?: string;
  utmMedium?: string;
  utmCampaign?: string;
  utmContent?: string;
  utmTerm?: string;
  ref?: string;
};

export function readLeadAttributionFromSearch(
  search: string,
): LeadAttributionPayload {
  const params = new URLSearchParams(search);
  const payload: LeadAttributionPayload = {};

  for (const queryKey of LEAD_ATTRIBUTION_QUERY_KEYS) {
    const raw = params.get(queryKey);
    if (!raw) {
      continue;
    }
    const trimmed = raw.trim();
    if (!trimmed) {
      continue;
    }
    const bodyKey = LEAD_ATTRIBUTION_BODY_KEYS[queryKey];
    payload[bodyKey] = trimmed.slice(0, LEAD_ATTRIBUTION_MAX_LENGTH);
  }

  return payload;
}

export type LeadAttributionField =
  | "utmSource"
  | "utmMedium"
  | "utmCampaign"
  | "utmContent"
  | "utmTerm"
  | "ref";

const ATTRIBUTION_FIELDS: LeadAttributionField[] = [
  "utmSource",
  "utmMedium",
  "utmCampaign",
  "utmContent",
  "utmTerm",
  "ref",
];

export type LeadAttributionEntry = {
  field: LeadAttributionField;
  value: string;
};

export function getLeadAttributionEntries(
  lead: LeadResponse,
): LeadAttributionEntry[] {
  const entries: LeadAttributionEntry[] = [];
  for (const field of ATTRIBUTION_FIELDS) {
    const value = lead[field];
    if (value && value.trim()) {
      entries.push({ field, value: value.trim() });
    }
  }
  return entries;
}
