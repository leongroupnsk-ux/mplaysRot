import api from "./client";

export interface ProductVariation {
  external_product_id: string;
  title: string;
  stock: number;
}

export interface Product {
  id: string;
  store_id: string;
  provider: string;
  external_product_id: string;
  parent_external_id: string | null;
  title: string;
  price: number;
  stock: number;
  image_url: string | null;
  has_variations: boolean;
  is_active: boolean;
  is_archived: boolean;
  variations: ProductVariation[];
}

export interface ProductSearchResponse {
  items: Product[];
  total: number;
}

export const searchProducts = (params: {
  q?: string;
  marketplace?: string;
  store_id?: string;
  include_out_of_stock?: boolean;
  expand_variations?: boolean;
  limit?: number;
  offset?: number;
}) =>
  api
    .get<ProductSearchResponse>("/products/search", { params })
    .then((r) => r.data);
