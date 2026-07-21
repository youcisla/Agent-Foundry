/**
 * Data-flow simulation controller for the orchestration pipeline. Walks the
 * dispatch edges in `step` order, marking one edge/node active per tick, so the
 * user watches a prompt travel orchestrator → planner → executor → provider →
 * critic → SQLite → response. Respects prefers-reduced-motion by stepping
 * without the traveling token (the edge classes handle that in CSS).
 */
import { graphStore } from "./store.js";

export function makeSimulation(getEdges) {
  let timer = null;

  const sorted = () =>
    (getEdges() || []).slice().sort((a, b) => (a.data?.step || 0) - (b.data?.step || 0));

  function stop() {
    if (timer) { clearTimeout(timer); timer = null; }
  }

  function play() {
    const edges = sorted();
    if (!edges.length) return;
    stop();
    graphStore.getState().simSet({ running: true, done: false, step: -1 });
    let i = 0;
    const tick = () => {
      if (i >= edges.length) {
        graphStore.getState().simSet({ running: false, done: true, activeEdgeId: null, activeNodeId: null });
        timer = null;
        return;
      }
      const e = edges[i];
      graphStore.getState().simSet({ step: i, activeEdgeId: e.id, activeNodeId: e.target });
      i += 1;
      const speed = graphStore.getState().simulation.speed || 1;
      timer = setTimeout(tick, 1100 / speed);
    };
    tick();
  }

  function pause() {
    stop();
    graphStore.getState().simSet({ running: false });
  }

  function reset() {
    stop();
    graphStore.getState().simSet({ running: false, done: false, step: -1, activeEdgeId: null, activeNodeId: null });
  }

  function stepOnce() {
    const edges = sorted();
    if (!edges.length) return;
    stop();
    const cur = graphStore.getState().simulation.step;
    const i = Math.min(cur + 1, edges.length - 1);
    const e = edges[i];
    graphStore.getState().simSet({
      step: i, activeEdgeId: e.id, activeNodeId: e.target,
      running: false, done: i >= edges.length - 1,
    });
  }

  return { play, pause, reset, stepOnce };
}
