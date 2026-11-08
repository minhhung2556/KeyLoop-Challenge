import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getLead,
  listLeads,
  logLeadActivity,
  updateLeadStatus,
} from "../api/client";
import type { ActivityCreate, LeadStatus } from "../api";
import { queryKeys } from "./queryKeys";

export type LeadStatusFilter = LeadStatus | "all";

export function useLeadsList(filters: { status: LeadStatusFilter; q: string }) {
  return useQuery({
    queryKey: queryKeys.leads.list(filters),
    queryFn: () =>
      listLeads({
        status: filters.status,
        q: filters.q || undefined,
      }),
  });
}

export function useLeadDetail(leadId: string | null) {
  return useQuery({
    queryKey: queryKeys.leads.detail(leadId || ""),
    queryFn: () => getLead(leadId as string),
    enabled: Boolean(leadId),
  });
}

export function useUpdateLeadStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ leadId, status }: { leadId: string; status: LeadStatus }) =>
      updateLeadStatus(leadId, status),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.leads.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.leads.detail(variables.leadId),
      });
    },
  });
}

export function useLogLeadActivity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      leadId,
      payload,
    }: {
      leadId: string;
      payload: ActivityCreate;
    }) => logLeadActivity(leadId, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.leads.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.leads.detail(variables.leadId),
      });
    },
  });
}
