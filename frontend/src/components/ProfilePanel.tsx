"use client";

import { DOMAINS, scoreBand, BAND_LABELS } from "@kashmiratlas/shared-types";
import { useAtlas } from "@/store/atlasStore";

function ScoreBars({ scores }: { scores: Record<string, number> }) {
  return (
    <div className="space-y-1">
      {DOMAINS.map((d) => {
        const v = scores[d.id] ?? 0;
        return (
          <div key={d.id} className="flex items-center gap-2 text-xs">
            <span className="w-40 shrink-0 truncate text-slate-300" title={d.label}>
              {d.label}
            </span>
            <div className="h-2 flex-1 overflow-hidden rounded bg-panelMuted">
              <div
                className="h-full bg-sky-500"
                style={{ width: `${v}%` }}
                title={`${v} — band ${scoreBand(v)} (${BAND_LABELS[scoreBand(v)]})`}
              />
            </div>
            <span className="w-7 text-right tabular-nums">{v}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function ProfilePanel() {
  const { selectedCell, selectedPlace, setSelectedCell, setSelectedPlace } = useAtlas();
  if (!selectedCell && !selectedPlace) return null;

  const title = selectedPlace
    ? selectedPlace.name
    : `Cell ${selectedCell!.h3_index.slice(0, 8)}…`;
  const subtitle = selectedPlace
    ? `${selectedPlace.kind}${selectedPlace.district ? ` · ${selectedPlace.district}` : ""} · ${selectedPlace.cell_count} cells`
    : `res ${selectedCell!.resolution}${
        selectedCell!.elevation_m ? ` · ${Math.round(selectedCell!.elevation_m)} m` : ""
      }`;
  const scores = selectedPlace ? selectedPlace.scores : selectedCell!.scores;

  return (
    <div className="absolute right-4 top-4 z-10 max-h-[90vh] w-96 overflow-auto rounded-lg bg-panel/95 p-4 backdrop-blur">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h2 className="text-base font-semibold">{title}</h2>
          <p className="text-xs text-slate-400">{subtitle}</p>
        </div>
        <button
          onClick={() => {
            setSelectedCell(null);
            setSelectedPlace(null);
          }}
          className="rounded px-2 text-slate-400 hover:text-white"
        >
          ✕
        </button>
      </div>

      <h3 className="mb-1 text-xs uppercase tracking-wide text-slate-400">
        360 capability profile
      </h3>
      <ScoreBars scores={scores} />

      {selectedCell && (
        <>
          <h3 className="mb-1 mt-4 text-xs uppercase tracking-wide text-slate-400">
            Raw parameters
          </h3>
          <dl className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[11px]">
            {Object.entries(selectedCell.raw).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2">
                <dt className="truncate text-slate-400" title={k}>
                  {k}
                </dt>
                <dd className="tabular-nums">{String(v)}</dd>
              </div>
            ))}
          </dl>
          {selectedCell.places.length > 0 && (
            <p className="mt-3 text-xs text-slate-400">
              In: {selectedCell.places.map((p) => p.name).join(", ")}
            </p>
          )}
        </>
      )}
    </div>
  );
}
