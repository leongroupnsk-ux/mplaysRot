import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchIntegrations, deleteIntegration, type Integration } from "../api/integrations";
import ConnectModal from "../components/integrations/ConnectModal";
import styles from "./SettingsIntegrationsPage.module.css";

const MARKETPLACES = [
  { provider: "ozon",          name: "Ozon",            logo: "🟦" },
  { provider: "wildberries",   name: "Wildberries",     logo: "🍇" },
  { provider: "yandex_market", name: "Яндекс.Маркет",  logo: "🟡" },
  { provider: "amazon",        name: "Amazon",          logo: "📦" },
];

const AD_PLATFORMS = [
  { provider: "yandex_direct",  name: "Яндекс.Директ",   logo: "Y" },
  { provider: "vk_ads",         name: "VK Ads",           logo: "V" },
  { provider: "vk_blogger",     name: "VK Блогер",        logo: "📝" },
  { provider: "telegram_ads",   name: "Telegram Ads",     logo: "✈️" },
  { provider: "messenger_max",  name: "Messenger MAX",    logo: "💬" },
];

const NAMES: Record<string, string> = {
  ozon: "Ozon", wildberries: "Wildberries", yandex_market: "Яндекс.Маркет", amazon: "Amazon",
  yandex_direct: "Яндекс.Директ", vk_ads: "VK Ads", vk_blogger: "VK Блогер",
  telegram_ads: "Telegram Ads", messenger_max: "Messenger MAX",
};

const LOGOS: Record<string, string> = {
  ozon: "🟦", wildberries: "🍇", yandex_market: "🟡", amazon: "📦",
  yandex_direct: "Y", vk_ads: "V", vk_blogger: "📝", telegram_ads: "✈️", messenger_max: "💬",
};

interface ModalState {
  provider: string;
  type: "marketplace" | "ad_platform";
}

function ConnectedRow({ integration }: { integration: Integration }) {
  const qc = useQueryClient();
  const [confirm, setConfirm] = useState(false);

  const deleteMut = useMutation({
    mutationFn: () => deleteIntegration(integration.id),
    onSuccess: () => {
      setConfirm(false);
      qc.invalidateQueries({ queryKey: ["integrations"] });
    },
  });

  const lastSync = integration.last_synced_at
    ? new Date(integration.last_synced_at).toLocaleString("ru-RU", {
        day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
      })
    : null;

  const statusLabel =
    integration.status === "active" ? "Активен" :
    integration.status === "error"  ? "Ошибка"  : "Ожидает";

  const statusColor =
    integration.status === "active" ? "#4ade80" :
    integration.status === "error"  ? "#f87171" : "#fbbf24";

  return (
    <div className={styles.connectedRow}>
      <span className={styles.connLogo}>{LOGOS[integration.provider] ?? "?"}</span>
      <div className={styles.connInfo}>
        <span className={styles.connName}>
          {integration.account_name || NAMES[integration.provider] || integration.provider}
        </span>
        {lastSync && <span className={styles.connMeta}>Синхр. {lastSync}</span>}
      </div>
      <span className={styles.connStatus} style={{ color: statusColor }}>● {statusLabel}</span>

      {confirm ? (
        <div className={styles.confirmRow}>
          <span className={styles.confirmText}>Удалить подключение?</span>
          <button
            className={styles.btnDangerSm}
            onClick={() => deleteMut.mutate()}
            disabled={deleteMut.isPending}
          >
            {deleteMut.isPending ? "…" : "Да, удалить"}
          </button>
          <button className={styles.btnGhostSm} onClick={() => setConfirm(false)}>
            Отмена
          </button>
        </div>
      ) : (
        <button className={styles.btnDangerSm} onClick={() => setConfirm(true)}>
          Удалить
        </button>
      )}
    </div>
  );
}

export default function SettingsIntegrationsPage() {
  const { data: integrations = [] } = useQuery({
    queryKey: ["integrations"],
    queryFn: fetchIntegrations,
  });

  const [modal, setModal] = useState<ModalState | null>(null);

  // Группируем все подключения по провайдеру (может быть несколько на 1 провайдер)
  const byProvider = new Map<string, Integration[]>();
  for (const i of integrations) {
    if (!byProvider.has(i.provider)) byProvider.set(i.provider, []);
    byProvider.get(i.provider)!.push(i);
  }

  const renderSection = (
    items: { provider: string; name: string; logo: string }[],
    type: "marketplace" | "ad_platform"
  ) =>
    items.map(({ provider, name, logo }) => {
      const connected = byProvider.get(provider) ?? [];
      return (
        <div key={provider} className={styles.providerBlock}>
          {/* Строки подключённых аккаунтов */}
          {connected.map((c) => (
            <ConnectedRow key={c.id} integration={c} />
          ))}

          {/* Кнопка «Подключить» — всегда видна, но для дубля заблокирует сервер */}
          <div className={connected.length > 0 ? styles.disconnectedCardCompact : styles.disconnectedCard}>
            {connected.length === 0 && (
              <>
                <div className={styles.disconnectedLogo}>{logo}</div>
                <div className={styles.disconnectedInfo}>
                  <div className={styles.disconnectedName}>{name}</div>
                </div>
              </>
            )}
            {connected.length === 0 && (
              <button
                className={styles.btnConnect}
                onClick={() => setModal({ provider, type })}
              >
                Подключить
              </button>
            )}
          </div>
        </div>
      );
    });

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Интеграции</h1>
        <p className={styles.subtitle}>
          Подключите маркетплейсы и рекламные кабинеты, чтобы начать аналитику
        </p>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>Маркетплейсы</div>
        <div className={styles.grid}>
          {renderSection(MARKETPLACES, "marketplace")}
        </div>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>Рекламные кабинеты</div>
        <div className={styles.grid}>
          {renderSection(AD_PLATFORMS, "ad_platform")}
        </div>
      </div>

      {modal && (
        <ConnectModal
          provider={modal.provider}
          type={modal.type}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}
