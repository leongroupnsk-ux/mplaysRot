import { useRef, useEffect, useCallback } from "react";
import type { CanvasWidget } from "../../api/canvas";
import type { Viewport } from "./InfiniteCanvas";
import css from "./MiniMap.module.css";

interface Props {
  widgets: CanvasWidget[];
  viewport: Viewport;
  containerWidth: number;
  containerHeight: number;
  onNavigate: (vp: Viewport) => void;
}

const MM_W = 180;
const MM_H = 110;

/** Compute bounding box of all widgets + some padding. */
function worldBounds(widgets: CanvasWidget[]) {
  if (widgets.length === 0) {
    return { minX: -500, minY: -300, maxX: 1000, maxY: 800 };
  }
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const w of widgets) {
    minX = Math.min(minX, w.x - 60);
    minY = Math.min(minY, w.y - 60);
    maxX = Math.max(maxX, w.x + w.width + 60);
    maxY = Math.max(maxY, w.y + w.height + 60);
  }
  return { minX, minY, maxX, maxY };
}

export default function MiniMap({
  widgets,
  viewport,
  containerWidth,
  containerHeight,
  onNavigate,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const bounds = worldBounds(widgets);
  const worldW = bounds.maxX - bounds.minX;
  const worldH = bounds.maxY - bounds.minY;
  const scaleX = MM_W / worldW;
  const scaleY = MM_H / worldH;
  const scale = Math.min(scaleX, scaleY) * 0.9;

  // Map world coords to minimap coords
  const toMM = (wx: number, wy: number) => ({
    x: (wx - bounds.minX) * scale + (MM_W - worldW * scale) / 2,
    y: (wy - bounds.minY) * scale + (MM_H - worldH * scale) / 2,
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, MM_W, MM_H);

    // Draw widgets as colored rects
    for (const w of widgets) {
      const { x, y } = toMM(w.x, w.y);
      const ww = w.width * scale;
      const wh = w.height * scale;

      const colors: Record<string, string> = {
        product_card: "#ede9fe",
        logistics:    "#dcfce7",
        ad_connector: "#dbeafe",
        mini_chart:   "#fce7f3",
        sticker:      "#fef3c7",
        text:         "#f1f5f9",
        kpi_table:    "#fef3c7",
      };

      ctx.fillStyle = colors[w.widget_type] || "#e2e8f0";
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 0.5;
      ctx.beginPath();
      ctx.roundRect(x, y, Math.max(ww, 3), Math.max(wh, 3), 1);
      ctx.fill();
      ctx.stroke();
    }
  }, [widgets, scale, bounds]);

  // Viewport indicator
  // Convert viewport to world rect → minimap rect
  const vpWorldX = -viewport.x / viewport.zoom;
  const vpWorldY = -viewport.y / viewport.zoom;
  const vpWorldW = containerWidth / viewport.zoom;
  const vpWorldH = containerHeight / viewport.zoom;

  const vpMM = toMM(vpWorldX, vpWorldY);
  const vpMMW = vpWorldW * scale;
  const vpMMH = vpWorldH * scale;

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const mmX = e.clientX - rect.left;
      const mmY = e.clientY - rect.top;

      const offsetX = (MM_W - worldW * scale) / 2;
      const offsetY = (MM_H - worldH * scale) / 2;

      const worldX = (mmX - offsetX) / scale + bounds.minX;
      const worldY = (mmY - offsetY) / scale + bounds.minY;

      // Center viewport on clicked world point
      onNavigate({
        ...viewport,
        x: containerWidth / 2 - worldX * viewport.zoom,
        y: containerHeight / 2 - worldY * viewport.zoom,
      });
    },
    [viewport, containerWidth, containerHeight, bounds, worldW, scale, onNavigate]
  );

  return (
    <div className={css.minimap} onClick={handleClick} title="Кликните для навигации">
      <canvas
        ref={canvasRef}
        className={css.canvas}
        width={MM_W}
        height={MM_H}
      />
      {/* Viewport indicator */}
      <div
        className={css.viewport}
        style={{
          left: Math.max(0, vpMM.x),
          top: Math.max(0, vpMM.y),
          width: Math.min(MM_W, vpMMW),
          height: Math.min(MM_H, vpMMH),
        }}
      />
      <div className={css.label}>Мини-карта</div>
    </div>
  );
}
