import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchCampaign, fetchTrackingLinks } from "../api/campaigns";
import FunnelChart from "../components/campaign/FunnelChart";
import ClickToOrderHistogram from "../components/campaign/ClickToOrderHistogram";
import AttributionTable from "../components/campaign/AttributionTable";
import DateRangePicker from "../components/shared/DateRangePicker";
import styles from "./Page.module.css";
import cardStyles from "../components/dashboard/Chart.module.css";

export default function CampaignPage() {
  const { id } = useParams<{ id: string }>();

  const { data: campaign } = useQuery({
    queryKey: ["campaign", id],
    queryFn: () => fetchCampaign(id!),
    enabled: !!id,
  });

  const { data: links = [] } = useQuery({
    queryKey: ["tracking-links", id],
    queryFn: () => fetchTrackingLinks(id!),
    enabled: !!id,
  });

  if (!id) return null;

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <div>
          <h1 className={styles.heading}>{campaign?.name ?? "Кампания"}</h1>
          <p style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>
            {campaign?.marketplace} · {campaign?.ad_platform}
          </p>
        </div>
        <DateRangePicker />
      </div>

      <div className={styles.grid2}>
        <FunnelChart campaignId={id} />
        <ClickToOrderHistogram campaignId={id} />
      </div>

      <AttributionTable campaignId={id} />

      {links.length > 0 && (
        <div className={cardStyles.card}>
          <h3 className={cardStyles.title}>Трекинг-ссылки</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr>
                {["Метка", "Trax ID", "Ссылка", "Создана"].map((h) => (
                  <th key={h} style={{ textAlign: "left", padding: "8px 10px",
                    color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {links.map((link) => (
                <tr key={link.trax_id}>
                  <td style={{ padding: "8px 10px" }}>{link.label ?? "—"}</td>
                  <td style={{ padding: "8px 10px", fontFamily: "monospace", color: "var(--text-muted)" }}>{link.trax_id}</td>
                  <td style={{ padding: "8px 10px" }}>
                    <a href={link.tracking_url} target="_blank" rel="noreferrer"
                       style={{ color: "var(--accent)" }}>{link.tracking_url}</a>
                  </td>
                  <td style={{ padding: "8px 10px", color: "var(--text-muted)" }}>
                    {new Date(link.created_at).toLocaleDateString("ru")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
