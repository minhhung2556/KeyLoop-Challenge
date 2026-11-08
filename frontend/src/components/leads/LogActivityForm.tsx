import { FormEvent, useState } from "react";

import { ApiError } from "../../api/client";
import type { ActivityType } from "../../api";
import { messageForLeadError } from "../../constants/leadErrorCodes";
import { useLogLeadActivity } from "../../hooks/useLeads";

const TYPES: ActivityType[] = ["call", "email", "note"];

export default function LogActivityForm({ leadId }: { leadId: string }) {
  const mutation = useLogLeadActivity();
  const [type, setType] = useState<ActivityType>("call");
  const [summary, setSummary] = useState("Called customer");
  const [notes, setNotes] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!summary.trim()) {
      setLocalError("Summary is required.");
      return;
    }
    setLocalError(null);
    mutation.mutate({
      leadId,
      payload: {
        type,
        summary: summary.trim(),
        notes: notes.trim() || undefined,
      },
    });
  };

  const apiError =
    mutation.error instanceof ApiError
      ? messageForLeadError(mutation.error.error_code)
      : mutation.error
        ? "Could not save activity."
        : null;

  return (
    <form className="space-y-3" onSubmit={onSubmit}>
      <h3 className="text-sm font-semibold text-foreground">Log follow-up</h3>
      <label className="block text-sm">
        <span className="text-muted-foreground">Type</span>
        <select
          className="mt-1 w-full rounded-lg border border-border bg-card px-2 py-1.5"
          value={type}
          onChange={(event) => setType(event.target.value as ActivityType)}
        >
          {TYPES.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        <span className="text-muted-foreground">Summary</span>
        <input
          className="mt-1 w-full rounded-lg border border-border bg-card px-2 py-1.5"
          value={summary}
          onChange={(event) => setSummary(event.target.value)}
        />
        <button
          type="button"
          className="mt-1 text-xs text-accent-600"
          onClick={() => setSummary("Called customer")}
        >
          Use “Called customer”
        </button>
      </label>
      <label className="block text-sm">
        <span className="text-muted-foreground">Notes (optional)</span>
        <textarea
          className="mt-1 w-full rounded-lg border border-border bg-card px-2 py-1.5"
          rows={3}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
        />
      </label>
      {localError || apiError ? (
        <p role="alert" className="text-sm text-danger">
          {localError || apiError}
        </p>
      ) : null}
      {mutation.isSuccess ? (
        <p className="text-sm text-success">Activity saved.</p>
      ) : null}
      <button
        type="submit"
        className="rounded-lg bg-blue-20 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
        disabled={mutation.isPending}
      >
        {mutation.isPending ? "Saving…" : "Save activity"}
      </button>
    </form>
  );
}
