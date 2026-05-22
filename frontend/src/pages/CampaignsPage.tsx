import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchCampaigns, patchCampaign } from "../api/campaigns";
import type { Campaign } from "../api/types";
import CreateCampaignModal from "../components/campaign/CreateCampaignModal";
import EditCampaignModal from "../components/campaign/EditCampaignModal";
import styles from "./CampaignsPage.module.css";
import pageStyles from "./Page.module.css";

const MARKETPLACE_LABELS: Record<string, string> = {
  ozon: "Ozon",
  wildberries: "WB",
  yandex_market: "ЯМ",
  amazon: "Amazon",
};

const AD_LABELS: Record<string, string> = {
  yandex_direct: "Директ",
  vk_ads: "VK Ads",
  vk_blogger: "VK Блогер",
  telegram_ads: "TG Ads",
  messenger_max: "MAX",
};

function StatusDot({ active }: { active: boolean }) {
  return (
    <span
      className={active ? styles.dotActive : styles.dotPaused}
      title={active ? "Активна" : "На паузе"}
    />
  );
}

export default function CampaignsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editCampaign, setEditCampaign] = useState<Campaign | null>(null);

  const { data: campaigns = [], isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: fetchCampaigns,
  });

  const { mutate: toggleActive } = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      patchCampaign(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaigns"] }),
  });

  return (
    <div className={pageStyles.page}>
      <div className={pageStyles.toolbar}>
        <h1 className={pageStyles.heading}>Кампании</h1>
        <button className={styles.btnCreate} onClick={() => setShowModal(true)} type="button">
          + Создать кампанию
        </button>
      </div>

      {isLoading && (
        <div className={styles.empty}>Загрузка…</div>
      )}

      {!isLoading && campaigns.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>Нет кампаний</p>
          <p className={styles.emptyHint}>Создайте первую кампанию, чтобы начать отслеживать трафик</p>
          <button className={styles.btnCreate} onClick={() => setShowModal(true)} type="button">
            + Создать кампанию
          </button>
        </div>
      )}

      {campaigns.length > 0 && (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Название</th>
                <th>Маркетплейс</th>
                <th>Площадка</th>
                <th>Бюджет</th>
                <th>Статус</th>
                <th>Создана</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr
                  key={c.id}
                  className={styles.row}
                  onClick={() => navigate(`/campaigns/${c.id}`)}
                >
                  <td className={styles.nameCell}>
                    <StatusDot active={c.is_active} />
                    <span className={styles.name}>{c.name}</span>
                  </td>
                  <td>
                    <span className={styles.badge}>{MARKETPLACE_LABELS[c.marketplace] ?? c.marketplace}</span>
                  </td>
                  <td>
                    <span className={`${styles.badge} ${styles.badgeAd}`}>
                      {AD_LABELS[c.ad_platform] ?? c.ad_platform}
                    </span>
                  </td>
                  <td className={styles.budget}>
                    {c.budget != null
                      ? `${c.budget.toLocaleString("ru")} ₽`
                      : <span className={styles.muted}>—</span>}
                  </td>
                  <td>
                    <span className={c.is_active ? styles.statusActive : styles.statusPaused}>
                      {c.is_active ? "Активна" : "На паузе"}
                    </span>
                  </td>
                  <td className={styles.muted}>
                    {new Date(c.created_at).toLocaleDateString("ru")}
                  </td>
                  <td
                    onClick={(e) => e.stopPropagation()}
                    className={styles.actions}
                  >
                    <button
                      className={styles.btnEdit}
                      onClick={() => setEditCampaign(c)}
                      type="button"
                    >
                      Изменить
                    </button>
                    <button
                      className={c.is_active ? styles.btnPause : styles.btnResume}
                      onClick={() => toggleActive({ id: c.id, is_active: !c.is_active })}
                      type="button"
                    >
                      {c.is_active ? "Пауза" : "Запустить"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && <CreateCampaignModal onClose={() => setShowModal(false)} />}
      {editCampaign && (
        <EditCampaignModal campaign={editCampaign} onClose={() => setEditCampaign(null)} />
      )}
    </div>
  );
}
