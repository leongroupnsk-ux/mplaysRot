import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchStores } from "../../api/stores";
import { deleteIntegration } from "../../api/integrations";
import styles from "./StoresWidget.module.css";

const LOGOS: Record<string, string> = {
  ozon: "🟦", wildberries: "🍇", yandex_market: "🟡", amazon: "📦",
};

const PROVIDER_NAMES: Record<string, string> = {
  ozon: "Ozon", wildberries: "Wildberries",
  yandex_market: "Яндекс.Маркет", amazon: "Amazon",
};

function syncStatus(lastSyncAt: string | null): { ok: boolean; label: string } {
  if (!lastSyncAt) return { ok: false, label: "Не синхронизировано" };
  const diffMs = Date.now() - new Date(lastSyncAt).getTime();
  const diffH = diffMs / 3_600_000;
  if (diffH > 3) return { ok: false, label: `Обновлено ${Math.round(diffH)} ч назад` };
  const diffM = Math.round(diffMs / 60_000);
  if (diffM < 2) return { ok: true, label: "Только что" };
  return { ok: true, label: `${diffM} мин назад` };
}

export default function StoresWidget() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const { data: stores = [] } = useQuery({
    queryKey: ["stores"],
    queryFn: fetchStores,
    refetchInterval: 60_000,
  });

  const disconnectMut = useMutation({
    mutationFn: (connectionId: string) => deleteIntegration(connectionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["stores"] });
      qc.invalidateQueries({ queryKey: ["integrations"] });
      setConfirmId(null);
    },
  });

  return (
    <div className={styles.widget}>
      <div className={styles.header}>
        <span className={styles.title}>Мои магазины</span>
        <Link to="/settings/integrations" className={styles.settingsLink}>
          Управление →
        </Link>
      </div>

      {stores.length === 0 ? (
        <div className={styles.empty}>
          Нет подключённых магазинов.{" "}
          <span
            className={styles.emptyLink}
            onClick={() => navigate("/settings/integrations")}
          >
            Подключить
          </span>
        </div>
      ) : (
        <div className={styles.grid}>
          {stores.map((store) => {
            const sync = syncStatus(store.last_sync_at);
            const isConfirming = confirmId === store.id;

            return (
              <div key={store.id} className={styles.card}>
                <div className={styles.cardHeader}>
                  <div className={styles.logo}>
                    {LOGOS[store.provider] ?? "🏪"}
                  </div>
                  <div className={styles.storeInfo}>
                    <div className={styles.storeName}>{store.name}</div>
                    <div className={styles.provider}>
                      {PROVIDER_NAMES[store.provider] ?? store.provider}
                    </div>
                  </div>
                </div>

                <div className={styles.syncRow}>
                  <span
                    className={`${styles.syncDot} ${
                      sync.ok ? styles.syncDotOk : styles.syncDotStale
                    }`}
                  />
                  <span className={styles.syncText}>{sync.label}</span>
                </div>

                <div className={styles.actions}>
                  <button
                    className={styles.analyticsBtn}
                    onClick={() =>
                      navigate(`/attribution?marketplace=${store.provider}`)
                    }
                  >
                    📊 Перейти к аналитике
                  </button>

                  {isConfirming ? (
                    <div className={styles.confirmRow}>
                      <span className={styles.confirmText}>Отключить?</span>
                      <button
                        className={styles.confirmYes}
                        disabled={disconnectMut.isPending}
                        onClick={() => disconnectMut.mutate(store.connection_id)}
                      >
                        {disconnectMut.isPending ? "…" : "Да"}
                      </button>
                      <button
                        className={styles.confirmNo}
                        onClick={() => setConfirmId(null)}
                      >
                        Нет
                      </button>
                    </div>
                  ) : (
                    <button
                      className={styles.disconnectBtn}
                      onClick={() => setConfirmId(store.id)}
                      title="Отключить магазин"
                    >
                      Отключить
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
