export const PHONE_NORMALIZED_RE = /^\+?[0-9]{8,20}$/;

export function normalizePhone(value: string): string {
  return value.replace(/[\s\-().]/g, "").trim();
}

export function isValidPhone(value: string): boolean {
  return PHONE_NORMALIZED_RE.test(normalizePhone(value));
}

export function sortActivitiesByCreatedAt<T extends { createdAt: string }>(
  activities: T[],
): T[] {
  return [...activities].sort(
    (left, right) =>
      new Date(left.createdAt).getTime() - new Date(right.createdAt).getTime(),
  );
}
