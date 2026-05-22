import api from "./client";

export interface WBStockItem {
  lastChangeDate: string;
  warehouseName: string;
  supplierArticle: string;
  nmId: number;
  barcode: string;
  subject: string;
  category: string;
  brand: string;
  techSize: string;
  Price: number;
  Discount: number;
  isSupply: boolean;
  isRealization: boolean;
  quantityFull: number;
  quantityNotInOrders: number;
  inWayToClient: number;
  inWayFromClient: number;
  quantity: number;
}

export interface WBWarehouse {
  id: number;
  name: string;
  officeId?: number;
}

export const fetchWBStocks = () =>
  api.get<WBStockItem[]>("/logistics/stocks").then((r) => r.data);

export const fetchWBWarehouses = () =>
  api.get<WBWarehouse[]>("/logistics/warehouses").then((r) => r.data);
