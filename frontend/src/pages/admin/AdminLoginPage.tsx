import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { adminLogin } from "../../api/admin";
import { useAdminAuthStore } from "../../store/adminAuth";
import styles from "./AdminLoginPage.module.css";

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const { setToken } = useAdminAuthStore();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true);
    setError(null);
    try {
      const token = await adminLogin(email, password, totpCode || null);
      setToken(token);
      navigate("/admin", { replace: true });
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } }).response?.status;
      if (status === 401) {
        setError("Неверные учётные данные или код TOTP.");
      } else {
        setError("Ошибка сервера. Попробуйте позже.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.logoMark}>A</div>
          <div className={styles.headerText}>
            <h1 className={styles.title}>MPlays Admin</h1>
            <p className={styles.subtitle}>Вход в административную панель</p>
          </div>
        </div>

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <label className={styles.label}>
            Email
            <input
              className={styles.input}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
            />
          </label>

          <label className={styles.label}>
            Пароль
            <input
              className={styles.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          <label className={styles.label}>
            Код TOTP <span style={{fontWeight:400,opacity:0.5,fontSize:"12px"}}>(если настроен)</span>
            <input
              className={`${styles.input} ${styles.inputCode}`}
              type="text"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              placeholder="оставьте пустым, если TOTP не настроен"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ""))}
              autoComplete="one-time-code"
            />
          </label>

          {error && <p className={styles.error} role="alert">{error}</p>}

          <button className={styles.btn} type="submit" disabled={loading || !email || !password}>
            {loading ? "Вход…" : "Войти"}
          </button>
        </form>

        <p className={styles.hint}>
          Доступ только для сотрудников MPlays.<br />
          TOTP-приложение: Google Authenticator или Authy.
        </p>
      </div>
    </div>
  );
}
