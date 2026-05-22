import { describe, it, expect, beforeEach } from "vitest";
import { useFilters } from "./filters";

beforeEach(() => {
  useFilters.setState({
    dateFrom: "2024-01-01",
    dateTo: "2024-01-31",
    marketplace: "",
    adPlatform: "",
    campaignId: "",
  });
});

describe("useFilters store", () => {
  it("has default state", () => {
    const { marketplace, adPlatform, campaignId } = useFilters.getState();
    expect(marketplace).toBe("");
    expect(adPlatform).toBe("");
    expect(campaignId).toBe("");
  });

  it("setDateRange updates both dates", () => {
    useFilters.getState().setDateRange("2024-03-01", "2024-03-31");
    const { dateFrom, dateTo } = useFilters.getState();
    expect(dateFrom).toBe("2024-03-01");
    expect(dateTo).toBe("2024-03-31");
  });

  it("setMarketplace updates marketplace", () => {
    useFilters.getState().setMarketplace("ozon");
    expect(useFilters.getState().marketplace).toBe("ozon");
  });

  it("setAdPlatform updates adPlatform", () => {
    useFilters.getState().setAdPlatform("vk_ads");
    expect(useFilters.getState().adPlatform).toBe("vk_ads");
  });

  it("setCampaignId updates campaignId", () => {
    useFilters.getState().setCampaignId("camp-123");
    expect(useFilters.getState().campaignId).toBe("camp-123");
  });

  it("reset clears marketplace, adPlatform, campaignId but keeps dates", () => {
    const s = useFilters.getState();
    s.setMarketplace("ozon");
    s.setAdPlatform("vk_ads");
    s.setCampaignId("camp-123");
    s.reset();
    const after = useFilters.getState();
    expect(after.marketplace).toBe("");
    expect(after.adPlatform).toBe("");
    expect(after.campaignId).toBe("");
    expect(after.dateFrom).toBe("2024-01-01");
    expect(after.dateTo).toBe("2024-01-31");
  });
});
