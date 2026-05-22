import api from "./client";
import type { Campaign, TrackingLink } from "./types";

export const fetchCampaigns = () =>
  api.get<{ items: Campaign[] } | Campaign[]>("/campaigns").then((r) =>
    Array.isArray(r.data) ? r.data : (r.data as { items: Campaign[] }).items ?? []
  );

export const fetchCampaign = (id: string) =>
  api.get<Campaign>(`/campaigns/${id}`).then((r) => r.data);

export const fetchTrackingLinks = (campaignId: string) =>
  api.get<TrackingLink[]>(`/campaigns/${campaignId}/links`).then((r) => r.data);

export const createCampaign = (payload: Partial<Campaign>) =>
  api.post<Campaign>("/campaigns", payload).then((r) => r.data);

export const patchCampaign = (id: string, patch: Partial<Campaign>) =>
  api.patch<Campaign>(`/campaigns/${id}`, patch).then((r) => r.data);
