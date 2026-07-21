/**
 * Deterministic color system.
 * - communityColor(): 44 distinguishable hues on a wheel anchored to the brand
 *   accent (#f5a623 ≈ hue 39), with alternating saturation/lightness so adjacent
 *   community indices stay visually separable.
 * - KIND_COLORS: fixed accents per node kind for the orchestration pipeline.
 */
export function communityColor(index, total = 44) {
  const hue = Math.round((39 + (index * 360) / Math.max(total, 1)) % 360);
  const sat = 60 + (index % 3) * 9;   // 60 / 69 / 78
  const light = 56 + (index % 2) * 7; // 56 / 63
  return `hsl(${hue} ${sat}% ${light}%)`;
}

export const KIND_COLORS = {
  function: "#f5a623",
  class: "#ff6b35",
  method: "#f5a623",
  file: "#6496ff",
  symbol: "#8b8b95",
  agent: "#f5a623",
  skill: "#4ade80",
  store: "#8b8b95",
  provider: "#4ade80",
  input: "#f5a623",
  output: "#f5a623",
};

// Per agent-role accent so planner/critic/orchestrator read distinctly.
export const ROLE_COLORS = {
  orchestrator: "#f5a623",
  planner: "#6496ff",
  critic: "#ff6b35",
};
