import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getCampaignWidgetData } from "../../../api/canvas";
import type { CanvasWidget } from "../../../api/canvas";

interface Props {
  widget: CanvasWidget;
  onDataChange: (data: Record<string, any>) => void;
}

const AD_PLATFORM_ICONS: Record<string, string> = {
  yandex: "🟡",
  vk: "🔵",
  google: "🔴",
  mytarget: "🟠",
};

/** Mini spark-line as SVG */
function SparkLine({ color = "#6366f1" }: { color?: string }) {
  // Placeholder random data
  const pts = [20, 45, 30, 60, 40, 70, 55, 80, 65, 50, 75, 60];
  const max = Math.max(...pts);
  const min = Math.min(...pts);
  const w = 200;
  const h = 40;
  const scaleY = (v: number) => h - ((v - min) / (max - min + 1)) * h;
  const path = pts
    .map((v, i) => `${i === 0 ? "M" : "L"} ${(i / (pts.length - 1)) * w} ${scaleY(v)}`)
    .join(" ");

  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <path d={path} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

export default function AdConnectorWidget({ widget, onDataChange }: Props) {
  const { data } = widget;
  const [configuring, setConfiguring] = useState(!data.campaign_id && !data.label);
  const [campaignId, setCampaignId] = useState(data.campaign_id || "");
  const [label, setLabel] = useState(data.label || "");

  const { data: campaignData } = useQuery({
    queryKey: ["canvas-campaign", data.campaign_id],
    queryFn: () => getCampaignWidgetData(data.campaign_id!),
    enabled: !!data.campaign_id,
    retry: false,
  });

  const handleSave = () => {
    onDataChange({ ...data, campaign_id: campaignId, label });
    setConfiguring(false);
  };

  if (configuring) {
    return (
      <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 10, height: "100%" }}>
        <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600 }}>Рекламный коннектор</div>
        <input
          value={campaignId}
          onChange={(e) => setCampaignId(e.target.value)}
          onMouseDown={(e) => e.stopPropagation()}
          placeholder="ID кампании (необязательно)"
          style={inputStyle}
        />
        <input
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onMouseDown={(e) => e.stopPropagation()}
          placeholder="Название (напр. Яндекс.Директ)"
          style={inputStyle}
        />
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={handleSave}
          style={saveBtnStyle}
        >
          Сохранить
        </button>
      </div>
    );
  }

  // Use real campaign data if available, otherwise use label as placeholder
  const name = campaignData?.name || data.label || "Рекламная кампания";
  const platform = campaignData?.ad_platform || "ad";
  const isActive = campaignData?.is_active ?? true;
  const marketplace = campaignData?.marketplace || "";
  const platformIcon = AD_PLATFORM_ICONS[platform] || "📢";

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", padding: 14, gap: 8 }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 24 }}>{platformIcon}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#1e293b", lineHeight: 1.2 }}>
            {name}
          </div>
          {marketplace && (
            <div style={{ fontSize: 11, color: "#94a3b8" }}>{marketplace}</div>
          )}
        </div>
        {/* Active toggle (visual only) */}
        <div
          style={{
            background: isActive ? "#dcfce7" : "#fee2e2",
            color: isActive ? "#15803d" : "#dc2626",
            borderRadius: 20,
            padding: "2px 8px",
            fontSize: 10,
            fontWeight: 700,
          }}
        >
          {isActive ? "Активна" : "Стоп"}
        </div>
      </div>

      {/* ROMI placeholder */}
      <div style={{ textAlign: "center", margin: "4px 0" }}>
        <div style={{ fontSize: 32, fontWeight: 800, color: "#6366f1" }}>
          {data.romi ? `${data.romi}%` : "ROMI"}
        </div>
        <div style={{ fontSize: 11, color: "#94a3b8" }}>Рентабельность</div>
      </div>

      {/* Sparkline */}
      <div style={{ margin: "0 -4px" }}>
        <SparkLine color="#6366f1" />
      </div>

      {/* Metrics row */}
      <div style={{ display: "flex", gap: 6 }}>
        <MetricMini label="CPC" value={data.cpc || "—"} />
        <MetricMini label="Расход" value={data.spend ? `${Number(data.spend).toLocaleString("ru-RU")} ₽` : "—"} />
      </div>

      <button
        onMouseDown={(e) => e.stopPropagation()}
        onClick={() => setConfiguring(true)}
        style={{ background: "none", border: "none", cursor: "pointer", fontSize: 11, color: "#94a3b8", marginTop: "auto" }}
      >
        ⚙ Настроить
      </button>
    </div>
  );
}

function MetricMini({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        flex: 1,
        background: "#f8fafc",
        borderRadius: 6,
        padding: "5px 8px",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: 11, color: "#94a3b8" }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 700, color: "#1e293b" }}>{value}</div>
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
