import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCampaigns } from "../api/campaigns";
import { fetchSegments } from "../api/segments";
import SegmentCard from "../components/audience/SegmentCard";
import styles from "./Page.module.css";

export default function AudiencePage() {
  const { data: campaigns = [] } = useQuery({
    queryKey: ["campaigns"],
    queryFn: fetchCampaigns,
  });

  const [selectedCampaign, setSelectedCampaign] = useState(campaigns[0]?.id ?? "");

  useEffect(() => {
    if (!selectedCampaign && campaigns.length > 0) {
      setSelectedCampaign(campaigns[0].id);
    }
  }, [campaigns, selectedCampaign]);

  const { data: segments = [] } = useQuery({
    queryKey: ["segments", selectedCampaign],
    queryFn: () => fetchSegments({ campaign_id: selectedCampaign }),
    enabled: !!selectedCampaign,
    refetchInterval: 10_000,
  });

  const campaignSegments = segments;

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <h1 className={styles.heading}>Аудитории</h1>
        {campaigns.length > 0 && (
          <select
            value={selectedCampaign}
            onChange={(e) => setSelectedCampaign(e.target.value)}
            style={{
              minWidth: 200,
              padding: "7px 12px",
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              color: "var(--text)",
              fontSize: 13,
            }}
          >
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        )}
      </div>

      {campaigns.length === 0 ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "80px 24px",
            gap: 16,
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 56 }}>👥</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "var(--text)" }}>
            Нет аудиторий
          </div>
          <div style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: 360 }}>
            Создайте рекламную кампанию и подключите магазин — MPlays автоматически
            сформирует сегменты покупателей по поведению и источнику трафика.
          </div>
          <a
            href="/campaigns"
            style={{
              marginTop: 8,
              padding: "10px 24px",
              background: "var(--accent)",
              color: "#fff",
              borderRadius: 9,
              fontSize: 13,
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            Перейти в Кампании
          </a>
        </div>
      ) : selectedCampaign ? (
        <SegmentCard campaignId={selectedCampaign} segments={campaignSegments} />
      ) : null}
    </div>
  );
}
