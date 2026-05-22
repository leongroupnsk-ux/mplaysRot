import api from "./client";

export interface PublicPlan {
  id: string;
  slug: string;
  name: string;
  price_monthly: number;
  price_yearly: number;
  limits: Record<string, number>;
  features: string[];
  sort_order: number;
}

export interface UsageLimit {
  key: string;
  label: string;
  used: number;
  limit: number;
}

export interface UsageResponse {
  plan_slug: string;
  billing_period: string;
  status: string;
  current_period_end: string | null;
  limits: UsageLimit[];
}

export async function fetchPublicPlans(): Promise<PublicPlan[]> {
  const { data } = await api.get<PublicPlan[]>("/billing/tariffs/public");
  return data;
}

export async function fetchUsage(): Promise<UsageResponse> {
  const { data } = await api.get<UsageResponse>("/billing/usage");
  return data;
}

export async function subscribe(body: {
  plan_slug: string;
  billing_period: "monthly" | "yearly";
  promo_code?: string;
  return_url?: string;
}): Promise<{ subscription_id: string; payment_url: string | null; status: string }> {
  const { data } = await api.post("/billing/subscribe", body);
  return data;
}

export async function checkPromo(
  code: string,
  plan_slug: string
): Promise<{ valid: boolean; discount_pct: number; message: string }> {
  const { data } = await api.post("/billing/promo", { code, plan_slug });
  return data;
}
