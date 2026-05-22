import api from "./client";

export type IntegrationType = "marketplace" | "ad_platform";

export interface Integration {
  id: string;
  type: IntegrationType;
  provider: string;
  account_name: string | null;
  status: "pending" | "active" | "error";
  last_synced_at: string | null;
  created_at: string;

}

export interface ValidateResult {
  ok: boolean;
  message: string;
}

export const fetchIntegrations = () =>
  api.get<Integration[]>("/integrations").then((r) => r.data);

export const connectMarketplace = (payload: {
  provider: string;
  api_key: string;
  client_id?: string;
  seller_id?: string;
}) => api.post<Integration>("/integrations/marketplace", payload).then((r) => r.data);

export const connectAdPlatform = (payload: {
  provider: string;
  access_token: string;
  refresh_token?: string;
  account_id?: string;
  account_name?: string;
}) => api.post<Integration>("/integrations/ad", payload).then((r) => r.data);

export const deleteIntegration = (id: string) =>
  api.delete(`/integrations/${id}`);

export const validateIntegration = (id: string) =>
  api.post<ValidateResult>(`/integrations/${id}/validate`).then((r) => r.data);
