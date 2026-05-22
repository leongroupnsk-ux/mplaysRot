import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createCampaign } from "../../api/campaigns";
import ProductAutocomplete from "./ProductAutocomplete";
import type { Product } from "../../api/products";
import type { Marketplace, AdPlatform } from "../../api/types";
import styles from "./CreateCampaignModal.module.css";

const MARKETPLACES: { value: Marketplace; label: string }[] = [
  { value: "ozon", label: "Ozon" },
  { value: "wildberries", label: "Wildberries" },
  { value: "yandex_market", label: "Яндекс.Маркет" },
  { value: "amazon", label: "Amazon" },
];

const AD_PLATFORMS: { value: AdPlatform; label: string }[] = [
  { value: "yandex_direct", label: "Яндекс.Директ" },
  { value: "vk_ads", label: "VK Ads" },
  { value: "vk_blogger", label: "VK Блогер" },
  { value: "telegram_ads", label: "Telegram Ads" },
  { value: "messenger_max", label: "Messenger MAX" },
];

interface Props {
  onClose: () => void;
}

export default function CreateCampaignModal({ onClose }: Props) {
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [name, setName] = useState("");
  const [marketplace, setMarketplace] = useState<Marketplace>("ozon");
  const [adPlatform, setAdPlatform] = useState<AdPlatform>("vk_ads");
  const [budget, setBudget] = useState("");
  const [destinationUrl, setDestinationUrl] = useState("");
  const [products, setProducts] = useState<Product[]>([]);

  const { mutate, isPending, error } = useMutation({
    mutationFn: () =>
      createCampaign({
        name,
        marketplace,
        ad_platform: adPlatform,
        budget: budget ? Number(budget) : null,
        destination_url: destinationUrl,
      } as Parameters<typeof createCampaign>[0]),
    onSuccess: (campaign) => {
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      navigate(`/campaigns/${campaign.id}`);
    },
  });

  const canSubmit = name.trim().length > 0 && destinationUrl.trim().length > 0;

  return (
    <div className={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <span className={styles.title}>Новая кампания</span>
          <button className={styles.close} onClick={onClose} type="button">×</button>
        </div>

        <div className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label}>Название</label>
            <input
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="VK Ads → Ozon | Лето 2026"
              autoFocus
            />
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label}>Маркетплейс</label>
              <select
                className={styles.input}
                value={marketplace}
                onChange={(e) => setMarketplace(e.target.value as Marketplace)}
              >
                {MARKETPLACES.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Рекламная площадка</label>
              <select
                className={styles.input}
                value={adPlatform}
                onChange={(e) => setAdPlatform(e.target.value as AdPlatform)}
              >
                {AD_PLATFORMS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Ссылка назначения</label>
            <input
              className={styles.input}
              value={destinationUrl}
              onChange={(e) => setDestinationUrl(e.target.value)}
              placeholder="https://ozon.ru/product/..."
              type="url"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Бюджет, ₽ <span className={styles.optional}>(необязательно)</span></label>
            <input
              className={styles.input}
              value={budget}
              onChange={(e) => setBudget(e.target.value.replace(/\D/g, ""))}
              placeholder="150 000"
              inputMode="numeric"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>
              Товары <span className={styles.optional}>(необязательно)</span>
            </label>
            <ProductAutocomplete
              marketplace={marketplace}
              value={products}
              onChange={setProducts}
            />
          </div>

          {error && (
            <div className={styles.error}>Не удалось создать кампанию. Попробуйте ещё раз.</div>
          )}

          <div className={styles.footer}>
            <button className={styles.btnCancel} onClick={onClose} type="button">
              Отмена
            </button>
            <button
              className={styles.btnSubmit}
              onClick={() => mutate()}
              disabled={!canSubmit || isPending}
              type="button"
            >
              {isPending ? "Создаю…" : "Создать"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
