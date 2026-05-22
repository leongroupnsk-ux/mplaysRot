import api from "./client";

export interface Store {
  id: string;
  connection_id: string;
  provider: string;
  external_store_id: string;
  name: string;
  logo_url: string | null;
  is_active: boolean;
  last_sync_at: string | null;
  created_at: string;
}

export const fetchStores = () =>
  api.get<Store[]>("/stores").then((r) => r.data);
