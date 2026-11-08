export const queryKeys = {
  leads: {
    all: ["leads"] as const,
    list: (filters: { status?: string; q?: string } = {}) =>
      [...queryKeys.leads.all, "list", filters] as const,
    detail: (leadId: string) => [...queryKeys.leads.all, "detail", leadId] as const,
  },
} as const;
