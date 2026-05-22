import api from "./client";

// ── Types ─────────────────────────────────────────────────────────────────────

export type WidgetType =
  | "product_card"
  | "logistics"
  | "ad_connector"
  | "mini_chart"
  | "sticker"
  | "text"
  | "kpi_table";

export interface CanvasWidget {
  id: string;
  board_id: string;
  widget_type: WidgetType;
  x: number;
  y: number;
  width: number;
  height: number;
  z_index: number;
  data: Record<string, any>;
  style: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CanvasConnection {
  id: string;
  board_id: string;
  from_widget_id: string;
  to_widget_id: string;
  style: Record<string, any>;
  label?: string | null;
  created_at: string;
}

export interface CanvasBoard {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  template_id?: string | null;
  is_public: boolean;
  share_token?: string | null;
  viewport_x: number;
  viewport_y: number;
  viewport_zoom: number;
  created_at: string;
  updated_at: string;
}

export interface CanvasBoardDetail extends CanvasBoard {
  widgets: CanvasWidget[];
  connections: CanvasConnection[];
}

export interface BoardTemplate {
  id: string;
  name: string;
  description?: string | null;
  category: string;
  thumbnail_emoji: string;
  template_data: Record<string, any>;
  is_system: boolean;
}

// Widget data types
export interface ProductWidgetData {
  external_product_id: string;
  title: string;
  image_url?: string | null;
  price?: string | null;
  stock: number;
  store_name?: string | null;
  marketplace?: string | null;
}

export interface LogisticsWidgetData {
  external_product_id: string;
  title: string;
  image_url?: string | null;
  stock: number;
  days_supply?: number | null;
  status: "ok" | "warn" | "critical";
}

export interface CampaignWidgetData {
  campaign_id: string;
  name: string;
  marketplace: string;
  ad_platform: string;
  is_active: boolean;
  budget?: string | null;
  utm_source?: string | null;
}

// ── Boards ────────────────────────────────────────────────────────────────────

export const listBoards = () =>
  api.get<CanvasBoard[]>("/canvas/boards").then((r) => r.data);

export const createBoard = (payload: { title?: string; description?: string; template_id?: string }) =>
  api.post<CanvasBoardDetail>("/canvas/boards", payload).then((r) => r.data);

export const getBoard = (id: string) =>
  api.get<CanvasBoardDetail>(`/canvas/boards/${id}`).then((r) => r.data);

export const updateBoard = (
  id: string,
  payload: Partial<{
    title: string;
    description: string;
    viewport_x: number;
    viewport_y: number;
    viewport_zoom: number;
    is_public: boolean;
  }>
) => api.patch<CanvasBoard>(`/canvas/boards/${id}`, payload).then((r) => r.data);

export const deleteBoard = (id: string) => api.delete(`/canvas/boards/${id}`);

export const toggleShareBoard = (id: string) =>
  api.post<CanvasBoard>(`/canvas/boards/${id}/share`).then((r) => r.data);

// ── Widgets ───────────────────────────────────────────────────────────────────

export interface WidgetCreatePayload {
  widget_type: WidgetType;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  z_index?: number;
  data?: Record<string, any>;
  style?: Record<string, any>;
}

export const addWidget = (boardId: string, payload: WidgetCreatePayload) =>
  api.post<CanvasWidget>(`/canvas/boards/${boardId}/widgets`, payload).then((r) => r.data);

export const updateWidget = (
  boardId: string,
  widgetId: string,
  payload: Partial<{ x: number; y: number; width: number; height: number; z_index: number; data: Record<string, any>; style: Record<string, any> }>
) => api.patch<CanvasWidget>(`/canvas/boards/${boardId}/widgets/${widgetId}`, payload).then((r) => r.data);

export const bulkUpdateWidgets = (
  boardId: string,
  updates: Array<{ id: string; x?: number; y?: number; z_index?: number }>
) => api.post(`/canvas/boards/${boardId}/widgets/bulk`, { updates });

export const deleteWidget = (boardId: string, widgetId: string) =>
  api.delete(`/canvas/boards/${boardId}/widgets/${widgetId}`);

// ── Connections ───────────────────────────────────────────────────────────────

export const addConnection = (
  boardId: string,
  payload: { from_widget_id: string; to_widget_id: string; style?: Record<string, any>; label?: string }
) => api.post<CanvasConnection>(`/canvas/boards/${boardId}/connections`, payload).then((r) => r.data);

export const deleteConnection = (boardId: string, connId: string) =>
  api.delete(`/canvas/boards/${boardId}/connections/${connId}`);

// ── Templates ─────────────────────────────────────────────────────────────────

export const listTemplates = () =>
  api.get<BoardTemplate[]>("/canvas/templates").then((r) => r.data);

// ── Widget data ───────────────────────────────────────────────────────────────

export const getProductWidgetData = (store_id: string, external_product_id: string) =>
  api
    .get<ProductWidgetData>("/canvas/widget-data/product", { params: { store_id, external_product_id } })
    .then((r) => r.data);

export const getLogisticsWidgetData = (store_id: string, external_product_id: string) =>
  api
    .get<LogisticsWidgetData>("/canvas/widget-data/logistics", { params: { store_id, external_product_id } })
    .then((r) => r.data);

export const getCampaignWidgetData = (campaign_id: string) =>
  api
    .get<CampaignWidgetData>("/canvas/widget-data/campaign", { params: { campaign_id } })
    .then((r) => r.data);

// ── AI ────────────────────────────────────────────────────────────────────────

export const sendAICommand = (boardId: string, command: string) =>
  api
    .post<{ message: string; actions: any[] }>(`/canvas/boards/${boardId}/ai-command`, { command })
    .then((r) => r.data);
