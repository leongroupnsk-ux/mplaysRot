import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  adminFetchArticle, adminCreateArticle, adminUpdateArticle, adminUploadMedia,
  type ArticleCreatePayload,
} from "../../api/blog";

const CATEGORIES = [
  { value: "traffic",      label: "Внешний трафик" },
  { value: "logistics",    label: "Логистика" },
  { value: "analytics",    label: "Аналитика" },
  { value: "ai",           label: "AI" },
  { value: "integrations", label: "Интеграции" },
  { value: "news",         label: "Новости" },
  { value: "general",      label: "Общее" },
];

function slugify(s: string) {
  return s
    .toLowerCase()
    .replace(/[а-яё]/g, (c) => (translitMap[c] ?? c))
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
const translitMap: Record<string, string> = {
  а:"a",б:"b",в:"v",г:"g",д:"d",е:"e",ё:"yo",ж:"zh",з:"z",и:"i",й:"j",
  к:"k",л:"l",м:"m",н:"n",о:"o",п:"p",р:"r",с:"s",т:"t",у:"u",ф:"f",
  х:"kh",ц:"ts",ч:"ch",ш:"sh",щ:"shch",ъ:"",ы:"y",ь:"",э:"e",ю:"yu",я:"ya",
};

export default function AdminBlogArticlePage() {
  const { id } = useParams<{ id: string }>();
  const isNew = id === "new";
  const articleId = isNew ? null : Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [form, setForm] = useState<ArticleCreatePayload>({
    title: "", slug: "", excerpt: "", content: "", cover_image: "",
    category: "general", tags: [], author: "Команда MPlays",
    published_at: null, status: "draft", meta_title: "", meta_description: "",
  });
  const [tagsInput, setTagsInput] = useState("");
  const [preview, setPreview] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: existing } = useQuery({
    queryKey: ["admin-blog-article", articleId],
    queryFn: () => adminFetchArticle(articleId!),
    enabled: !isNew && articleId !== null,
    staleTime: 0,
  });

  useEffect(() => {
    if (existing) {
      setForm({
        title: existing.title,
        slug: existing.slug,
        excerpt: existing.excerpt ?? "",
        content: existing.content ?? "",
        cover_image: existing.cover_image ?? "",
        category: existing.category,
        tags: existing.tags,
        author: existing.author,
        published_at: existing.published_at ?? null,
        status: existing.status,
        meta_title: existing.meta_title ?? "",
        meta_description: existing.meta_description ?? "",
      });
      setTagsInput(existing.tags.join(", "));
    }
  }, [existing]);

  const createMut = useMutation({
    mutationFn: adminCreateArticle,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["admin-blog-articles"] });
      navigate(`/admin/blog/${data.id}`, { replace: true });
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? String(e);
      setSaveError(msg);
    },
  });

  const updateMut = useMutation({
    mutationFn: ({ payload }: { payload: Partial<ArticleCreatePayload> }) =>
      adminUpdateArticle(articleId!, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-blog-articles"] });
      qc.invalidateQueries({ queryKey: ["admin-blog-article", articleId] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? String(e);
      setSaveError(msg);
    },
  });

  function set(key: keyof ArticleCreatePayload, val: unknown) {
    setForm((prev) => ({ ...prev, [key]: val }));
    if (saveError) setSaveError(null);
  }

  function handleTitleChange(v: string) {
    set("title", v);
    if (isNew || !form.slug) set("slug", slugify(v));
  }

  function handleTagsBlur() {
    const tags = tagsInput.split(",").map((t) => t.trim()).filter(Boolean);
    set("tags", tags);
  }

  async function handleUpload(file: File) {
    setUploadLoading(true);
    try {
      const url = await adminUploadMedia(file);
      set("cover_image", url);
    } catch {
      setSaveError("Ошибка загрузки изображения");
    } finally {
      setUploadLoading(false);
    }
  }

  function validate() {
    if (!form.title.trim()) return "Заголовок обязателен";
    if (!form.slug.trim()) return "Slug обязателен";
    if ((form.content ?? "").length > 100_000) return "Контент слишком длинный";
    return null;
  }

  function handleSave(status?: string) {
    const err = validate();
    if (err) { setSaveError(err); return; }
    const payload = status ? { ...form, status } : form;
    setSaveError(null);
    if (isNew) createMut.mutate(payload);
    else updateMut.mutate({ payload });
  }

  const isBusy = createMut.isPending || updateMut.isPending;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 1100 }}>
      {/* Toolbar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button onClick={() => navigate("/admin/blog")} style={btnBack}>← Назад</button>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>
            {isNew ? "Новая статья" : "Редактирование статьи"}
          </h1>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {saved && <span style={{ fontSize: 13, color: "#4ade80" }}>✓ Сохранено</span>}
          {saveError && <span style={{ fontSize: 13, color: "#f87171" }}>{saveError}</span>}
          <button style={btnPreview} onClick={() => setPreview(!preview)}>
            {preview ? "← Редактор" : "Превью →"}
          </button>
          <button style={btnDraft} onClick={() => handleSave("draft")} disabled={isBusy}>
            {isBusy ? "…" : "Черновик"}
          </button>
          <button style={btnPublish} onClick={() => handleSave("published")} disabled={isBusy}>
            {isBusy ? "…" : "Опубликовать"}
          </button>
        </div>
      </div>

      {preview ? (
        /* ── Preview ── */
        <div style={previewWrap}>
          <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 16 }}>{form.title || "(без заголовка)"}</h1>
          {form.cover_image && (
            <img src={form.cover_image} alt="" style={{ width: "100%", borderRadius: 10, marginBottom: 20, maxHeight: 400, objectFit: "cover" }} />
          )}
          <div
            style={contentPreviewStyle}
            dangerouslySetInnerHTML={{ __html: form.content ?? "" }}
          />
        </div>
      ) : (
        /* ── Editor ── */
        <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 20, alignItems: "start" }}>
          {/* Main fields */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* Title */}
            <Field label="Заголовок *">
              <input
                style={inputStyle}
                value={form.title}
                onChange={(e) => handleTitleChange(e.target.value)}
                placeholder="Введите заголовок статьи"
              />
            </Field>

            {/* Slug */}
            <Field label="Slug (URL)">
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  style={{ ...inputStyle, flex: 1, fontFamily: "monospace", fontSize: 12 }}
                  value={form.slug}
                  onChange={(e) => set("slug", e.target.value)}
                  placeholder="url-slug-stati"
                />
                <button style={btnGenSlug} onClick={() => set("slug", slugify(form.title))}>
                  Авто
                </button>
              </div>
              <div style={{ fontSize: 11, color: "#8890a4", marginTop: 4 }}>
                /blog/{form.slug || "…"}
              </div>
            </Field>

            {/* Excerpt */}
            <Field label="Краткое описание (до 160 символов)">
              <textarea
                style={{ ...inputStyle, height: 70, resize: "vertical" }}
                value={form.excerpt ?? ""}
                onChange={(e) => set("excerpt", e.target.value)}
                maxLength={200}
                placeholder="Краткий анонс для карточки на главной блога"
              />
            </Field>

            {/* Content */}
            <Field label="Контент (HTML)">
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <textarea
                  style={{ ...inputStyle, height: 480, resize: "vertical", fontFamily: "monospace", fontSize: 12, lineHeight: 1.5 }}
                  value={form.content ?? ""}
                  onChange={(e) => set("content", e.target.value)}
                  placeholder="<h2>Заголовок раздела</h2><p>Текст статьи…</p>"
                />
                <div
                  style={{ ...previewWrap, height: 480, overflowY: "auto", padding: "12px 16px" }}
                  dangerouslySetInnerHTML={{ __html: form.content ?? "<i style='color:#8890a4'>HTML-превью</i>" }}
                />
              </div>
              <div style={{ fontSize: 11, color: "#8890a4", marginTop: 4 }}>
                {(form.content ?? "").length.toLocaleString("ru-RU")} символов
              </div>
            </Field>
          </div>

          {/* Sidebar fields */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* Status */}
            <SideSection title="Публикация">
              <label style={labelStyle}>Статус</label>
              <select style={inputStyle} value={form.status} onChange={(e) => set("status", e.target.value)}>
                <option value="draft">Черновик</option>
                <option value="published">Опубликована</option>
                <option value="archived">Архив</option>
              </select>
              <label style={{ ...labelStyle, marginTop: 10 }}>Дата публикации</label>
              <input
                type="datetime-local"
                style={inputStyle}
                value={form.published_at ? form.published_at.slice(0, 16) : ""}
                onChange={(e) => set("published_at", e.target.value ? e.target.value + ":00Z" : null)}
              />
            </SideSection>

            {/* Category */}
            <SideSection title="Категория и теги">
              <label style={labelStyle}>Категория</label>
              <select style={inputStyle} value={form.category} onChange={(e) => set("category", e.target.value)}>
                {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
              <label style={{ ...labelStyle, marginTop: 10 }}>Теги (через запятую)</label>
              <input
                style={inputStyle}
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                onBlur={handleTagsBlur}
                placeholder="тег1, тег2, тег3"
              />
              <label style={{ ...labelStyle, marginTop: 10 }}>Автор</label>
              <input
                style={inputStyle}
                value={form.author}
                onChange={(e) => set("author", e.target.value)}
              />
            </SideSection>

            {/* Cover image */}
            <SideSection title="Обложка">
              {form.cover_image && (
                <img
                  src={form.cover_image}
                  alt="cover"
                  style={{ width: "100%", borderRadius: 8, marginBottom: 8, objectFit: "cover", height: 120 }}
                />
              )}
              <input
                style={{ ...inputStyle, fontSize: 11, fontFamily: "monospace" }}
                value={form.cover_image ?? ""}
                onChange={(e) => set("cover_image", e.target.value)}
                placeholder="https://… или загрузите файл"
              />
              <input
                ref={fileRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                style={{ display: "none" }}
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f); }}
              />
              <button
                style={{ ...btnDraft, marginTop: 8, width: "100%", justifyContent: "center" }}
                onClick={() => fileRef.current?.click()}
                disabled={uploadLoading}
              >
                {uploadLoading ? "Загрузка…" : "Загрузить файл"}
              </button>
            </SideSection>

            {/* SEO */}
            <SideSection title="SEO">
              <label style={labelStyle}>Meta Title (до 70 символов)</label>
              <input
                style={inputStyle}
                value={form.meta_title ?? ""}
                onChange={(e) => set("meta_title", e.target.value)}
                maxLength={70}
                placeholder="SEO-заголовок"
              />
              <div style={{ fontSize: 11, color: "#8890a4", marginTop: 2 }}>
                {(form.meta_title ?? "").length}/70
              </div>
              <label style={{ ...labelStyle, marginTop: 10 }}>Meta Description (до 160 символов)</label>
              <textarea
                style={{ ...inputStyle, height: 70, resize: "vertical" }}
                value={form.meta_description ?? ""}
                onChange={(e) => set("meta_description", e.target.value)}
                maxLength={160}
                placeholder="SEO-описание"
              />
              <div style={{ fontSize: 11, color: "#8890a4", marginTop: 2 }}>
                {(form.meta_description ?? "").length}/160
              </div>
            </SideSection>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Helper components ─────────────────────────────────────────────────────────

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <label style={labelStyle}>{label}</label>
      {children}
    </div>
  );
}

function SideSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={sideCard}>
      <div style={sideSectionTitle}>{title}</div>
      {children}
    </div>
  );
}

// ── Inline styles ─────────────────────────────────────────────────────────────

const inputStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8, padding: "8px 12px",
  fontSize: 13, color: "#e8eaf0", outline: "none", width: "100%", boxSizing: "border-box",
};

const labelStyle: React.CSSProperties = {
  fontSize: 11, fontWeight: 700, textTransform: "uppercase",
  letterSpacing: "0.06em", color: "#8890a4", display: "block",
};

const sideCard: React.CSSProperties = {
  background: "#141626", border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 10, padding: 16, display: "flex", flexDirection: "column", gap: 8,
};

const sideSectionTitle: React.CSSProperties = {
  fontSize: 12, fontWeight: 700, textTransform: "uppercase",
  letterSpacing: "0.07em", color: "#8890a4", marginBottom: 4,
};

const previewWrap: React.CSSProperties = {
  background: "#141626", border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 10, padding: 24, color: "#d0d4e0", lineHeight: 1.7,
};

const contentPreviewStyle: React.CSSProperties = {
  fontSize: 16, lineHeight: 1.8, color: "#d0d4e0",
};

const btnBack: React.CSSProperties = {
  padding: "6px 12px", background: "transparent",
  border: "1px solid rgba(255,255,255,0.12)", borderRadius: 7,
  color: "#8890a4", fontSize: 13, cursor: "pointer",
};

const btnPreview: React.CSSProperties = {
  padding: "7px 14px", background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.12)", borderRadius: 7,
  color: "#e8eaf0", fontSize: 13, cursor: "pointer",
};

const btnDraft: React.CSSProperties = {
  padding: "7px 16px", background: "rgba(251,191,36,0.12)",
  border: "1px solid rgba(251,191,36,0.3)", borderRadius: 7,
  color: "#fbbf24", fontSize: 13, fontWeight: 600, cursor: "pointer",
};

const btnPublish: React.CSSProperties = {
  padding: "7px 18px", background: "#7c3aed",
  border: "none", borderRadius: 7,
  color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer",
};

const btnGenSlug: React.CSSProperties = {
  padding: "8px 12px", background: "rgba(167,139,250,0.12)",
  border: "1px solid rgba(167,139,250,0.2)", borderRadius: 7,
  color: "#a78bfa", fontSize: 12, cursor: "pointer", whiteSpace: "nowrap",
};
