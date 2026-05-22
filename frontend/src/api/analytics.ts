import api from "./client";
import type {
  OverviewResponse, FunnelResponse, TimeSeriesPoint,
  GeoPoint, TopCreativeRow, ClickToOrderBucket,
} from "./types";

export const fetchOverview = (params: {
  date_from: string; date_to: string;
  marketplace?: string; ad_platform?: string;
  campaign_id?: string; compare?: boolean;
}) =>
  api.get<OverviewResponse>("/analytics/overview", { params }).then((r) => r.data);

export const fetchTimeseries = (params: {
  date_from: string; date_to: string;
  marketplace?: string; ad_platform?: string;
  campaign_id?: string; granularity?: "day" | "week";
}) =>
  api.get<TimeSeriesPoint[]>("/analytics/timeseries", { params }).then((r) => r.data);

export const fetchFunnel = (params: {
  campaign_id: string; date_from: string; date_to: string;
}) =>
  api.get<FunnelResponse>("/analytics/funnel", { params }).then((r) => r.data);

export const fetchGeo = (params: {
  date_from: string; date_to: string;
  campaign_id?: string; marketplace?: string;
}) =>
  api.get<GeoPoint[]>("/analytics/geo", { params }).then((r) => r.data);

export const fetchTopCreatives = (params: {
  date_from: string; date_to: string;
  ad_platform?: string; campaign_id?: string; limit?: number;
}) =>
  api.get<TopCreativeRow[]>("/analytics/top-creatives", { params }).then((r) => r.data);

export const fetchClickToOrderDistribution = (params: {
  date_from: string; date_to: string; campaign_id?: string;
}) =>
  api
    .get<ClickToOrderBucket[]>("/analytics/click-to-order-distribution", { params })
    .then((r) => r.data);
