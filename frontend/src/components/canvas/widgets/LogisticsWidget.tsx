import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getLogisticsWidgetData } from "../../../api/canvas";
import type { Store } from "../../../api/stores";
import type { CanvasWidget } from "../../../api/canvas";

interface Props {
  widget: CanvasWidget;
  onDataChange: (data: Record<string, any>) => void;
}

const STATUS_CONFIG = {
  ok:       { color: "#22c55e", bg: "#dcfce7", label: "Норма",    icon: "✅" },
  warn:     { color: "#f59e0b", bg: "#fef3c7", label: "Внимание", icon: "⚠️" },
  critical: { color: "#ef4444", bg: "#fee2e2", label: "Дефицит",  icon: "🔴" },
};

export default function LogisticsWidget({ widget, onDataChange }: Props) {
  const { data } = widget;
  const [configuring, setConfiguring] = useState(!data.store_id || !data.external_product_id);
  const [storeId, setStoreId] = useState(data.store_id || "");
  const [sku, setSku] = useState(data.external_product_id || "");

  const { data: stores = [] } = useQuery<Store[]>({
    queryKey: ["stores"],
    queryFn: () => import("../../../api/stores").then((m) => m.fetchStores()) as Promise<Store[]>,
  });

  const { data: logData, isLoading, isError } = useQuery({
    queryKey: ["canvas-logistics", data.store_id, data.external_product_id],
    queryFn: () => getLogisticsWidgetData(data.store_id!, data.external_product_id!),
    enabled: !!data.store_id && !!data.external_product_id,
    retry: false,
  });

  const handleSave = () => {
    onDataChange({ ...data, store_id: storeId, external_product_id: sku });
    setConfiguring(false);
  };

  if (configuring) {
    return (
      <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 10, height: "100%" }}>
        <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600 }}>Выберите товар</div>
        <select
          value={storeId}
          onChange={(e) => setStoreId(e.target.value)}
          onMouseDown={(e) => e.stopPropagation()}
          style={inputStyle}
        >
          <option value="">Магазин…</option>
          {stores.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <input
          value={sku}
          onChange={(e) => setSku(e.target.value)}
          onMouseDown={(e) => e.stopPropagation()}
          placeholder="Артикул (SKU)"
          style={inputStyle}
        />
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={handleSave}
          disabled={!storeId || !sku}
          style={saveBtnStyle}
        >
          Загрузить данные
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div style={centerStyle}>
        <div style={{ fontSize: 24 }}>⏳</div>
        <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 6 }}>Загрузка…</div>
      </div>
    );
  }

  if (isError || !logData) {
    return (
      <div style={centerStyle}>
        <div style={{ fontSize: 24 }}>❌</div>
        <div style={{ fontSize: 12, color: "#ef4444", marginTop: 6 }}>Товар не найден</div>
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => setConfiguring(true)}
          style={{ ...saveBtnStyle, marginTop: 10 }}
        >
          Изменить
        </button>
      </div>
    );
  }

  const sc = STATUS_CONFIG[logData.status] ?? STATUS_CONFIG.ok;

  return (
    <div
      style={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: 14,
        gap: 10,
      }}
    >
      {/* Title */}
      <div style={{ fontSize: 12, fontWeight: 600, color: "#1e293b", lineHeight: 1.3 }}>
        {logData.title}
      </div>
      <div style={{ fontSize: 11, color: "#94a3b8" }}>SKU: {logData.external_product_id}</div>

      {/* Status badge */}
      <div
        style={{
          background: sc.bg,
          color: sc.color,
          borderRadius: 8,
          padding: "6px 12px",
          display: "flex",
          alignItems: "center",
          gap: 6,
          fontWeight: 700,
          fontSize: 13,
        }}
      >
        <span>{sc.icon}</span>
        <span>{sc.label}</span>
      </div>

      {/* Big stock number */}
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 40, fontWeight: 800, color: sc.color, lineHeight: 1 }}>
          {logData.stock}
        </div>
        <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>единиц на складе</div>
      </div>

      {/* Warehouse label from data */}
      {data.warehouse && (
        <div
          style={{
            background: "#f1f5f9",
            borderRadius: 6,
            padding: "4px 10px",
            fontSize: 11,
            color: "#64748b",
            textAlign: "center",
          }}
        >
          📍 {data.warehouse}
        </div>
      )}

      {/* Action */}
      <a
        href="/logistics"
        onMouseDown={(e) => e.stopPropagation()}
        style={{
          marginTop: "auto",
          display: "block",
          textAlign: "center",
          padding: "7px",
          border: "1.5px solid #e2e8f0",
          borderRadius: 7,
          fontSize: 12,
          color: "#6366f1",
          fontWeight: 600,
          textDecoration: "none",
          cursor: "pointer",
        }}
      >
        Открыть в Logistics Tracker
      </a>

      <button
        onMouseDown={(e) => e.stopPropagation()}
        onClick={() => setConfiguring(true)}
        style={{ background: "none", border: "none", cursor: "pointer", fontSize: 11, color: "#94a3b8" }}
      >
        ⚙ Изменить товар
      </button>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "7px 10px",
  border: "1px solid #e2e8f0",
  borderRadius: 7,
  fontSize: 12,
  background: "#f8fafc",
  color: "#334155",
  width: "100%",
};

const saveBtnStyle: React.CSSProperties = {
  padding: "8px",
  background: "#6366f1",
  color: "#fff",
  border: "none",
  borderRadius: 7,
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
  width: "100%",
};

const centerStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  height: "100%",
  padding: 16,
};
