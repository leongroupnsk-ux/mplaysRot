import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { connectMarketplace, connectAdPlatform } from "../../api/integrations";
import styles from "./ConnectModal.module.css";

const MARKETPLACE_FIELDS: Record<string, { label: string; hint?: string; required?: boolean }[]> = {
  ozon: [
    { label: "Client-Id", hint: "Числовой ID из настроек Ozon Seller", required: true },
    { label: "API-ключ", hint: "Ключ с правами на чтение заказов и товаров", required: true },
    { label: "Seller ID", hint: "Необязательно" },
  ],
  wildberries: [
    { label: "API-ключ", hint: "Токен из WB Seller → Настройки → Доступ к API. Нужны права: Статистика, Контент, Маркетплейс", required: true },
  ],
  yandex_market: [
    { label: "OAuth-токен", hint: "Токен с правами market:partner-api", required: true },
    { label: "Client-Id", hint: "ID приложения Яндекс", required: true },
    { label: "Campaign ID", hint: "ID кампании (магазина) в ЯМ", required: true },
  ],
  amazon: [
    { label: "Refresh Token", hint: "LWA refresh token из SP-API", required: true },
    { label: "Client ID", hint: "LWA App Client ID", required: true },
    { label: "Client Secret", hint: "LWA App Client Secret", required: true },
  ],
};

const AD_FIELDS: Record<string, { label: string; hint?: string; required?: boolean }[]> = {
  yandex_direct: [
    { label: "OAuth-токен", hint: "Токен Яндекс.Директа", required: true },
    { label: "Логин клиента", hint: "Client Login в API" },
  ],
  vk_ads: [
    { label: "Access Token", required: true },
    { label: "Account ID", hint: "ID рекламного кабинета", required: true },
  ],
  vk_blogger: [
    { label: "Access Token", hint: "VK OAuth-токен", required: true },
  ],
  telegram_ads: [
    { label: "Access Token", hint: "Токен из Telegram Ads", required: true },
  ],
  messenger_max: [
    { label: "Access Token", required: true },
    { label: "Webhook Secret", hint: "Для верификации вебхуков" },
  ],
};

const NAMES: Record<string, string> = {
  ozon: "Ozon", wildberries: "Wildberries", yandex_market: "Яндекс.Маркет", amazon: "Amazon",
  yandex_direct: "Яндекс.Директ", vk_ads: "VK Ads", vk_blogger: "VK Блогер",
  telegram_ads: "Telegram Ads", messenger_max: "Messenger MAX",
};

interface Props {
  provider: string;
  type: "marketplace" | "ad_platform";
  onClose: () => void;
}

export default function ConnectModal({ provider, type, onClose }: Props) {
  const qc = useQueryClient();
  const fields = type === "marketplace"
    ? (MARKETPLACE_FIELDS[provider] ?? [])
    : (AD_FIELDS[provider] ?? []);

  const [values, setValues] = useState<string[]>(fields.map(() => ""));
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      setError(null);
      if (type === "marketplace") {
        const [clientIdOrKey, apiKey, sellerId] = values;
        const payload: Record<string, string> = { provider };
        if (provider === "ozon") {
          payload.client_id = clientIdOrKey;
          payload.api_key = apiKey;
          if (sellerId) payload.seller_id = sellerId;
        } else if (provider === "wildberries") {
          payload.api_key = clientIdOrKey;
        } else if (provider === "yandex_market") {
          payload.api_key = clientIdOrKey;   // oauth_token stored as api_key
          payload.client_id = apiKey;
          payload.seller_id = sellerId;
        } else {
          payload.api_key = clientIdOrKey;
          if (apiKey) payload.client_id = apiKey;
          if (sellerId) payload.seller_id = sellerId;
        }
        return connectMarketplace(payload as any);
      } else {
        const [accessToken, secondField] = values;
        return connectAdPlatform({
          provider,
          access_token: accessToken,
          account_id: secondField || undefined,
          account_name: undefined,
        });
      }
    },
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["integrations"] });
      qc.invalidateQueries({ queryKey: ["stores"] });
      if (result.status === "error") {
        setError(
          "API-ключ не прошёл проверку. Убедитесь, что ключ правильный и имеет нужные права доступа."
        );
      } else {
        onClose();
      }
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail ?? "Ошибка при подключении. Попробуйте позже.");
    },
  });

  const canSubmit = fields
    .filter((f) => f.required)
    .every((_, i) => values[i]?.trim());

  return (
    <div className={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <span className={styles.title}>Подключить {NAMES[provider]}</span>
          <button className={styles.close} onClick={onClose}>×</button>
        </div>

        <div className={styles.form}>
          {fields.map((f, i) => (
            <div key={i} className={styles.field}>
              <label className={styles.label}>
                {f.label}{f.required && " *"}
              </label>
              <input
                className={styles.input}
                type={f.label.toLowerCase().includes("secret") || f.label.toLowerCase().includes("token") || f.label.toLowerCase().includes("ключ") ? "password" : "text"}
                placeholder={f.hint ?? f.label}
                value={values[i]}
                onChange={(e) => setValues((v) => v.map((x, j) => j === i ? e.target.value : x))}
              />
              {f.hint && <span className={styles.hint}>{f.hint}</span>}
            </div>
          ))}

          {error && (
            <div className={styles.error}>
              {error}
              {provider === "wildberries" && (
                <div style={{ marginTop: 6, fontSize: 12, opacity: 0.8 }}>
                  Создайте токен в{" "}
                  <a
                    href="https://seller.wildberries.ru/supplier-settings/access-to-api"
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: "inherit", textDecoration: "underline" }}
                  >
                    WB Seller → Настройки → Доступ к API
                  </a>
                  {" "}со всеми нужными правами.
                </div>
              )}
            </div>
          )}

          <div className={styles.footer}>
            <button className={styles.btnCancel} onClick={onClose}>Отмена</button>
            <button
              className={styles.btnSubmit}
              disabled={!canSubmit || mutation.isPending}
              onClick={() => mutation.mutate()}
            >
              {mutation.isPending ? "Подключение…" : "Подключить"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
