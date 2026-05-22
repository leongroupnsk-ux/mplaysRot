import { useState } from "react";
import type { Viewport } from "./InfiniteCanvas";
import css from "./CanvasToolbar.module.css";

interface Props {
  title: string;
  viewport: Viewport;
  isAIPanelOpen: boolean;
  isWidgetPanelOpen: boolean;
  isTemplatesPanelOpen: boolean;
  onTitleChange: (title: string) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomReset: () => void;
  onFitAll: () => void;
  onToggleWidgets: () => void;
  onToggleTemplates: () => void;
  onToggleAI: () => void;
  onShare: () => void;
  onExport: () => void;
}

export default function CanvasToolbar({
  title,
  viewport,
  isAIPanelOpen,
  isWidgetPanelOpen,
  isTemplatesPanelOpen,
  onTitleChange,
  onZoomIn,
  onZoomOut,
  onZoomReset,
  onFitAll,
  onToggleWidgets,
  onToggleTemplates,
  onToggleAI,
  onShare,
  onExport,
}: Props) {
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleVal, setTitleVal] = useState(title);

  const commitTitle = () => {
    setEditingTitle(false);
    if (titleVal.trim()) onTitleChange(titleVal.trim());
    else setTitleVal(title);
  };

  return (
    <div className={css.toolbar}>
      {/* Logo */}
      <span style={{ fontSize: 18, flexShrink: 0 }}>🎨</span>

      {/* Board title */}
      {editingTitle ? (
        <input
          className={css.boardTitleInput}
          value={titleVal}
          onChange={(e) => setTitleVal(e.target.value)}
          onBlur={commitTitle}
          onKeyDown={(e) => {
            if (e.key === "Enter") commitTitle();
            if (e.key === "Escape") { setEditingTitle(false); setTitleVal(title); }
          }}
          autoFocus
        />
      ) : (
        <div
          className={css.boardTitle}
          title="Дважды кликните для переименования"
          onDoubleClick={() => { setEditingTitle(true); setTitleVal(title); }}
        >
          {title}
        </div>
      )}

      <div className={css.divider} />

      {/* Widget panel toggle */}
      <button
        className={`${css.iconBtn} ${isWidgetPanelOpen ? css.active : ""}`}
        onClick={onToggleWidgets}
        title="Виджеты"
      >
        🧩 Виджеты
      </button>

      {/* Templates */}
      <button
        className={`${css.iconBtn} ${isTemplatesPanelOpen ? css.active : ""}`}
        onClick={onToggleTemplates}
        title="Шаблоны"
      >
        📋 Шаблоны
      </button>

      {/* AI */}
      <button
        className={`${css.iconBtn} ${isAIPanelOpen ? css.active : ""}`}
        onClick={onToggleAI}
        title="AI-ассистент"
      >
        🤖 AI-ассистент
      </button>

      <div className={css.divider} />

      {/* Zoom controls */}
      <div className={css.zoomGroup}>
        <button className={css.zoomBtn} onClick={onZoomOut} title="Уменьшить">−</button>
        <span
          className={css.zoomLabel}
          onClick={onZoomReset}
          title="Сбросить масштаб"
        >
          {Math.round(viewport.zoom * 100)}%
        </span>
        <button className={css.zoomBtn} onClick={onZoomIn} title="Увеличить">+</button>
      </div>

      <button className={css.iconBtn} onClick={onFitAll} title="Вписать всё в экран">
        ⊡
      </button>

      <div className={css.spacer} />

      {/* Hints */}
      <span className={css.hint}>
        Space+перетащить — пан · Колёсико — зум
      </span>

      <div className={css.divider} />

      {/* Share */}
      <button className={css.iconBtn} onClick={onShare}>
        🔗 Поделиться
      </button>

      {/* Export (placeholder) */}
      <button className={css.iconBtn} onClick={onExport}>
        ⬇ Экспорт
      </button>
    </div>
  );
}
