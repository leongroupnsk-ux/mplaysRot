import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteIntegration, validateIntegration, type Integration } from "../../api/integrations";
import styles from "./IntegrationCard.module.css";

const LOGOS: Record<string, string> = {
  ozon: "🟦", wildberries: "🍇", yandex_market: "🟡", amazon: "📦",
  yandex_direct: "Y", vk_ads: "V", vk_blogger: "📝", telegram_ads: "✈️", messenger_max: "💬",
};

const NAMES: Record<string, string> = {
  ozon: "Ozon", wildberries: "Wildberries", yandex_market: "Яндекс.Маркет", amazon: "Amazon",
  yandex_direct: "Яндекс.Директ", vk_ads: "VK Ads", vk_blogger: "VK Блогер",
  telegram_ads: "Telegram Ads", messenger_max: "Messenger MAX",
};

interface Props {
  integration: Integration;
  onConnect: () => void;
}

export default function IntegrationCard({ integration, onConnect }: Props) {
  const qc = useQueryClient();
  const [validateMsg, setValidateMsg] = useState<string | null>(null);

  const isConnected = integration.status === "active";

  const deleteMut = useMutation({
    mutationFn: () => deleteIntegration(integration.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["integrations"] }),
  });

  const validateMut = useMutation({
    mutationFn: () => validateIntegration(integration.id),
    onSuccess: (res) => {
      setValidateMsg(res.message);
      qc.invalidateQueries({ queryKey: ["integrations"] });
      setTimeout(() => setValidateMsg(null), 3000);
    },
  });

  const lastSync = integration.last_synced_at
    ? new Date(integration.last_synced_at).toLocaleString("ru-RU", {
        day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
      })
    : null;

  const dotClass =
    integration.status === "active" ? styles.dotActive :
    integration.status === "error"  ? styles.dotError  : styles.dotPending;

  const statusClass =
    integration.status === "active" ? styles.statusActive :
    integration.status === "error"  ? styles.statusError  : styles.statusPending;

  const statusLabel =
    integration.status === "active" ? "Активен" :
    integration.status === "error"  ? "Ошибка"  : "Ожидает";

  return (
    <div className={styles.card}>
      <div className={styles.logo}>{LOGOS[integration.provider] ?? "?"}</div>

      <div className={styles.info}>
        <div className={styles.name}>{NAMES[integration.provider] ?? integration.provider}</div>
        <div className={styles.meta}>
          {integration.account_name ?? "Аккаунт не указан"}
          {lastSync && <span className={styles.syncing}> · Синхр. {lastSync}</span>}
          {validateMsg && <span style={{ color: "var(--green)", marginLeft: 8 }}>{validateMsg}</span>}
        </div>
      </div>

      <div className={styles.status}>
        <span className={`${styles.dot} ${dotClass}`} />
        <span className={statusClass}>{statusLabel}</span>
      </div>

      <div className={styles.actions}>
        {isConnected ? (
          <>
            <button
              className={styles.btnGhost}
              onClick={() => validateMut.mutate()}
              disabled={validateMut.isPending}
            >
              {validateMut.isPending ? "Проверка…" : "Проверить"}
            </button>
            <button
              className={styles.btnDanger}
              onClick={() => deleteMut.mutate()}
              disabled={deleteMut.isPending}
            >
              Отключить
            </button>
          </>
        ) : (
          <>
            <button className={styles.btnPrimary} onClick={onConnect}>
              {integration.status === "error" ? "Повторить" : "Подключить"}
            </button>
            {integration.status === "error" && (
              <button
                className={styles.btnDanger}
                onClick={() => deleteMut.mutate()}
                disabled={deleteMut.isPending}
              >
                Удалить
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
