import api from "./client";
import type { AttributionLogResponse } from "./types";

export const fetchAttributionLog = (params: {
  date_from: string; date_to: string;
  campaign_id?: string; marketplace?: string;
  min_confidence?: number; limit?: number; offset?: number;
}) =>
  api.get<AttributionLogResponse>("/attribution/log", { params }).then((r) => r.data);
