import { useQuery } from "@tanstack/react-query";
import { useFilters } from "../store/filters";
import {
  fetchOverview, fetchTimeseries, fetchFunnel,
  fetchGeo, fetchTopCreatives, fetchClickToOrderDistribution,
} from "../api/analytics";

export function useOverview() {
  const { dateFrom, dateTo, marketplace, adPlatform, campaignId } = useFilters();
  return useQuery({
    queryKey: ["overview", dateFrom, dateTo, marketplace, adPlatform, campaignId],
    queryFn: () =>
      fetchOverview({
        date_from: dateFrom, date_to: dateTo,
        marketplace: marketplace || undefined,
        ad_platform: adPlatform || undefined,
        campaign_id: campaignId || undefined,
        compare: true,
      }),
  });
}

export function useTimeseries(granularity: "day" | "week" = "day") {
  const { dateFrom, dateTo, marketplace, adPlatform, campaignId } = useFilters();
  return useQuery({
    queryKey: ["timeseries", dateFrom, dateTo, marketplace, adPlatform, campaignId, granularity],
    queryFn: () =>
      fetchTimeseries({
        date_from: dateFrom, date_to: dateTo,
        marketplace: marketplace || undefined,
        ad_platform: adPlatform || undefined,
        campaign_id: campaignId || undefined,
        granularity,
      }),
  });
}

export function useFunnel(campaignId: string) {
  const { dateFrom, dateTo } = useFilters();
  return useQuery({
    queryKey: ["funnel", campaignId, dateFrom, dateTo],
    queryFn: () => fetchFunnel({ campaign_id: campaignId, date_from: dateFrom, date_to: dateTo }),
    enabled: !!campaignId,
  });
}

export function useTopCreatives(limit = 10) {
  const { dateFrom, dateTo, adPlatform, campaignId } = useFilters();
  return useQuery({
    queryKey: ["top-creatives", dateFrom, dateTo, adPlatform, campaignId],
    queryFn: () =>
      fetchTopCreatives({
        date_from: dateFrom, date_to: dateTo,
        ad_platform: adPlatform || undefined,
        campaign_id: campaignId || undefined,
        limit,
      }),
  });
}

export function useClickToOrderDistribution(campaignId?: string) {
  const { dateFrom, dateTo } = useFilters();
  return useQuery({
    queryKey: ["c2o-dist", campaignId, dateFrom, dateTo],
    queryFn: () =>
      fetchClickToOrderDistribution({
        date_from: dateFrom, date_to: dateTo,
        campaign_id: campaignId,
      }),
    enabled: !!campaignId,
  });
}

export function useGeo() {
  const { dateFrom, dateTo, campaignId, marketplace } = useFilters();
  return useQuery({
    queryKey: ["geo", dateFrom, dateTo, campaignId, marketplace],
    queryFn: () =>
      fetchGeo({
        date_from: dateFrom, date_to: dateTo,
        campaign_id: campaignId || undefined,
        marketplace: marketplace || undefined,
      }),
  });
}
