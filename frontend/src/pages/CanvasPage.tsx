/**
 * CanvasPage — the MPlays Canvas entry point.
 *
 * URL: /canvas               → shows boards picker
 * URL: /canvas/:boardId      → opens that board
 * URL: /canvas?new           → directly opens template chooser
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate, useSearchParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listBoards,
  createBoard,
  getBoard,
  updateBoard,
  deleteBoard,
  addWidget,
  updateWidget,
  deleteWidget,
  addConnection,
  deleteConnection,
  toggleShareBoard,
  type CanvasBoard,
  type CanvasBoardDetail,
  type CanvasWidget,
  type WidgetType,
} from "../api/canvas";
import type { Viewport } from "../components/canvas/InfiniteCanvas";
import InfiniteCanvas from "../components/canvas/InfiniteCanvas";
import CanvasToolbar from "../components/canvas/CanvasToolbar";
import WidgetPanel from "../components/canvas/WidgetPanel";
import AIAssistantPanel from "../components/canvas/AIAssistantPanel";
import TemplatesPanel from "../components/canvas/TemplatesPanel";
import MiniMap from "../components/canvas/MiniMap";
import css from "./CanvasPage.module.css";

// ── Breadcrumb ────────────────────────────────────────────────────────────────

function Breadcrumb({ boardTitle }: { boardTitle?: string }) {
  return (
    <nav className={css.breadcrumb} aria-label="Навигация">
      <span className={css.breadcrumbItem}>
        <Link to="/dashboard" className={css.breadcrumbLink}>
          ⌂ Главное меню
        </Link>
      </span>
      <span className={css.breadcrumbSep}>›</span>
      <span className={css.breadcrumbItem}>
        {boardTitle ? (
          <Link to="/canvas" className={css.breadcrumbLink}>
            🎨 Canvas
          </Link>
        ) : (
          <span className={css.breadcrumbCurrent}>🎨 Canvas</span>
        )}
      </span>
      {boardTitle && (
        <>
          <span className={css.breadcrumbSep}>›</span>
          <span className={css.breadcrumbItem}>
            <span className={css.breadcrumbCurrent} title={boardTitle}>
              {boardTitle}
            </span>
          </span>
        </>
      )}
    </nav>
  );
}

const MIN_ZOOM = 0.1;
const MAX_ZOOM = 5;
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

// Debounce viewport save (don't hit the API on every wheel event)
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debouncedValue;
}

export default function CanvasPage() {
  const { boardId } = useParams<{ boardId?: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const qc = useQueryClient();

  const [activeBoardId, setActiveBoardId] = useState<string | null>(boardId ?? null);
  const [showTemplates, setShowTemplates] = useState(!!searchParams.get("new"));
  const [isWidgetPanelOpen, setIsWidgetPanelOpen] = useState(true);
  const [isAIPanelOpen, setIsAIPanelOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ w: 1200, h: 800 });

  // Board detail state
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, zoom: 1 });
  const [widgets, setWidgets] = useState<CanvasWidget[]>([]);
  const [connectionsState, setConnectionsState] = useState<any[]>([]);

  // ── Container size observer ───────────────────────────────
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => {
      setContainerSize({ w: el.clientWidth, h: el.clientHeight });
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // ── Load boards list ──────────────────────────────────────
  const { data: boards = [], isLoading: boardsLoading } = useQuery<CanvasBoard[]>({
    queryKey: ["canvas-boards"],
    queryFn: listBoards,
    enabled: !activeBoardId,
  });

  // ── Load active board ─────────────────────────────────────
  const { data: boardDetail } = useQuery<CanvasBoardDetail>({
    queryKey: ["canvas-board", activeBoardId],
    queryFn: () => getBoard(activeBoardId!),
    enabled: !!activeBoardId,
  });

  // Sync board detail into local state when loaded/changed
  useEffect(() => {
    if (!boardDetail) return;
    setWidgets(boardDetail.widgets);
    setConnectionsState(boardDetail.connections);
    setViewport({
      x: boardDetail.viewport_x,
      y: boardDetail.viewport_y,
      zoom: boardDetail.viewport_zoom,
    });
  }, [boardDetail?.id]); // only re-sync on board change, not on every re-render

  // ── Viewport persistence (debounced) ─────────────────────
  const debouncedViewport = useDebounce(viewport, 1500);
  useEffect(() => {
    if (!activeBoardId) return;
    updateBoard(activeBoardId, {
      viewport_x: debouncedViewport.x,
      viewport_y: debouncedViewport.y,
      viewport_zoom: debouncedViewport.zoom,
    }).catch(() => {});
  }, [debouncedViewport, activeBoardId]);

  // ── Create board ──────────────────────────────────────────
  const createMut = useMutation({
    mutationFn: createBoard,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["canvas-boards"] });
      setActiveBoardId(data.id);
      setWidgets(data.widgets);
      setConnectionsState(data.connections);
      setViewport({ x: data.viewport_x, y: data.viewport_y, zoom: data.viewport_zoom });
      navigate(`/canvas/${data.id}`, { replace: true });
    },
  });

  const deleteBoardMut = useMutation({
    mutationFn: deleteBoard,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["canvas-boards"] });
    },
  });

  // ── Widget mutations ──────────────────────────────────────
  const addWidgetMut = useMutation({
    mutationFn: (payload: Parameters<typeof addWidget>[1] & { board_id: string }) => {
      const { board_id, ...rest } = payload;
      return addWidget(board_id, rest);
    },
    onSuccess: (widget) => {
      setWidgets((prev) => [...prev, widget]);
    },
  });

  const updateWidgetMut = useMutation({
    mutationFn: ({
      widgetId,
      data,
    }: {
      widgetId: string;
      data: Parameters<typeof updateWidget>[2];
    }) => updateWidget(activeBoardId!, widgetId, data),
  });

  const deleteWidgetMut = useMutation({
    mutationFn: (widgetId: string) => deleteWidget(activeBoardId!, widgetId),
    onSuccess: (_, widgetId) => {
      setWidgets((prev) => prev.filter((w) => w.id !== widgetId));
      setConnectionsState((prev) =>
        prev.filter((c) => c.from_widget_id !== widgetId && c.to_widget_id !== widgetId)
      );
    },
  });

  // ── Connection mutations ──────────────────────────────────
  const addConnMut = useMutation({
    mutationFn: (payload: { from_widget_id: string; to_widget_id: string }) =>
      addConnection(activeBoardId!, payload),
    onSuccess: (conn) => {
      setConnectionsState((prev) => [...prev, conn]);
    },
  });

  const deleteConnMut = useMutation({
    mutationFn: (connId: string) => deleteConnection(activeBoardId!, connId),
    onSuccess: (_, connId) => {
      setConnectionsState((prev) => prev.filter((c) => c.id !== connId));
    },
  });

  // ── Handlers ─────────────────────────────────────────────

  const handleWidgetMove = useCallback(
    (id: string, x: number, y: number) => {
      setWidgets((prev) =>
        prev.map((w) => (w.id === id ? { ...w, x, y } : w))
      );
      updateWidgetMut.mutate({ widgetId: id, data: { x, y } });
    },
    [updateWidgetMut]
  );

  const handleWidgetDelete = useCallback(
    (id: string) => {
      deleteWidgetMut.mutate(id);
    },
    [deleteWidgetMut]
  );

  const handleWidgetDataChange = useCallback(
    (id: string, data: Record<string, any>) => {
      setWidgets((prev) =>
        prev.map((w) => (w.id === id ? { ...w, data: { ...w.data, ...data } } : w))
      );
      updateWidgetMut.mutate({ widgetId: id, data: { data } });
    },
    [updateWidgetMut]
  );

  const handleAddWidget = useCallback(
    (
      type: WidgetType,
      size: { w: number; h: number },
      data?: Record<string, any>,
      style?: Record<string, any>
    ) => {
      if (!activeBoardId) return;
      // Place in the viewport center (world coords)
      const cx = (containerSize.w / 2 - viewport.x) / viewport.zoom;
      const cy = (containerSize.h / 2 - viewport.y) / viewport.zoom;
      addWidgetMut.mutate({
        board_id: activeBoardId,
        widget_type: type,
        x: cx - size.w / 2,
        y: cy - size.h / 2,
        width: size.w,
        height: size.h,
        data: data || {},
        style: style || {},
      });
    },
    [activeBoardId, viewport, containerSize, addWidgetMut]
  );

  const handleAddWidgetAt = useCallback(
    (
      type: WidgetType,
      size: { w: number; h: number },
      wx: number,
      wy: number,
      data?: Record<string, any>
    ) => {
      if (!activeBoardId) return;
      addWidgetMut.mutate({
        board_id: activeBoardId,
        widget_type: type,
        x: wx,
        y: wy,
        width: size.w,
        height: size.h,
        data: data || {},
        style: {},
      });
    },
    [activeBoardId, addWidgetMut]
  );

  // Zoom helpers
  const zoomIn = () => setViewport((v) => ({ ...v, zoom: clamp(v.zoom * 1.2, MIN_ZOOM, MAX_ZOOM) }));
  const zoomOut = () => setViewport((v) => ({ ...v, zoom: clamp(v.zoom / 1.2, MIN_ZOOM, MAX_ZOOM) }));
  const zoomReset = () => setViewport((v) => ({ ...v, zoom: 1, x: 0, y: 0 }));

  const fitAll = () => {
    if (widgets.length === 0) { zoomReset(); return; }
    const padding = 80;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const w of widgets) {
      minX = Math.min(minX, w.x);
      minY = Math.min(minY, w.y);
      maxX = Math.max(maxX, w.x + w.width);
      maxY = Math.max(maxY, w.y + w.height);
    }
    const worldW = maxX - minX + padding * 2;
    const worldH = maxY - minY + padding * 2;
    const zoom = clamp(
      Math.min(containerSize.w / worldW, containerSize.h / worldH),
      MIN_ZOOM, MAX_ZOOM
    );
    setViewport({
      zoom,
      x: (containerSize.w - worldW * zoom) / 2 - (minX - padding) * zoom,
      y: (containerSize.h - worldH * zoom) / 2 - (minY - padding) * zoom,
    });
  };

  const handleShare = async () => {
    if (!activeBoardId) return;
    const board = await toggleShareBoard(activeBoardId);
    if (board.share_token) {
      const url = `${window.location.origin}/canvas/shared/${board.share_token}`;
      navigator.clipboard.writeText(url).then(() => {
        setToast("Ссылка скопирована! " + url);
        setTimeout(() => setToast(null), 3000);
      });
    } else {
      setToast("Публичный доступ отключён.");
      setTimeout(() => setToast(null), 2000);
    }
  };

  const handleTitleChange = (title: string) => {
    if (!activeBoardId) return;
    updateBoard(activeBoardId, { title }).catch(() => {});
    qc.invalidateQueries({ queryKey: ["canvas-boards"] });
  };

  const handleSelectTemplate = (templateId: string | null, title: string) => {
    setShowTemplates(false);
    createMut.mutate({ title, template_id: templateId || undefined });
  };

  const openBoard = (board: CanvasBoard) => {
    setActiveBoardId(board.id);
    navigate(`/canvas/${board.id}`);
  };

  const closeBoard = () => {
    setActiveBoardId(null);
    setWidgets([]);
    setConnectionsState([]);
    navigate("/canvas");
  };

  // ── Render: boards picker ─────────────────────────────────
  if (!activeBoardId) {
    return (
      <div className={css.shell}>
        <Breadcrumb />
        {/* Background canvas preview */}
        <div
          style={{
            flex: 1,
            background: "radial-gradient(circle, rgba(0,0,0,.06) 1.5px, transparent 1.5px) 0 0 / 32px 32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div className={css.boardsModal}>
            <div className={css.boardsHeader}>
              <div>
                <div className={css.boardsTitle}>🎨 MPlays Canvas</div>
                <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 2 }}>
                  Ваши рабочие пространства
                </div>
              </div>
              <button
                className={css.btnNew}
                onClick={() => setShowTemplates(true)}
                disabled={createMut.isPending}
              >
                + Новый канвас
              </button>
            </div>

            <div className={css.boardsList}>
              {boardsLoading && (
                <div className={css.emptyBoards}>
                  <div>Загрузка…</div>
                </div>
              )}

              {!boardsLoading && boards.length === 0 && (
                <div className={css.emptyBoards}>
                  <div className={css.emptyIcon}>🎨</div>
                  <div style={{ fontWeight: 600, color: "#1e293b", marginBottom: 8 }}>
                    Нет канвасов
                  </div>
                  <div>Создайте первое рабочее пространство</div>
                </div>
              )}

              {boards.map((board) => (
                <div
                  key={board.id}
                  className={css.boardCard}
                  onClick={() => openBoard(board)}
                >
                  <div className={css.boardCardEmoji}>🎨</div>
                  <div className={css.boardCardTitle}>{board.title}</div>
                  <div className={css.boardCardMeta}>
                    {new Date(board.updated_at).toLocaleDateString("ru-RU")}
                  </div>
                  <button
                    className={css.boardCardDelete}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Удалить «${board.title}»?`)) {
                        deleteBoardMut.mutate(board.id);
                      }
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {showTemplates && (
          <TemplatesPanel
            onClose={() => setShowTemplates(false)}
            onSelectTemplate={handleSelectTemplate}
          />
        )}
      </div>
    );
  }

  // ── Render: canvas ────────────────────────────────────────
  const boardTitle = boardDetail?.title ?? "Канвас";

  return (
    <div className={css.shell}>
      <Breadcrumb boardTitle={boardTitle} />
      <CanvasToolbar
        title={boardTitle}
        viewport={viewport}
        isAIPanelOpen={isAIPanelOpen}
        isWidgetPanelOpen={isWidgetPanelOpen}
        isTemplatesPanelOpen={false}
        onTitleChange={handleTitleChange}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onZoomReset={zoomReset}
        onFitAll={fitAll}
        onToggleWidgets={() => setIsWidgetPanelOpen((v) => !v)}
        onToggleTemplates={() => setShowTemplates(true)}
        onToggleAI={() => setIsAIPanelOpen((v) => !v)}
        onShare={handleShare}
        onExport={() => {
          setToast("Экспорт в PNG будет доступен в следующей версии.");
          setTimeout(() => setToast(null), 2500);
        }}
      />

      <div className={css.canvasArea}>
        {/* Back to boards list */}
        <button className={css.backBtn} onClick={closeBoard} title="Все канвасы">
          ⊞ Все канвасы
        </button>

        {/* Widget panel */}
        {isWidgetPanelOpen && (
          <WidgetPanel onAddWidget={handleAddWidget} />
        )}

        {/* Canvas */}
        <div ref={containerRef} style={{ flex: 1, position: "relative", overflow: "hidden" }}>
          <InfiniteCanvas
            widgets={widgets}
            connections={connectionsState}
            viewport={viewport}
            onViewportChange={setViewport}
            onWidgetMove={handleWidgetMove}
            onWidgetDelete={handleWidgetDelete}
            onWidgetDataChange={handleWidgetDataChange}
            onConnectionCreate={(fromId, toId) => addConnMut.mutate({ from_widget_id: fromId, to_widget_id: toId })}
            onConnectionDelete={(id) => deleteConnMut.mutate(id)}
          />

          <MiniMap
            widgets={widgets}
            viewport={viewport}
            containerWidth={containerSize.w}
            containerHeight={containerSize.h}
            onNavigate={setViewport}
          />
        </div>

        {/* AI panel */}
        {isAIPanelOpen && (
          <AIAssistantPanel
            boardId={activeBoardId}
            onAddWidget={handleAddWidgetAt}
          />
        )}
      </div>

      {/* Templates panel */}
      {showTemplates && (
        <TemplatesPanel
          onClose={() => setShowTemplates(false)}
          onSelectTemplate={handleSelectTemplate}
        />
      )}

      {/* Toast */}
      {toast && <div className={css.toast}>{toast}</div>}
    </div>
  );
}
