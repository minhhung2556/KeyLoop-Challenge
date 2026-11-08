import assert from "node:assert/strict";
import test from "node:test";

import { readLeadAttributionFromSearch } from "../../src/utils/leadAttribution.ts";
import { LEAD_ERROR_CODES, messageForLeadError } from "../../src/constants/leadErrorCodes.ts";
import {
  isValidPhone,
  normalizePhone,
  sortActivitiesByCreatedAt,
} from "../../src/utils/leadValidation.ts";

test("extracts attribution from query string", () => {
  const payload = readLeadAttributionFromSearch(
    "?utm_source=google&utm_medium=cpc&ref=homepage",
  );
  assert.equal(payload.utmSource, "google");
  assert.equal(payload.utmMedium, "cpc");
  assert.equal(payload.ref, "homepage");
});

test("normalizes and validates phone numbers", () => {
  assert.equal(normalizePhone("+84 123 456 789"), "+84123456789");
  assert.equal(isValidPhone("+84 123 456 789"), true);
  assert.equal(isValidPhone("abc"), false);
});

test("maps lead error codes", () => {
  assert.equal(messageForLeadError(LEAD_ERROR_CODES.LEAD_NOT_FOUND), "Lead not found.");
});

test("sorts activities chronologically", () => {
  const sorted = sortActivitiesByCreatedAt([
    { createdAt: "2026-01-02T00:00:00" },
    { createdAt: "2026-01-01T00:00:00" },
  ]);
  assert.equal(sorted[0].createdAt, "2026-01-01T00:00:00");
  assert.equal(sorted[1].createdAt, "2026-01-02T00:00:00");
});
