/**
 * InfiniteCanvas — the core canvas engine.
 *
 * Features:
 * - Pan: Space+drag | middle-click drag | right-click drag
 * - Zoom: Ctrl+Wheel (pinch zoom on trackpad)
 * - Widget drag via their handle bar
 * - Connection mode: click "connect" icon on widget → click another widget
 * - Delete widget/connection with keyboard Delete
 */
import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type { CanvasConnection, CanvasWidget, WidgetType } from "../../api/canvas";
import ProductCardWidget from "./widgets/ProductCardWidget";
import LogisticsWidget from "./widgets/LogisticsWidget";
import AdConnectorWidget from "./widgets/AdConnectorWidget";
import MiniChartWidget from "./widgets/MiniChartWidget";
import StickerWidget from "./widgets/StickerWidget";

import css from "./InfiniteCanvas.module.css";

export interface Viewport {
  x: number;
  y: number;
  zoom: number;
}

interface Props {
  widgets: CanvasWidget[];
  connections: CanvasConnection[];
  viewport: Viewport;
  onViewportChange: (vp: Viewport) => void;
  onWidgetMove: (id: string, x: number, y: number) => void;
  onWidgetDelete: (id: string) => void;
  onWidgetDataChange: (id: string, data: Record<string, any>) => void;
  onConnectionCreate: (fromId: string, toId: string) => void;
  onConnectionDelete: (id: string) => void;
}

const MIN_ZOOM = 0.1;
const MAX_ZOOM = 5;
const GRID_SIZE = 32;

/** Clamp zoom. */
const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

/** Widget center in SCREEN space (for drawing connections). */
function widgetScreenCenter(w: CanvasWidget, vp: Viewport) {
  return {
    x: w.x * vp.zoom + vp.x + (w.width * vp.zoom) / 2,
    y: w.y * vp.zoom + vp.y + (w.height * vp.zoom) / 2,
  };
}

/** Cubic bezier path between two screen points. */
function cubicBezierPath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = Math.abs(x2 - x1) * 0.5;
  return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
}

const WIDGET_LABELS: Record<WidgetType, { icon: string; label: string }> = {
  product_card: { icon: "🛍", label: "Карточка товара" },
  logistics:    { icon: "📦", label: "Логистика" },
  ad_connector: { icon: "📢", label: "Реклама" },
  mini_chart:   { icon: "📈", label: "График" },
  sticker:      { icon: "📝", label: "Стикер" },
  text:         { icon: "✏️", label: "Текст" },
  kpi_table:    { icon: "📊", label: "Таблица KPI" },
};

const DEFAULT_SIZES: Record<WidgetType, { w: number; h: number }> = {
  product_card: { w: 280, h: 360 },
  logistics:    { w: 260, h: 220 },
  ad_connector: { w: 260, h: 210 },
  mini_chart:   { w: 340, h: 200 },
  sticker:      { w: 220, h: 160 },
  text:         { w: 260, h: 120 },
  kpi_table:    { w: 380, h: 260 },
};

export { DEFAULT_SIZES };

function renderWidgetContent(
  widget: CanvasWidget,
  onDataChange: (data: Record<string, any>) => void
) {
  switch (widget.widget_type) {
    case "product_card":
      return <ProductCardWidget widget={widget} onDataChange={onDataChange} />;
    case "logistics":
      return <LogisticsWidget widget={widget} onDataChange={onDataChange} />;
    case "ad_connector":
      return <AdConnectorWidget widget={widget} onDataChange={onDataChange} />;
    case "mini_chart":
      return <MiniChartWidget widget={widget} />;
    case "sticker":
    case "text":
      return <StickerWidget widget={widget} onDataChange={onDataChange} />;
    case "kpi_table":
      return (
        <div style={{ padding: 12, fontSize: 13, color: "#64748b" }}>
          📊 Таблица KPI
          <br />
          <span style={{ fontSize: 11 }}>Двойной клик для редактирования</span>
        </div>
      );
    default:
      return null;
  }
}

export default function InfiniteCanvas({
  widgets,
  connections,
  viewport,
  onViewportChange,
  onWidgetMove,
  onWidgetDelete,
  onWidgetDataChange,
  onConnectionCreate,
  onConnectionDelete,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const vpRef = useRef(viewport);
  vpRef.current = viewport;

  // Panning state
  const isPanning = useRef(false);
  const panStart = useRef({ x: 0, y: 0, vpX: 0, vpY: 0 });
  const spaceDown = useRef(false);

  // Dragging widget state
  const draggingWidget = useRef<{
    id: string;
    startMouseX: number;
    startMouseY: number;
    startX: number;
    startY: number;
  } | null>(null);

  // Connection mode
  const [connectSource, setConnectSource] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Drag local positions (optimistic update while dragging)
  const [dragOverride, setDragOverride] = useState<Record<string, { x: number; y: number }>>({});

  // ── Keyboard ──────────────────────────────────────────────

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && !e.repeat) {
        // Don't hijack Space when typing in an input/textarea
        const tag = (document.activeElement as HTMLElement)?.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA") return;
        e.preventDefault();
        spaceDown.current = true;
        containerRef.current?.setAttribute("data-pan", "true");
      }
      if ((e.code === "Delete" || e.code === "Backspace") && selectedId) {
        const tag = (document.activeElement as HTMLElement)?.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA") return;
        e.preventDefault();
        onWidgetDelete(selectedId);
        setSelectedId(null);
      }
      if (e.code === "Escape") {
        setConnectSource(null);
        setSelectedId(null);
      }
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        spaceDown.current = false;
        containerRef.current?.removeAttribute("data-pan");
      }
    };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
    };
  }, [selectedId, onWidgetDelete]);

  // ── Canvas mouse events ───────────────────────────────────

  const startPan = useCallback((clientX: number, clientY: number) => {
    isPanning.current = true;
    panStart.current = {
      x: clientX,
      y: clientY,
      vpX: vpRef.current.x,
      vpY: vpRef.current.y,
    };
    containerRef.current?.setAttribute("data-pan", "true");
  }, []);

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      // Click on canvas bg → deselect
      if (e.target === containerRef.current || (e.target as HTMLElement).classList.contains(css.world)) {
        setSelectedId(null);
        setConnectSource(null);
      }
      // Middle click or Space+left → pan
      if (e.button === 1 || (e.button === 0 && spaceDown.current)) {
        e.preventDefault();
        startPan(e.clientX, e.clientY);
      }
      // Right-click → pan
      if (e.button === 2) {
        e.preventDefault();
        startPan(e.clientX, e.clientY);
      }
    },
    [startPan]
  );

  const onMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (isPanning.current) {
        const dx = e.clientX - panStart.current.x;
        const dy = e.clientY - panStart.current.y;
        onViewportChange({
          ...vpRef.current,
          x: panStart.current.vpX + dx,
          y: panStart.current.vpY + dy,
        });
        return;
      }

      if (draggingWidget.current) {
        const dw = draggingWidget.current;
        const dx = (e.clientX - dw.startMouseX) / vpRef.current.zoom;
        const dy = (e.clientY - dw.startMouseY) / vpRef.current.zoom;
        setDragOverride((prev) => ({
          ...prev,
          [dw.id]: { x: dw.startX + dx, y: dw.startY + dy },
        }));
      }
    },
    [onViewportChange]
  );

  const onMouseUp = useCallback(
    () => {
      if (isPanning.current) {
        isPanning.current = false;
        if (!spaceDown.current) {
          containerRef.current?.removeAttribute("data-pan");
        }
      }

      if (draggingWidget.current) {
        const dw = draggingWidget.current;
        const override = dragOverride[dw.id];
        if (override) {
          onWidgetMove(dw.id, override.x, override.y);
        }
        draggingWidget.current = null;
        setDragOverride({});
      }
    },
    [dragOverride, onWidgetMove]
  );

  const onWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();
      const rect = containerRef.current!.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const vp = vpRef.current;
      const factor = e.deltaY < 0 ? 1.1 : 0.9;
      const newZoom = clamp(vp.zoom * factor, MIN_ZOOM, MAX_ZOOM);
      const scale = newZoom / vp.zoom;

      onViewportChange({
        x: mouseX - (mouseX - vp.x) * scale,
        y: mouseY - (mouseY - vp.y) * scale,
        zoom: newZoom,
      });
    },
    [onViewportChange]
  );

  // ── Widget drag ───────────────────────────────────────────

  const onWidgetHandleMouseDown = useCallback(
    (e: React.MouseEvent, widget: CanvasWidget) => {
      e.stopPropagation();
      if (connectSource !== null) return;
      setSelectedId(widget.id);
      draggingWidget.current = {
        id: widget.id,
        startMouseX: e.clientX,
        startMouseY: e.clientY,
        startX: widget.x,
        startY: widget.y,
      };
    },
    [connectSource]
  );

  // ── Connection mode ───────────────────────────────────────

  const onConnectClick = useCallback(
    (e: React.MouseEvent, widgetId: string) => {
      e.stopPropagation();
      if (!connectSource) {
        setConnectSource(widgetId);
      } else if (connectSource !== widgetId) {
        onConnectionCreate(connectSource, widgetId);
        setConnectSource(null);
      } else {
        setConnectSource(null);
      }
    },
    [connectSource, onConnectionCreate]
  );

  const onWidgetClick = useCallback(
    (e: React.MouseEvent, widgetId: string) => {
      e.stopPropagation();
      if (connectSource && connectSource !== widgetId) {
        onConnectionCreate(connectSource, widgetId);
        setConnectSource(null);
      } else {
        setSelectedId(widgetId);
      }
    },
    [connectSource, onConnectionCreate]
  );

  // ── Background grid style ─────────────────────────────────

  const gridBgStyle = {
    backgroundSize: `${GRID_SIZE * viewport.zoom}px ${GRID_SIZE * viewport.zoom}px`,
    backgroundPosition: `${((viewport.x % (GRID_SIZE * viewport.zoom)) + GRID_SIZE * viewport.zoom) % (GRID_SIZE * viewport.zoom)}px ${((viewport.y % (GRID_SIZE * viewport.zoom)) + GRID_SIZE * viewport.zoom) % (GRID_SIZE * viewport.zoom)}px`,
  } as React.CSSProperties;

  // ── Render ────────────────────────────────────────────────

  return (
    <div
      ref={containerRef}
      className={css.root}
      style={gridBgStyle}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      onWheel={onWheel}
      onContextMenu={(e) => e.preventDefault()}
    >
      {/* SVG connections layer — drawn in SCREEN space */}
      <svg className={css.connections}>
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#B0C4DE" />
          </marker>
        </defs>
        {connections.map((conn) => {
          const from = widgets.find((w) => w.id === conn.from_widget_id);
          const to = widgets.find((w) => w.id === conn.to_widget_id);
          if (!from || !to) return null;

          // Use drag override positions for live preview
          const fromPos = dragOverride[from.id] ? { ...from, ...dragOverride[from.id] } : from;
          const toPos = dragOverride[to.id] ? { ...to, ...dragOverride[to.id] } : to;

          const fc = widgetScreenCenter(fromPos, viewport);
          const tc = widgetScreenCenter(toPos, viewport);
          const isDashed = conn.style?.type === "dashed";
          const color = conn.style?.color || "#B0C4DE";
          const thickness = conn.style?.thickness || 2;

          const midX = (fc.x + tc.x) / 2;
          const midY = (fc.y + tc.y) / 2;

          return (
            <g key={conn.id}>
              <path
                d={cubicBezierPath(fc.x, fc.y, tc.x, tc.y)}
                className={`${css.connectionPath} ${isDashed ? css.connectionPathDashed : ""}`}
                stroke={color}
                strokeWidth={thickness}
                markerEnd="url(#arrowhead)"
                onClick={() => onConnectionDelete(conn.id)}
              />
              {conn.label && (
                <text
                  className={css.connectionLabel}
                  x={midX}
                  y={midY - 6}
                  textAnchor="middle"
                >
                  {conn.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {/* World layer — widgets live here */}
      <div
        className={css.world}
        style={{ transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})` }}
      >
        {widgets.map((widget) => {
          const pos = dragOverride[widget.id] ?? { x: widget.x, y: widget.y };
          const meta = WIDGET_LABELS[widget.widget_type as WidgetType] ?? { icon: "▣", label: widget.widget_type };
          const isSelected = selectedId === widget.id;
          const isConnectSrc = connectSource === widget.id;

          return (
            <div
              key={widget.id}
              className={`${css.widget} ${isSelected ? css.widgetSelected : ""} ${isConnectSrc ? css.widgetConnectSource : ""}`}
              style={{
                left: pos.x,
                top: pos.y,
                width: widget.width,
                height: widget.height,
                zIndex: widget.z_index + (isSelected ? 1000 : 0),
                display: "flex",
                flexDirection: "column",
                backgroundColor: widget.style?.bg_color || "#ffffff",
              }}
              onClick={(e) => onWidgetClick(e, widget.id)}
            >
              {/* Handle (drag bar) */}
              <div
                className={css.widgetHandle}
                onMouseDown={(e) => onWidgetHandleMouseDown(e, widget)}
              >
                <span className={css.widgetHandleIcon}>{meta.icon}</span>
                <span className={css.widgetHandleLabel}>{widget.data?.name || meta.label}</span>
                <button
                  className={css.widgetConnectBtn}
                  title="Соединить с другим виджетом"
                  onClick={(e) => onConnectClick(e, widget.id)}
                >
                  ⇢
                </button>
                <button
                  className={css.widgetDeleteBtn}
                  title="Удалить виджет"
                  onClick={(e) => {
                    e.stopPropagation();
                    onWidgetDelete(widget.id);
                  }}
                >
                  ×
                </button>
              </div>

              {/* Widget body */}
              <div className={css.widgetBody}>
                {renderWidgetContent(widget, (data) => onWidgetDataChange(widget.id, data))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
