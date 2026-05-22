import { useState, useEffect, useRef } from "react";
import type { CanvasWidget } from "../../../api/canvas";

const STICKER_COLORS = [
  { label: "Жёлтый",   value: "#FFF3D6" },
  { label: "Синий",    value: "#E6F0FA" },
  { label: "Зелёный",  value: "#D1FAE5" },
  { label: "Розовый",  value: "#FCE7F3" },
  { label: "Фиолет.",  value: "#EDE9FE" },
  { label: "Серый",    value: "#F1F5F9" },
];

interface Props {
  widget: CanvasWidget;
  onDataChange: (data: Record<string, any>) => void;
}

export default function StickerWidget({ widget, onDataChange }: Props) {
  const { data } = widget;
  const [editing, setEditing] = useState(false);
  const [content, setContent] = useState(data.content || "");
  const [color, setColor] = useState(data.color || "#FFF3D6");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [editing]);

  const handleBlur = () => {
    setEditing(false);
    onDataChange({ ...data, content, color });
  };

  return (
    <div
      style={{
        height: "100%",
        background: color,
        borderRadius: "0 0 10px 10px",
        display: "flex",
        flexDirection: "column",
      }}
      onDoubleClick={() => setEditing(true)}
    >
      {/* Color picker */}
      <div
        style={{
          display: "flex",
          gap: 4,
          padding: "6px 10px",
          borderBottom: "1px solid rgba(0,0,0,.06)",
        }}
      >
        {STICKER_COLORS.map((c) => (
          <button
            key={c.value}
            title={c.label}
            onMouseDown={(e) => {
              e.stopPropagation();
              setColor(c.value);
              onDataChange({ ...data, content, color: c.value });
            }}
            style={{
              width: 14,
              height: 14,
              borderRadius: "50%",
              background: c.value,
              border: color === c.value ? "2px solid #6366f1" : "1.5px solid rgba(0,0,0,.12)",
              cursor: "pointer",
              padding: 0,
              flexShrink: 0,
            }}
          />
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, padding: "8px 10px", overflow: "hidden" }}>
        {editing ? (
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onBlur={handleBlur}
            onMouseDown={(e) => e.stopPropagation()}
            style={{
              width: "100%",
              height: "100%",
              border: "none",
              outline: "none",
              background: "transparent",
              resize: "none",
              fontFamily: "system-ui, sans-serif",
              fontSize: 13,
              lineHeight: 1.5,
              color: "#334155",
            }}
          />
        ) : (
          <div
            style={{
              fontSize: 13,
              lineHeight: 1.5,
              color: "#334155",
              whiteSpace: "pre-wrap",
              overflow: "hidden",
              height: "100%",
              cursor: "text",
            }}
          >
            {content || (
              <span style={{ color: "#94a3b8", fontStyle: "italic" }}>
                Двойной клик для редактирования…
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
