import { Inbox } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import { LeadStatus } from "../api";
import LeadStatusMenu from "../components/dashboard/LeadStatusMenu";
import {
  COMPACT_CARD,
  COMPACT_CARD_DESC,
  COMPACT_CARD_TITLE,
  COMPACT_META,
  COMPACT_SECTION_GAP,
} from "../components/dashboard/dashboardStyles";
import LeadDetailPanel from "../components/leads/LeadDetailPanel";
import { getLeadAttributionEntries } from "../utils/leadAttribution";
import {
  useLeadsList,
  useUpdateLeadStatus,
  type LeadStatusFilter,
} from "../hooks/useLeads";

const STATUS_FILTERS: LeadStatusFilter[] = [
  "all",
  LeadStatus.NEW,
  LeadStatus.CONTACTED,
  LeadStatus.CLOSED,
];

function LeadListSkeleton() {
  return (
    <div className={COMPACT_SECTION_GAP} aria-busy="true">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className={COMPACT_CARD}>
          <div className="h-4 w-40 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-3 w-52 animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  );
}

export default function LeadInboxPage() {
  const [statusFilter, setStatusFilter] = useState<LeadStatusFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const leadsQuery = useLeadsList({ status: statusFilter, q: appliedQuery });
  const updateStatus = useUpdateLeadStatus();
  const items = leadsQuery.data?.items ?? [];
  const total = leadsQuery.data?.total ?? 0;

  const onSearch = (event: FormEvent) => {
    event.preventDefault();
    setAppliedQuery(searchInput.trim());
  };

  const filterLabel = (filter: LeadStatusFilter) => {
    if (filter === "all") return "All";
    if (filter === LeadStatus.CONTACTED) return "Contacted";
    if (filter === LeadStatus.CLOSED) return "Closed";
    return "New";
  };

  const selectedInList = useMemo(
    () => items.find((item) => item.id === selectedId),
    [items, selectedId],
  );

  return (
    <main className="min-h-screen bg-background bg-hero-radial px-4 py-6">
      <div className="mx-auto max-w-6xl">
        <header className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-accent-600">
            Keyloop · Demand
          </p>
          <h1 className="text-2xl font-semibold text-foreground">Sales lead inbox</h1>
          <p className="text-sm text-muted-foreground">
            Website inquiries for dealership sales follow-up.
          </p>
        </header>

        <form className="mb-4 flex flex-wrap gap-2" onSubmit={onSearch}>
          <input
            className="min-w-[16rem] flex-1 rounded-lg border border-border bg-card px-3 py-2 text-sm"
            placeholder="Search name, email, phone, vehicle…"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            aria-label="Search leads"
          />
          <button type="submit" className="rounded-lg bg-blue-20 px-3 py-2 text-sm font-medium text-white">
            Search
          </button>
        </form>

        <div className="mb-4 flex flex-wrap gap-2" role="tablist" aria-label="Status filter">
          {STATUS_FILTERS.map((filter) => {
            const active = filter === statusFilter;
            return (
              <button
                key={filter}
                type="button"
                role="tab"
                aria-selected={active}
                className={
                  active
                    ? "rounded-full bg-blue-20 px-3 py-1 text-sm font-medium text-white"
                    : "rounded-full border border-border px-3 py-1 text-sm text-muted-foreground"
                }
                onClick={() => setStatusFilter(filter)}
              >
                {filterLabel(filter)}
              </button>
            );
          })}
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <section>
            {leadsQuery.isPending ? <LeadListSkeleton /> : null}
            {leadsQuery.isError ? (
              <div className={COMPACT_CARD}>
                <p role="alert">Could not load leads.</p>
                <button
                  type="button"
                  className="mt-2 text-sm text-accent-600"
                  onClick={() => leadsQuery.refetch()}
                >
                  Retry
                </button>
              </div>
            ) : null}
            {!leadsQuery.isPending && !leadsQuery.isError && items.length === 0 ? (
              <div className={COMPACT_CARD}>
                <Inbox className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
                <p className={COMPACT_CARD_TITLE}>No leads</p>
                <p className={COMPACT_CARD_DESC}>
                  Incoming website inquiries will show here.
                </p>
              </div>
            ) : null}
            <div className={COMPACT_SECTION_GAP}>
              {items.map((lead) => {
                const selected = lead.id === selectedId;
                const chips = getLeadAttributionEntries(lead);
                return (
                  <button
                    key={lead.id}
                    type="button"
                    className={`${COMPACT_CARD} w-full text-left ${selected ? "ring-2 ring-accent-600" : ""}`}
                    onClick={() => setSelectedId(lead.id)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className={COMPACT_CARD_TITLE}>{lead.name}</p>
                        <p className={COMPACT_META}>{lead.email}</p>
                        {lead.vehicleInterest ? (
                          <p className="text-sm text-foreground">{lead.vehicleInterest}</p>
                        ) : null}
                      </div>
                      <LeadStatusMenu
                        leadId={lead.id}
                        status={lead.status}
                        isUpdating={
                          updateStatus.isPending &&
                          updateStatus.variables?.leadId === lead.id
                        }
                        onSelect={(status) =>
                          updateStatus.mutate({ leadId: lead.id, status })
                        }
                      />
                    </div>
                    {chips.length ? (
                      <p className="mt-2 text-xs text-muted-foreground">
                        {chips.map((entry) => entry.value).join(" · ")}
                      </p>
                    ) : null}
                    {selectedInList && selected ? (
                      <span className="sr-only">Selected</span>
                    ) : null}
                    <span className="sr-only">{total} total</span>
                  </button>
                );
              })}
            </div>
          </section>
          <section>
            <LeadDetailPanel leadId={selectedId} />
          </section>
        </div>
      </div>
    </main>
  );
}
