import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { useAuthStore } from "../store/auth";
import api from "../api/client";
import type { Me } from "../api/auth";
import styles from "./SettingsProfilePage.module.css";
import pageStyles from "./Page.module.css";

function updateProfile(payload: {
  full_name?: string;
  current_password?: string;
  new_password?: string;
}) {
  return api.patch<Me>("/auth/me", payload).then((r) => r.data);
}

export default function SettingsProfilePage() {
  const { user, setUser, logout } = useAuthStore();

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [nameSaved, setNameSaved] = useState(false);

  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwSaved, setPwSaved] = useState(false);

  const nameMutation = useMutation({
    mutationFn: () => updateProfile({ full_name: fullName }),
    onSuccess: (updated) => { setUser(updated); setNameSaved(true); setTimeout(() => setNameSaved(false), 2500); },
  });

  const pwMutation = useMutation({
    mutationFn: () => updateProfile({ current_password: currentPw, new_password: newPw }),
    onSuccess: () => {
      setCurrentPw(""); setNewPw(""); setConfirmPw("");
      setPwSaved(true);
      setTimeout(() => setPwSaved(false), 2500);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setPwError(msg ?? "Не удалось изменить пароль.");
    },
  });

  const handleNameSubmit = (e: FormEvent) => {
    e.preventDefault();
    nameMutation.mutate();
  };

  const handlePwSubmit = (e: FormEvent) => {
    e.preventDefault();
    setPwError(null);
    if (newPw.length < 8) { setPwError("Минимум 8 символов."); return; }
    if (newPw !== confirmPw) { setPwError("Пароли не совпадают."); return; }
    pwMutation.mutate();
  };

  return (
    <div className={pageStyles.page}>
      <div className={pageStyles.toolbar}>
        <h1 className={pageStyles.heading}>Профиль</h1>
      </div>

      <div className={styles.sections}>
        {/* ── Основная информация ── */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Основная информация</h2>

          <form className={styles.form} onSubmit={handleNameSubmit}>
            <div className={styles.field}>
              <label className={styles.label}>Email</label>
              <div className={styles.staticValue}>{user?.email ?? "—"}</div>
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="fullName">Имя</label>
              <input
                id="fullName"
                className={styles.input}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Иван Иванов"
              />
            </div>

            <div className={styles.footer}>
              {nameSaved && <span className={styles.savedMsg}>Сохранено</span>}
              <button
                className={styles.btnPrimary}
                type="submit"
                disabled={nameMutation.isPending || fullName === (user?.full_name ?? "")}
              >
                {nameMutation.isPending ? "Сохраняю…" : "Сохранить"}
              </button>
            </div>
          </form>
        </section>

        {/* ── Пароль ── */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Изменить пароль</h2>

          <form className={styles.form} onSubmit={handlePwSubmit}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="currentPw">Текущий пароль</label>
              <input
                id="currentPw"
                className={styles.input}
                type="password"
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="newPw">Новый пароль</label>
              <input
                id="newPw"
                className={styles.input}
                type="password"
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                placeholder="Не менее 8 символов"
                autoComplete="new-password"
                required
                minLength={8}
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label} htmlFor="confirmPw">Подтвердите пароль</label>
              <input
                id="confirmPw"
                className={styles.input}
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
                required
              />
            </div>

            {pwError && <div className={styles.error}>{pwError}</div>}

            <div className={styles.footer}>
              {pwSaved && <span className={styles.savedMsg}>Пароль изменён</span>}
              <button
                className={styles.btnPrimary}
                type="submit"
                disabled={pwMutation.isPending || !currentPw || !newPw || !confirmPw}
              >
                {pwMutation.isPending ? "Изменяю…" : "Изменить пароль"}
              </button>
            </div>
          </form>
        </section>

        {/* ── Сессия ── */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Сессия</h2>
          <p className={styles.hint}>
            Вы вошли как <strong>{user?.email}</strong>. Роль: {user?.role ?? "—"}.
          </p>
          <button className={styles.btnDanger} onClick={logout} type="button">
            Выйти из аккаунта
          </button>
        </section>
      </div>
    </div>
  );
}
