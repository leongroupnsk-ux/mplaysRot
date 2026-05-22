import api from "./client";
import type { SegmentUpload } from "./types";

export const fetchSegments = (params?: { campaign_id?: string; status?: string }) =>
  api.get<SegmentUpload[]>("/segments", { params }).then((r) => r.data);

export const uploadSegment = (payload: {
  campaign_id: string; ad_platform: string;
  min_roas_threshold?: number; lookalike?: boolean; lookalike_scale?: number;
}) =>
  api.post<SegmentUpload>("/segments/upload", payload).then((r) => r.data);
