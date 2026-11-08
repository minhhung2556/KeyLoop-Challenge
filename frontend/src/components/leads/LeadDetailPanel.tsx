import LeadStatusMenu from "../dashboard/LeadStatusMenu";
import { COMPACT_CARD, COMPACT_CARD_TITLE, COMPACT_META } from "../dashboard/dashboardStyles";
import type { LeadStatus } from "../../api";
import { messageForLeadError } from "../../constants/leadErrorCodes";
import { ApiError } from "../../api/client";
import { useLeadDetail, useUpdateLeadStatus } from "../../hooks/useLeads";
import { getLeadAttributionEntries } from "../../utils/leadAttribution";
import { sortActivitiesByCreatedAt } from "../../utils/leadValidation";
import LogActivityForm from "./LogActivityForm";

export default function LeadDetailPanel({ leadId }: { leadId: string | null }) {
  const detailQuery = useLeadDetail(leadId);
  const updateStatus = useUpdateLeadStatus();

  if (!leadId) {
    return (
      <div className={COMPACT_CARD}>
        <p className="text-sm text-muted-foreground">Select a lead to see details.</p>
      </div>
    );
  }

  if (detailQuery.isPending) {
    return (
      <div className={COMPACT_CARD} aria-busy="true">
        <div className="h-5 w-40 animate-pulse rounded bg-muted" />
        <div className="mt-3 h-4 w-full animate-pulse rounded bg-muted" />
      </div>
    );
  }

  if (detailQuery.isError) {
    const code =
      detailQuery.error instanceof ApiError
        ? detailQuery.error.error_code
        : undefined;
    return (
      <div className={COMPACT_CARD}>
        <p role="alert">{messageForLeadError(code)}</p>
        <button type="button" className="mt-2 text-sm text-accent-600" onClick={() => detailQuery.refetch()}>
          Retry
        </button>
      </div>
    );
  }

  const lead = detailQuery.data;
  const activities = sortActivitiesByCreatedAt(lead.activities || []);
  const attribution = getLeadAttributionEntries(lead);

  return (
    <div className="space-y-4">
      <div className={COMPACT_CARD}>
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className={COMPACT_CARD_TITLE}>{lead.name}</h2>
            <p className={COMPACT_META}>{lead.email}</p>
            <p className={COMPACT_META}>{lead.phone}</p>
            {lead.vehicleInterest ? (
              <p className="mt-1 text-sm text-foreground">{lead.vehicleInterest}</p>
            ) : null}
          </div>
          <LeadStatusMenu
            leadId={lead.id}
            status={lead.status}
            isUpdating={updateStatus.isPending}
            onSelect={(status: LeadStatus) =>
              updateStatus.mutate({ leadId: lead.id, status })
            }
          />
        </div>
        <p className="mt-3 whitespace-pre-wrap text-sm text-foreground">{lead.message}</p>
        {attribution.length ? (
          <div className="mt-3 flex flex-wrap gap-1">
            {attribution.map((entry) => (
              <span
                key={entry.field}
                className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
              >
                {entry.field}: {entry.value}
              </span>
            ))}
          </div>
        ) : null}
      </div>

      <div className={COMPACT_CARD}>
        <h3 className="text-sm font-semibold text-foreground">Activity log</h3>
        {activities.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">No follow-ups yet.</p>
        ) : (
          <ol className="mt-3 space-y-3">
            {activities.map((activity) => (
              <li key={activity.id} className="border-l-2 border-accent-600 pl-3">
                <p className="text-sm font-medium">{activity.summary}</p>
                <p className="text-xs text-muted-foreground">
                  {activity.type} · {activity.createdBy} ·{" "}
                  {new Date(activity.createdAt).toLocaleString()}
                </p>
                {activity.notes ? (
                  <p className="mt-1 text-sm text-foreground">{activity.notes}</p>
                ) : null}
              </li>
            ))}
          </ol>
        )}
      </div>

      <div className={COMPACT_CARD}>
        <LogActivityForm leadId={lead.id} />
      </div>
    </div>
  );
}
