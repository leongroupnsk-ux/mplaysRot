import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuthStore } from "../store/auth";
import { register, fetchMe } from "../api/auth";
import styles from "./LoginPage.module.css";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { setTokens, setUser } = useAuthStore();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    if (password.length < 8) {
      setError("Пароль должен содержать не менее 8 символов.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const tokens = await register(email, password, fullName || undefined);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await fetchMe();
      setUser(me);
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } }).response?.status;
      if (status === 409) {
        setError("Этот email уже зарегистрирован.");
      } else if (status === 422) {
        setError("Проверьте правильность введённых данных.");
      } else {
        setError("Ошибка сервера. Попробуйте позже.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.root}>
      <div className={styles.card}>
        <div className={styles.logo}>
          <div className={styles.logoMark}>MP</div>
          <span className={styles.logoText}>MPlays</span>
        </div>

        <h1 className={styles.heading}>Регистрация</h1>
        <p className={styles.subheading}>Создайте аккаунт бесплатно</p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="fullName">Имя <span style={{ opacity: 0.5 }}>(необязательно)</span></label>
            <input
              id="fullName"
              className={styles.input}
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Иван Иванов"
              autoComplete="name"
              autoFocus
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="email">Email</label>
            <input
              id="email"
              className={styles.input}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="password">Пароль</label>
            <input
              id="password"
              className={styles.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Не менее 8 символов"
              autoComplete="new-password"
              required
              minLength={8}
            />
          </div>

          {error && <div className={styles.error}>{error}</div>}

          <button
            className={styles.btnSubmit}
            type="submit"
            disabled={loading || !email || !password}
          >
            {loading ? "Создаю аккаунт…" : "Создать аккаунт"}
          </button>
        </form>

        <p className={styles.footer}>
          Уже есть аккаунт?
          <Link to="/login" className={styles.footerLink}>Войти</Link>
        </p>
      </div>
    </div>
  );
}
