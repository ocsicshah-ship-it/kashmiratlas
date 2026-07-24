"use client";

import { DOMAINS, DOMAIN_GROUPS } from "@kashmiratlas/shared-types";
import { useAtlas } from "@/store/atlasStore";

export default function DomainSelector() {
  const { selectedDomain, setSelectedDomain } = useAtlas();

  return (
    <div className="rounded-lg bg-panel/90 p-2 backdrop-blur">
      <label className="mb-1 block text-xs uppercase tracking-wide text-slate-400">
        Capability domain
      </label>
      <select
        value={selectedDomain}
        onChange={(e) => setSelectedDomain(e.target.value)}
        className="w-64 rounded bg-panelMuted px-2 py-1 text-sm"
      >
        {DOMAIN_GROUPS.map((group) => (
          <optgroup key={group} label={group}>
            {DOMAINS.filter((d) => d.group === group).map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </div>
  );
}
