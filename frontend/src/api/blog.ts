import api from "./client";
import adminApi from "./admin";

// ── Public types ──────────────────────────────────────────────────────────────

export interface BlogArticleCard {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  cover_image: string | null;
  category: string;
  tags: string[];
  author: string;
  published_at: string | null;
  view_count: number;
  like_count: number;
}

export interface BlogArticleDetail extends BlogArticleCard {
  content: string | null;
  meta_title: string | null;
  meta_description: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface BlogListResponse {
  items: BlogArticleCard[];
  total: number;
  page: number;
  pages: number;
}

// ── Public API ────────────────────────────────────────────────────────────────

export const fetchBlogArticles = (params: { page?: number; category?: string; search?: string }) =>
  api.get<BlogListResponse>("/blog/articles", { params }).then((r) => r.data);

export const fetchBlogArticle = (slug: string) =>
  api.get<BlogArticleDetail>(`/blog/articles/${slug}`).then((r) => r.data);

export const registerView = (id: number) =>
  api.post<{ view_count: number }>(`/blog/articles/${id}/view`).then((r) => r.data);

export const toggleLike = (id: number) =>
  api.post<{ like_count: number; liked: boolean }>(`/blog/articles/${id}/like`).then((r) => r.data);

// ── Admin types ───────────────────────────────────────────────────────────────

export interface ArticleCreatePayload {
  title: string;
  slug: string;
  excerpt?: string;
  content?: string;
  cover_image?: string;
  category: string;
  tags: string[];
  author: string;
  published_at?: string | null;
  status: string;
  meta_title?: string;
  meta_description?: string;
}

export type ArticleUpdatePayload = Partial<ArticleCreatePayload>;

// ── Admin API ─────────────────────────────────────────────────────────────────

export const adminFetchArticles = (params?: { status?: string; category?: string }) =>
  adminApi.get<BlogArticleDetail[]>("/blog/articles", { params }).then((r) => r.data);

export const adminFetchArticle = (id: number) =>
  adminApi.get<BlogArticleDetail>(`/blog/articles/${id}`).then((r) => r.data);

export const adminCreateArticle = (payload: ArticleCreatePayload) =>
  adminApi.post<BlogArticleDetail>("/blog/articles", payload).then((r) => r.data);

export const adminUpdateArticle = (id: number, payload: ArticleUpdatePayload) =>
  adminApi.put<BlogArticleDetail>(`/blog/articles/${id}`, payload).then((r) => r.data);

export const adminDeleteArticle = (id: number) =>
  adminApi.delete(`/blog/articles/${id}`);

export const adminUploadMedia = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return adminApi
    .post<{ url: string }>("/blog/media/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data.url);
};
