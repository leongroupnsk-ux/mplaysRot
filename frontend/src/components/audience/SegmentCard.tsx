import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadSegment } from "../../api/segments";
import type { SegmentUpload } from "../../api/types";
import type { AdPlatform } from "../../api/types";
import styles from "./SegmentCard.module.css";

const STATUS_LABEL: Record<SegmentUpload["status"], string> = {
  pending: "В очереди",
  processing: "Обработка",
  uploaded: "Загружен",
  failed: "Ошибка",
};

const STATUS_COLOR: Record<SegmentUpload["status"], string> = {
  pending: "var(--text-muted)",
  processing: "var(--yellow)",
  uploaded: "var(--green)",
  failed: "var(--red)",
};

const AD_PLATFORMS: { value: AdPlatform; label: string }[] = [
  { value: "vk_ads",        label: "VK Ads" },
  { value: "yandex_direct", label: "Яндекс.Директ" },
  { value: "telegram_ads",  label: "Telegram Ads" },
  { value: "messenger_max", label: "Messenger MAX" },
];

interface Props {
  campaignId: string;
  segments: SegmentUpload[];
}

export default function SegmentCard({ campaignId, segments }: Props) {
  const qc = useQueryClient();
  const [adPlatform, setAdPlatform] = useState<AdPlatform>("vk_ads");
  const [minRoas, setMinRoas] = useState("3.0");
  const [lookalike, setLookalike] = useState(false);
  const [scale, setScale] = useState(5);

  const upload = useMutation({
    mutationFn: () =>
      uploadSegment({
        campaign_id: campaignId,
        ad_platform: adPlatform,
        lookalike,
        lookalike_scale: scale,
        min_roas_threshold: parseFloat(minRoas) || 3.0,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["segments", campaignId] }),
  });

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Аудитории и Look-alike</h3>

      {/* Controls */}
      <div className={styles.controls}>
        <div className={styles.controlRow}>
          <label className={styles.label}>Площадка</label>
          <select
            className={styles.select}
            value={adPlatform}
            onChange={(e) => setAdPlatform(e.target.value as AdPlatform)}
          >
            {AD_PLATFORMS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>

        <div className={styles.controlRow}>
          <label className={styles.label}>Мин. ROAS</label>
          <input
            className={styles.numInput}
            type="number"
            min="0"
            step="0.5"
            value={minRoas}
            onChange={(e) => setMinRoas(e.target.value)}
          />
        </div>

        <div className={styles.controlRow}>
          <label className={styles.label}>Look-alike</label>
          <input
            type="checkbox"
            checked={lookalike}
            onChange={(e) => setLookalike(e.target.checked)}
            style={{ accentColor: "var(--accent)", width: 16, height: 16 }}
          />
          {lookalike && (
            <>
              <label className={styles.label} style={{ marginLeft: 8 }}>Масштаб</label>
              <select
                className={styles.select}
                value={scale}
                onChange={(e) => setScale(Number(e.target.value))}
              >
                {[1, 2, 3, 5, 7, 10].map((s) => (
                  <option key={s} value={s}>{s}x</option>
                ))}
              </select>
            </>
          )}
        </div>
      </div>

      <div className={styles.actions}>
        <button
          className={styles.btn}
          onClick={() => { setLookalike(false); upload.mutate(); }}
          disabled={upload.isPending}
        >
          Загрузить seed
        </button>
        <button
          className={styles.btnAccent}
          onClick={() => { setLookalike(true); upload.mutate(); }}
          disabled={upload.isPending}
        >
          {upload.isPending ? "Загрузка…" : "Создать look-alike"}
        </button>
      </div>

      {upload.isError && (
        <p style={{ fontSize: 12, color: "var(--red)", marginTop: 8 }}>
          Ошибка при создании сегмента. Проверьте подключение площадки.
        </p>
      )}

      {segments.length > 0 && (
        <div className={styles.history}>
          <p className={styles.historyLabel}>История активаций</p>
          {segments.map((seg) => (
            <div key={seg.id} className={styles.row}>
              <div>
                <span className={styles.platform}>{seg.ad_platform}</span>
                {seg.lookalike && <span className={styles.badge}>Look-alike</span>}
              </div>
              <div className={styles.meta}>
                {seg.seed_size != null && (
                  <span>{seg.seed_size.toLocaleString("ru")} ID</span>
                )}
                <span style={{ color: STATUS_COLOR[seg.status] }}>
                  {STATUS_LABEL[seg.status]}
                </span>
                {seg.status === "processing" && <span className={styles.spinner} />}
              </div>
              {seg.error_message && (
                <p className={styles.error}>{seg.error_message}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
