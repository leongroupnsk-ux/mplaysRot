import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchTotpSetup,
  fetchPlatformSettings,
  setPlatformSetting,
  deletePlatformSetting,
  type PlatformSettingMeta,
} from "../../api/admin";
import styles from "./AdminSettingsPage.module.css";

// ── WB Service Key Section ────────────────────────────────────────────────────

function WBServiceKeySection() {
  const qc = useQueryClient();
  const [inputValue, setInputValue] = useState("");
  const [showInput, setShowInput] = useState(false);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);

  const { data: settings, isLoading } = useQuery({
    queryKey: ["admin-platform-settings"],
    queryFn: fetchPlatformSettings,
  });

  const meta: PlatformSettingMeta | undefined = settings?.wb_service_key;

  const saveMut = useMutation({
    mutationFn: () => setPlatformSetting("wb_service_key", inputValue.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-platform-settings"] });
      setInputValue("");
      setShowInput(false);
      setFeedback({ ok: true, text: "Сервисный ключ сохранён и применён ко всем WB-запросам." });
      setTimeout(() => setFeedback(null), 4000);
    },
    onError: () => {
      setFeedback({ ok: false, text: "Ошибка сохранения. Попробуйте ещё раз." });
    },
  });

  const deleteMut = useMutation({
    mutationFn: () => deletePlatformSetting("wb_service_key"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-platform-settings"] });
      setFeedback({ ok: true, text: "Сервисный ключ удалён. Запросы WB используют ключи пользователей." });
      setTimeout(() => setFeedback(null), 4000);
    },
  });

  return (
    <section className={styles.card} style={{ maxWidth: 620 }}>
      <h2 className={styles.cardTitle}>🔑 WB Сервисный секрет</h2>
      <p className={styles.cardDesc}>
        Платформенный JWT-токен типа «Сервисный» из кабинета WB.<br />
        Автоматически подставляется в заголовок <code style={{ background: "rgba(255,255,255,0.07)", padding: "1px 6px", borderRadius: 4, fontFamily: "monospace" }}>Authorization</code>{" "}
        всех WB API-запросов вместо индивидуального ключа пользователя.
      </p>
      <p className={styles.cardWarn}>
        Ключ хранится зашифрованно и недоступен обычным пользователям платформы.
      </p>

      {/* Current status */}
      {isLoading ? (
        <div style={{ color: "rgba(226,228,240,0.4)", fontSize: 13 }}>Загрузка…</div>
      ) : (
        <div className={styles.keyStatus}>
          <span className={meta?.set ? styles.keyStatusActive : styles.keyStatusEmpty}>
            {meta?.set ? "✓ Ключ задан" : "— Ключ не задан"}
          </span>
          {meta?.set && meta.updated_at && (
            <span className={styles.keyMeta}>
              Обновлён:{" "}
              {new Date(meta.updated_at).toLocaleString("ru-RU", {
                day: "2-digit", month: "2-digit", year: "numeric",
                hour: "2-digit", minute: "2-digit",
              })}
              {meta.updated_by && ` · ${meta.updated_by}`}
            </span>
          )}
        </div>
      )}

      {/* Feedback */}
      {feedback && (
        <div className={feedback.ok ? styles.successMsg : styles.error}>
          {feedback.text}
        </div>
      )}

      {/* Inline input */}
      {showInput && (
        <div className={styles.keyInputRow}>
          <input
            className={styles.keyInput}
            type="password"
            placeholder="eyJhbGci… вставьте JWT-токен"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            autoFocus
          />
          <button
            className={styles.btn}
            onClick={() => saveMut.mutate()}
            disabled={!inputValue.trim() || saveMut.isPending}
            style={{ padding: "10px 16px", fontSize: 13 }}
          >
            {saveMut.isPending ? "Сохранение…" : "Сохранить"}
          </button>
          <button
            className={styles.btnSecondary}
            onClick={() => { setShowInput(false); setInputValue(""); }}
            style={{ padding: "10px 14px", fontSize: 13 }}
          >
            Отмена
          </button>
        </div>
      )}

      {/* Action buttons */}
      {!showInput && (
        <div style={{ display: "flex", gap: 10 }}>
          <button
            className={styles.btn}
            onClick={() => setShowInput(true)}
          >
            {meta?.set ? "Обновить ключ" : "Задать ключ"}
          </button>
          {meta?.set && (
            <button
              className={styles.btnDanger}
              onClick={() => deleteMut.mutate()}
              disabled={deleteMut.isPending}
            >
              {deleteMut.isPending ? "Удаление…" : "Удалить ключ"}
            </button>
          )}
        </div>
      )}
    </section>
  );
}

// ── TOTP Section ──────────────────────────────────────────────────────────────

function TotpSection() {
  const [totp, setTotp] = useState<{ totp_secret: string; totp_uri: string; message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSetup = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTotpSetup();
      setTotp(data);
    } catch {
      setError("Не удалось сгенерировать TOTP-секрет.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className={styles.card}>
      <h2 className={styles.cardTitle}>TOTP-аутентификация</h2>
      <p className={styles.cardDesc}>
        Каждому администратору нужна настроенная TOTP для входа в панель.
        Нажмите кнопку ниже, чтобы сгенерировать новый секретный ключ и
        отсканировать QR-код в Google Authenticator или Authy.
      </p>
      <p className={styles.cardWarn}>
        Внимание: генерация нового ключа аннулирует предыдущий TOTP.
      </p>

      {!totp && (
        <button className={styles.btn} onClick={handleSetup} disabled={loading}>
          {loading ? "Генерация…" : "Сгенерировать TOTP-ключ"}
        </button>
      )}

      {error && <p className={styles.error}>{error}</p>}

      {totp && (
        <div className={styles.totpResult}>
          <p className={styles.totpMessage}>{totp.message}</p>
          <div className={styles.totpQrWrap}>
            <img
              className={styles.totpQr}
              src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(totp.totp_uri)}`}
              alt="TOTP QR-code"
              width={200}
              height={200}
            />
          </div>
          <label className={styles.secretLabel}>
            Секретный ключ (резервная копия):
            <code className={styles.secretCode}>{totp.totp_secret}</code>
          </label>
          <p className={styles.totpHint}>
            После сканирования QR-кода проверьте, что приложение генерирует
            6-значные коды, и войдите заново с новым кодом.
          </p>
          <button className={styles.btnSecondary} onClick={() => setTotp(null)}>
            Сгенерировать новый
          </button>
        </div>
      )}
    </section>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminSettingsPage() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Настройки платформы</h1>
        <p className={styles.subtitle}>Платформенные ключи и безопасность администратора</p>
      </header>

      <WBServiceKeySection />
      <TotpSection />
    </div>
  );
}
