import { Check, ChevronDown, Loader2 } from "lucide-react";
import { useId, useRef, useState } from "react";

import { LeadStatus } from "../../api";

const STATUS_OPTIONS: LeadStatus[] = [
  LeadStatus.NEW,
  LeadStatus.CONTACTED,
  LeadStatus.CLOSED,
];

const MENU_BUTTON_BASE =
  "inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60";

function statusButtonClass(status: LeadStatus): string {
  switch (status) {
    case LeadStatus.CONTACTED:
      return `${MENU_BUTTON_BASE} border-warning-border bg-warning text-warning-foreground`;
    case LeadStatus.CLOSED:
      return `${MENU_BUTTON_BASE} border-border bg-muted text-muted-foreground`;
    case LeadStatus.NEW:
    default:
      return `${MENU_BUTTON_BASE} border-info-border bg-info text-info-foreground`;
  }
}

function statusLabel(value: LeadStatus): string {
  switch (value) {
    case LeadStatus.CONTACTED:
      return "Contacted";
    case LeadStatus.CLOSED:
      return "Closed";
    default:
      return "New";
  }
}

type LeadStatusMenuProps = {
  leadId: string;
  status: LeadStatus;
  disabled?: boolean;
  isUpdating?: boolean;
  onSelect: (status: LeadStatus) => void;
};

export default function LeadStatusMenu({
  leadId,
  status,
  disabled = false,
  isUpdating = false,
  onSelect,
}: LeadStatusMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuId = useId();
  const isDisabled = disabled || isUpdating;

  return (
    <div className="relative inline-flex">
      <button
        ref={triggerRef}
        type="button"
        id={`lead-status-${leadId}`}
        className={statusButtonClass(status)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={isOpen ? menuId : undefined}
        disabled={isDisabled}
        onClick={() => setIsOpen((open) => !open)}
      >
        {isUpdating ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        ) : null}
        <span>{statusLabel(status)}</span>
        <ChevronDown className="h-3.5 w-3.5 opacity-70" aria-hidden="true" />
      </button>
      {isOpen ? (
        <div
          id={menuId}
          role="listbox"
          aria-labelledby={`lead-status-${leadId}`}
          className="absolute right-0 z-20 mt-1 min-w-[9rem] rounded-lg border border-border bg-card py-1 shadow-sm"
        >
          {STATUS_OPTIONS.map((option) => {
            const selected = option === status;
            return (
              <button
                key={option}
                type="button"
                role="option"
                aria-selected={selected}
                className="flex w-full items-center px-3 py-1.5 text-left text-sm hover:bg-muted"
                onClick={() => {
                  setIsOpen(false);
                  if (option !== status) {
                    onSelect(option);
                  }
                }}
              >
                <span>{statusLabel(option)}</span>
                {selected ? (
                  <Check className="ml-auto h-3 w-3 text-accent-600" aria-hidden="true" />
                ) : null}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
