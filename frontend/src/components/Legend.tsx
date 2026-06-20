"use client";

import { DOMAIN_BY_ID, BAND_LABELS } from "@kashmiratlas/shared-types";
import { useAtlas } from "@/store/atlasStore";
import { rampSwatch, type RampId } from "@/lib/colorRamp";

export default function Legend() {
  const { selectedDomain } = useAtlas();
  const domain = DOMAIN_BY_ID[selectedDomain];
  const ramp = (domain?.ramp ?? "viridis") as RampId;

  const stops = [0, 0.25, 0.5, 0.75, 1];

  return (
    <div className="absolute bottom-4 left-4 z-10 rounded-lg bg-panel/90 p-3 text-xs backdrop-blur">
      <div className="mb-2 font-medium">{domain?.label ?? selectedDomain}</div>
      <div className="flex h-3 w-56 overflow-hidden rounded">
        {Array.from({ length: 40 }).map((_, i) => (
          <div key={i} style={{ flex: 1, background: rampSwatch(ramp, i / 39) }} />
        ))}
      </div>
      <div className="mt-1 flex w-56 justify-between text-[10px] text-slate-400">
        {stops.map((s) => (
          <span key={s}>{Math.round(s * 100)}</span>
        ))}
      </div>
      <div className="mt-1 text-[10px] text-slate-500">
        {BAND_LABELS[1]} → {BAND_LABELS[5]}
      </div>
    </div>
  );
}
