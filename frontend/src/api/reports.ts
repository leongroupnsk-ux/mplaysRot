import axios from "axios";

const REPORTING_BASE = import.meta.env.VITE_REPORTING_URL ?? "/api/reporting";

export type ReportType = "attribution" | "overview" | "campaigns";

export interface ExportResponse {
  url: string;
  filename: string;
  expires_at: string;
  rows: number;
}

export async function exportReport(params: {
  type: ReportType;
  date_from: string;
  date_to: string;
  campaign_id?: string;
}): Promise<ExportResponse> {
  const token = localStorage.getItem("access_token");
  const search = new URLSearchParams({
    type: params.type,
    date_from: params.date_from,
    date_to: params.date_to,
    ...(params.campaign_id ? { campaign_id: params.campaign_id } : {}),
  });
  const res = await axios.post<ExportResponse>(
    `${REPORTING_BASE}/reports/export?${search}`,
    null,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.data;
}
