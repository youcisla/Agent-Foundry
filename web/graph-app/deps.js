/**
 * Shared dependency surface for the React Flow graph app.
 *
 * All bare specifiers ("react", "@xyflow/react", …) are resolved by the
 * <script type="importmap"> declared in graph.html, which points every one of
 * them at esm.sh. React Flow is imported with ?external=react,react-dom so it
 * reuses the SAME React instance as our components — this is mandatory, or hooks
 * across the custom-node boundary would throw "invalid hook call".
 *
 * No bundler, no build step: this runs natively in the browser.
 */
import React from "react";
import { createRoot } from "react-dom/client";
import htm from "htm";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  BackgroundVariant,
  MiniMap,
  Controls,
  Panel,
  Handle,
  Position,
  MarkerType,
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  getStraightPath,
  applyNodeChanges,
  applyEdgeChanges,
  useReactFlow,
} from "@xyflow/react";

export const html = htm.bind(React.createElement);

export {
  React,
  createRoot,
  ReactFlow,
  ReactFlowProvider,
  Background,
  BackgroundVariant,
  MiniMap,
  Controls,
  Panel,
  Handle,
  Position,
  MarkerType,
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  getStraightPath,
  applyNodeChanges,
  applyEdgeChanges,
  useReactFlow,
};

export const {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
  memo,
  useSyncExternalStore,
  createElement,
  Fragment,
} = React;

/**
 * Icon — renders a brand SVG from the global ICONS map (icons.js) directly into
 * the React tree. This replaces the old .icon-svg text-placeholder + DOM-mutation
 * approach, which fought with React's rendering.
 */
export function Icon({ name, className }) {
  const svg = (typeof window !== "undefined" && window.ICONS && window.ICONS[name]) || "";
  return React.createElement("span", {
    className: "icon-svg" + (className ? " " + className : ""),
    dangerouslySetInnerHTML: { __html: svg },
  });
}
