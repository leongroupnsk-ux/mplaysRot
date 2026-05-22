import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getProductWidgetData } from "../../../api/canvas";
import type { Store } from "../../../api/stores";
import type { CanvasWidget } from "../../../api/canvas";

interface Props {
  widget: CanvasWidget;
  onDataChange: (data: Record<string, any>) => void;
}

function StockBar({ stock }: { stock: number }) {
  const level = stock > 30 ? "ok" : stock > 10 ? "warn" : "critical";
  const colors = { ok: "#22c55e", warn: "#f59e0b", critical: "#ef4444" };
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div
        style={{
          flex: 1,
          height: 4,
          background: "#e2e8f0",
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.min(100, (stock / 100) * 100)}%`,
            height: "100%",
            background: colors[level],
            borderRadius: 2,
          }}
        />
      </div>
      <span style={{ fontSize: 11, color: colors[level], fontWeight: 600 }}>{stock}</span>
    </div>
  );
}

export default function ProductCardWidget({ widget, onDataChange }: Props) {
  const { data } = widget;
  const [configuring, setConfiguring] = useState(!data.store_id || !data.external_product_id);
  const [storeId, setStoreId] = useState(data.store_id || "");
  const [sku, setSku] = useState(data.external_product_id || "");

  const { data: stores = [] } = useQuery<Store[]>({
    queryKey: ["stores"],
    queryFn: () => import("../../../api/stores").then((m) => m.fetchStores()) as Promise<Store[]>,
  });

  const { data: product, isLoading, isError } = useQuery({
    queryKey: ["canvas-product", data.store_id, data.external_product_id],
    queryFn: () => getProductWidgetData(data.store_id!, data.external_product_id!),
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

  if (isError || !product) {
    return (
      <div style={centerStyle}>
        <div style={{ fontSize: 24 }}>❌</div>
        <div style={{ fontSize: 12, color: "#ef4444", marginTop: 6, textAlign: "center" }}>
          Товар не найден
        </div>
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => setConfiguring(true)}
          style={{ ...saveBtnStyle, marginTop: 10, width: "auto" }}
        >
          Изменить SKU
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Image */}
      {product.image_url ? (
        <img
          src={product.image_url}
          alt={product.title}
          style={{ width: "100%", height: 110, objectFit: "cover" }}
        />
      ) : (
        <div
          style={{
            height: 110,
            background: "#f1f5f9",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 36,
          }}
        >
          🛍
        </div>
      )}

      {/* Info */}
      <div style={{ padding: "10px 12px", flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={{ fontSize: 13, fontWeight: 600, lineHeight: 1.3, color: "#1e293b" }}>
          {product.title}
        </div>
        <div style={{ fontSize: 11, color: "#94a3b8" }}>SKU: {product.external_product_id}</div>

        {product.price && (
          <div style={{ fontSize: 16, fontWeight: 700, color: "#0f172a" }}>
            {Number(product.price).toLocaleString("ru-RU")} ₽
          </div>
        )}

        {/* Metrics */}
        <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>
            Остатки
          </div>
          <StockBar stock={product.stock} />
          <div
            style={{
              display: "flex",
              gap: 8,
              flexWrap: "wrap",
              marginTop: 4,
            }}
          >
            <MetricChip
              label="Маркетплейс"
              value={product.marketplace === "wildberries" ? "WB" : product.marketplace || "—"}
              color="#ede9fe"
              textColor="#5b21b6"
            />
            <MetricChip
              label="Магазин"
              value={product.store_name?.slice(0, 12) || "—"}
              color="#dbeafe"
              textColor="#1e40af"
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          borderTop: "1px solid #f1f5f9",
          padding: "6px 12px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: 11,
          color: "#94a3b8",
        }}
      >
        <span>Обновлено только что</span>
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => setConfiguring(true)}
          style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", fontSize: 14 }}
        >
          ⚙
        </button>
      </div>
    </div>
  );
}

function MetricChip({
  label,
  value,
  color,
  textColor,
}: {
  label: string;
  value: string;
  color: string;
  textColor: string;
}) {
  return (
    <div
      title={label}
      style={{
        background: color,
        color: textColor,
        padding: "2px 7px",
        borderRadius: 6,
        fontSize: 11,
        fontWeight: 600,
      }}
    >
      {value}
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
