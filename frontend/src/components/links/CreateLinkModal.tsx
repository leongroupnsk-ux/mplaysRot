import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchStores, type Store } from "../../api/stores";
import { fetchDomains, type CustomDomain } from "../../api/links";
import {
  createLink,
  verifySkuApi,
  type VerifySkuResponse,
  type DeepLinkCreate,
} from "../../api/links";
import css from "./CreateLinkModal.module.css";

interface Props {
  onClose: () => void;
}

type Step = 1 | 2 | 3 | 4;

interface FormState {
  store_id: string;
  marketplace: string;
  external_product_id: string;
  link_type: "deeplink" | "autolanding";
  name: string;
  custom_domain_id: string;
  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  utm_term: string;
  utm_content: string;
}

const INITIAL: FormState = {
  store_id: "",
  marketplace: "",
  external_product_id: "",
  link_type: "deeplink",
  name: "",
  custom_domain_id: "",
  utm_source: "",
  utm_medium: "",
  utm_campaign: "",
  utm_term: "",
  utm_content: "",
};

const STEPS = [
  { n: 1, label: "Товар" },
  { n: 2, label: "Тип ссылки" },
  { n: 3, label: "UTM и домен" },
  { n: 4, label: "Превью" },
];

export default function CreateLinkModal({ onClose }: Props) {
  const qc = useQueryClient();
  const [step, setStep] = useState<Step>(1);
  const [form, setForm] = useState<FormState>(INITIAL);
  const [verifyResult, setVerifyResult] = useState<VerifySkuResponse | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  const { data: stores = [] } = useQuery<Store[]>({
    queryKey: ["stores"],
    queryFn: fetchStores,
  });

  const { data: domains = [] } = useQuery<CustomDomain[]>({
    queryKey: ["domains"],
    queryFn: fetchDomains,
  });

  const activeDomains = domains.filter((d) => d.status === "active");

  // Auto-fill marketplace when store changes
  useEffect(() => {
    if (!form.store_id) return;
    const store = stores.find((s) => s.id === form.store_id);
    if (store) {
      setForm((f) => ({ ...f, marketplace: store.provider }));
    }
  }, [form.store_id, stores]);

  const set = (key: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const createMut = useMutation({
    mutationFn: createLink,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["links"] });
      onClose();
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || "Ошибка при создании ссылки";
      setCreateError(typeof msg === "string" ? msg : JSON.stringify(msg));
    },
  });

  const handleVerify = async () => {
    if (!form.store_id || !form.external_product_id.trim()) return;
    setIsVerifying(true);
    setVerifyResult(null);
    setVerifyError(null);
    try {
      const res = await verifySkuApi(form.store_id, form.external_product_id.trim());
      setVerifyResult(res);
      if (!res.valid) setVerifyError(res.message || "Товар не найден");
    } catch {
      setVerifyError("Ошибка проверки артикула");
    } finally {
      setIsVerifying(false);
    }
  };

  const canProceedStep1 = !!form.store_id && !!form.external_product_id && verifyResult?.valid;
  const canProceedStep2 = !!form.link_type;
  const canProceedStep3 = true;

  const handleSubmit = () => {
    setCreateError(null);
    const payload: DeepLinkCreate = {
      store_id: form.store_id,
      marketplace: form.marketplace,
      external_product_id: form.external_product_id.trim(),
      link_type: form.link_type,
      name: form.name || undefined,
      custom_domain_id: form.custom_domain_id || undefined,
      utm_source: form.utm_source || undefined,
      utm_medium: form.utm_medium || undefined,
      utm_campaign: form.utm_campaign || undefined,
      utm_term: form.utm_term || undefined,
      utm_content: form.utm_content || undefined,
    };
    createMut.mutate(payload);
  };

  const previewUrl = form.custom_domain_id
    ? `https://${activeDomains.find((d) => d.id === form.custom_domain_id)?.domain ?? ""}/${"{код}"}`
    : `https://attribly.ru/l/{код}`;

  return (
    <div className={css.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={css.modal}>
        {/* Header */}
        <div className={css.header}>
          <span className={css.title}>Создать ссылку</span>
          <button className={css.closeBtn} onClick={onClose}>×</button>
        </div>

        {/* Steps */}
        <div className={css.steps}>
          {STEPS.map(({ n, label }) => (
            <div key={n} className={`${css.step} ${step === n ? css.stepActive : ""}`}>
              <span className={css.stepNum}>{n}</span>
              {label}
            </div>
          ))}
        </div>

        {/* Body */}
        <div className={css.body}>
          {/* ── Step 1: Product ── */}
          {step === 1 && (
            <>
              <div className={css.formGroup}>
                <label className={css.label}>Магазин</label>
                <select className={css.select} value={form.store_id} onChange={set("store_id")}>
                  <option value="">Выберите магазин…</option>
                  {stores.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.provider})
                    </option>
                  ))}
                </select>
              </div>

              <div className={css.formGroup}>
                <label className={css.label}>Артикул товара (SKU)</label>
                <div className={css.skuVerify}>
                  <input
                    className={css.input}
                    placeholder="Например: 123456789"
                    value={form.external_product_id}
                    onChange={set("external_product_id")}
                    onKeyDown={(e) => e.key === "Enter" && handleVerify()}
                  />
                  <button
                    className={css.verifyBtn}
                    onClick={handleVerify}
                    disabled={!form.store_id || !form.external_product_id || isVerifying}
                  >
                    {isVerifying ? "…" : "Проверить"}
                  </button>
                </div>
              </div>

              {verifyResult?.valid && (
                <div className={`${css.verifyResult} ${css.verifyResultOk}`}>
                  {verifyResult.product_image && (
                    <img className={css.verifyThumb} src={verifyResult.product_image} alt="" />
                  )}
                  <div className={css.verifyInfo}>
                    <div className={css.verifyTitle}>{verifyResult.product_title}</div>
                    {verifyResult.product_price && (
                      <div className={css.verifyPrice}>
                        {Number(verifyResult.product_price).toLocaleString("ru-RU")} ₽
                      </div>
                    )}
                  </div>
                  <span style={{ color: "#065f46", fontSize: 18 }}>✓</span>
                </div>
              )}

              {verifyError && (
                <div className={`${css.verifyResult} ${css.verifyResultErr}`}>
                  <span className={css.verifyMsg}>{verifyError}</span>
                </div>
              )}

              <div className={css.formGroup}>
                <label className={css.label}>Название ссылки (необязательно)</label>
                <input
                  className={css.input}
                  placeholder="Например: WB Лето 2025"
                  value={form.name}
                  onChange={set("name")}
                />
                <span className={css.hint}>Для вашего удобства, не отображается пользователям</span>
              </div>
            </>
          )}

          {/* ── Step 2: Link type ── */}
          {step === 2 && (
            <>
              <div className={css.formGroup}>
                <label className={css.label}>Тип ссылки</label>
                <select className={css.select} value={form.link_type} onChange={set("link_type")}>
                  <option value="deeplink">
                    Диплинк — открывает приложение маркетплейса
                  </option>
                  <option value="autolanding">
                    Автолендинг — промежуточная страница с кнопками
                  </option>
                </select>
              </div>

              <div
                style={{
                  background: "var(--bg-hover, rgba(0,0,0,.04))",
                  borderRadius: 10,
                  padding: "16px",
                  fontSize: 13,
                  lineHeight: 1.6,
                }}
              >
                {form.link_type === "deeplink" ? (
                  <>
                    <strong>Диплинк</strong> — при клике пытается открыть официальное приложение{" "}
                    {form.marketplace === "ozon" ? "Ozon" : "Wildberries"} на странице товара.
                    Если приложение не установлено — редирект на сайт маркетплейса.
                  </>
                ) : (
                  <>
                    <strong>Автолендинг</strong> — пользователь видит промежуточную страницу с
                    фото товара, ценой и кнопками «Открыть в приложении» / «Перейти на сайт».
                    Хорошо работает для соцсетей и мессенджеров.
                  </>
                )}
              </div>
            </>
          )}

          {/* ── Step 3: UTM + domain ── */}
          {step === 3 && (
            <>
              <div className={css.formGroup}>
                <label className={css.label}>Кастомный домен (необязательно)</label>
                <select
                  className={css.select}
                  value={form.custom_domain_id}
                  onChange={set("custom_domain_id")}
                >
                  <option value="">attribly.ru (системный)</option>
                  {activeDomains.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.domain}
                    </option>
                  ))}
                </select>
                {activeDomains.length === 0 && (
                  <span className={css.hint}>
                    У вас нет активных доменов.{" "}
                    <a href="/settings/domains" style={{ color: "var(--accent)" }}>
                      Добавить домен →
                    </a>
                  </span>
                )}
              </div>

              <div className={css.formGroup}>
                <label className={css.label}>UTM-метки</label>
                <div className={css.utmGrid}>
                  <div>
                    <span className={css.hint} style={{ display: "block", marginBottom: 4 }}>
                      utm_source
                    </span>
                    <input
                      className={css.input}
                      placeholder="telegram"
                      value={form.utm_source}
                      onChange={set("utm_source")}
                    />
                  </div>
                  <div>
                    <span className={css.hint} style={{ display: "block", marginBottom: 4 }}>
                      utm_medium
                    </span>
                    <input
                      className={css.input}
                      placeholder="post"
                      value={form.utm_medium}
                      onChange={set("utm_medium")}
                    />
                  </div>
                  <div>
                    <span className={css.hint} style={{ display: "block", marginBottom: 4 }}>
                      utm_campaign
                    </span>
                    <input
                      className={css.input}
                      placeholder="summer_sale"
                      value={form.utm_campaign}
                      onChange={set("utm_campaign")}
                    />
                  </div>
                  <div>
                    <span className={css.hint} style={{ display: "block", marginBottom: 4 }}>
                      utm_term
                    </span>
                    <input
                      className={css.input}
                      placeholder=""
                      value={form.utm_term}
                      onChange={set("utm_term")}
                    />
                  </div>
                  <div style={{ gridColumn: "1 / -1" }}>
                    <span className={css.hint} style={{ display: "block", marginBottom: 4 }}>
                      utm_content
                    </span>
                    <input
                      className={css.input}
                      placeholder=""
                      value={form.utm_content}
                      onChange={set("utm_content")}
                    />
                  </div>
                </div>
              </div>
            </>
          )}

          {/* ── Step 4: Preview ── */}
          {step === 4 && (
            <>
              <div className={css.previewCard}>
                {verifyResult?.product_image && (
                  <img
                    className={css.previewImg}
                    src={verifyResult.product_image}
                    alt={verifyResult.product_title || ""}
                  />
                )}
                <div className={css.previewBody}>
                  <div className={css.previewTitle}>
                    {form.name || verifyResult?.product_title || form.external_product_id}
                  </div>
                  {verifyResult?.product_price && (
                    <div className={css.previewPrice}>
                      {Number(verifyResult.product_price).toLocaleString("ru-RU")} ₽
                    </div>
                  )}
                  <div className={css.previewUrl}>{previewUrl}</div>
                  <div className={css.previewBtns}>
                    <div className={css.previewBtnApp}>Открыть в приложении</div>
                    <div className={css.previewBtnWeb}>На сайте</div>
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.7 }}>
                <div>
                  <strong>Маркетплейс:</strong>{" "}
                  {form.marketplace === "wildberries" ? "Wildberries" : "Ozon"}
                </div>
                <div>
                  <strong>Тип:</strong>{" "}
                  {form.link_type === "deeplink" ? "Диплинк" : "Автолендинг"}
                </div>
                <div>
                  <strong>Артикул:</strong> {form.external_product_id}
                </div>
                {form.utm_source && (
                  <div>
                    <strong>UTM:</strong> {form.utm_source}/{form.utm_medium}/{form.utm_campaign}
                  </div>
                )}
              </div>

              {createError && <div className={css.error}>{createError}</div>}
            </>
          )}
        </div>

        {/* Footer */}
        <div className={css.footer}>
          <button
            className={css.btnBack}
            onClick={() => (step > 1 ? setStep((s) => (s - 1) as Step) : onClose())}
          >
            {step === 1 ? "Отмена" : "← Назад"}
          </button>

          {step < 4 ? (
            <button
              className={css.btnNext}
              disabled={
                (step === 1 && !canProceedStep1) ||
                (step === 2 && !canProceedStep2) ||
                (step === 3 && !canProceedStep3)
              }
              onClick={() => setStep((s) => (s + 1) as Step)}
            >
              Далее →
            </button>
          ) : (
            <button
              className={css.btnNext}
              disabled={createMut.isPending}
              onClick={handleSubmit}
            >
              {createMut.isPending ? "Создаём…" : "Создать ссылку"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
