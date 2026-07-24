import {
  interpolateViridis,
  interpolateMagma,
  interpolateRdYlGn,
  interpolateBlues,
} from "d3-scale-chromatic";

export type RampId = "viridis" | "magma" | "rdylgn" | "blues";

const INTERP: Record<RampId, (t: number) => string> = {
  viridis: interpolateViridis,
  magma: interpolateMagma,
  rdylgn: interpolateRdYlGn,
  blues: interpolateBlues,
};

/** Score (0–100) -> deck.gl RGBA tuple for the given ramp. */
export function scoreToRGBA(
  score: number | undefined,
  ramp: RampId,
  alpha = 200,
): [number, number, number, number] {
  if (score == null || Number.isNaN(score)) return [60, 60, 60, 40];
  const t = Math.max(0, Math.min(1, score / 100));
  const css = INTERP[ramp](t); // "rgb(r, g, b)"
  const m = css.match(/\d+/g)!.map(Number);
  return [m[0], m[1], m[2], alpha];
}

/** CSS color for legend swatches. */
export function rampSwatch(ramp: RampId, t: number): string {
  return INTERP[ramp](Math.max(0, Math.min(1, t)));
}
