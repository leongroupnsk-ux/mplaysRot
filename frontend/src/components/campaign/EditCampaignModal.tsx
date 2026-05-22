import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { patchCampaign } from "../../api/campaigns";
import type { Campaign, Marketplace, AdPlatform } from "../../api/types";
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
  campaign: Campaign;
  onClose: () => void;
}

export default function EditCampaignModal({ campaign, onClose }: Props) {
  const qc = useQueryClient();

  const [name, setName] = useState(campaign.name);
  const [marketplace, setMarketplace] = useState<Marketplace>(campaign.marketplace);
  const [adPlatform, setAdPlatform] = useState<AdPlatform>(campaign.ad_platform);
  const [budget, setBudget] = useState(campaign.budget != null ? String(campaign.budget) : "");
  const [destinationUrl, setDestinationUrl] = useState(campaign.destination_url);

  const { mutate, isPending, error } = useMutation({
    mutationFn: () =>
      patchCampaign(campaign.id, {
        name,
        marketplace,
        ad_platform: adPlatform,
        budget: budget ? Number(budget) : null,
        destination_url: destinationUrl,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      qc.invalidateQueries({ queryKey: ["campaign", campaign.id] });
      onClose();
    },
  });

  const isDirty =
    name !== campaign.name ||
    marketplace !== campaign.marketplace ||
    adPlatform !== campaign.ad_platform ||
    destinationUrl !== campaign.destination_url ||
    (budget || "") !== (campaign.budget != null ? String(campaign.budget) : "");

  return (
    <div className={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal}>
        <div className={styles.header}>
          <span className={styles.title}>Редактировать кампанию</span>
          <button className={styles.close} onClick={onClose} type="button">×</button>
        </div>

        <div className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label}>Название</label>
            <input
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
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
              type="url"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label}>
              Бюджет, ₽ <span className={styles.optional}>(необязательно)</span>
            </label>
            <input
              className={styles.input}
              value={budget}
              onChange={(e) => setBudget(e.target.value.replace(/\D/g, ""))}
              inputMode="numeric"
              placeholder="—"
            />
          </div>

          {error && (
            <div className={styles.error}>Не удалось сохранить изменения. Попробуйте ещё раз.</div>
          )}

          <div className={styles.footer}>
            <button className={styles.btnCancel} onClick={onClose} type="button">
              Отмена
            </button>
            <button
              className={styles.btnSubmit}
              onClick={() => mutate()}
              disabled={!isDirty || !name.trim() || isPending}
              type="button"
            >
              {isPending ? "Сохраняю…" : "Сохранить"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
