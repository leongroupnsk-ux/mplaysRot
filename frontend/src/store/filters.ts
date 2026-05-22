import { create } from "zustand";
import { format, subDays } from "date-fns";

interface FiltersState {
  dateFrom: string;
  dateTo: string;
  marketplace: string;
  adPlatform: string;
  campaignId: string;
  setDateRange: (from: string, to: string) => void;
  setMarketplace: (v: string) => void;
  setAdPlatform: (v: string) => void;
  setCampaignId: (v: string) => void;
  reset: () => void;
}

const today = format(new Date(), "yyyy-MM-dd");
const thirtyDaysAgo = format(subDays(new Date(), 30), "yyyy-MM-dd");

export const useFilters = create<FiltersState>((set) => ({
  dateFrom: thirtyDaysAgo,
  dateTo: today,
  marketplace: "",
  adPlatform: "",
  campaignId: "",
  setDateRange: (dateFrom, dateTo) => set({ dateFrom, dateTo }),
  setMarketplace: (marketplace) => set({ marketplace }),
  setAdPlatform: (adPlatform) => set({ adPlatform }),
  setCampaignId: (campaignId) => set({ campaignId }),
  reset: () => set({ marketplace: "", adPlatform: "", campaignId: "" }),
}));
