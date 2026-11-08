export const LEAD_ERROR_CODES = {
  LEAD_NOT_FOUND: "LEAD_NOT_FOUND",
  LEAD_VALIDATION_ERROR: "LEAD_VALIDATION_ERROR",
  INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
} as const;

export type LeadErrorCode =
  (typeof LEAD_ERROR_CODES)[keyof typeof LEAD_ERROR_CODES];

export function messageForLeadError(code?: string | null): string {
  switch (code) {
    case LEAD_ERROR_CODES.LEAD_NOT_FOUND:
      return "Lead not found.";
    case LEAD_ERROR_CODES.LEAD_VALIDATION_ERROR:
      return "Check the form fields and try again.";
    default:
      return "Something went wrong. Try again.";
  }
}
