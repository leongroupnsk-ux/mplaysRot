import { useEffect, useState, useCallback } from "react";
import {
  fetchAdminUsers,
  patchAdminUser,
  changeUserPassword,
  fetchBillingPlans,
  type AdminUser,
  type BillingPlan,
} from "../../api/admin";
import styles from "./AdminUsersPage.module.css";

const ROLE_LABELS: Record<string, string> = {
  admin: "Администратор",
  owner: "Владелец",
  analyst: "Аналитик",
};

const ROLE_OPTIONS = ["analyst", "owner", "admin"];

// Edit Modal Component
function EditUserModal({
  user,
  plans,
  onSave,
  onClose,
}: {
  user: AdminUser;
  plans: BillingPlan[];
  onSave: (user: AdminUser) => void;
  onClose: () => void;
}) {
  const [email, setEmail] = useState(user.email);
  const [fullName, setFullName] = useState(user.full_name);
  const [role, setRole] = useState(user.role);
  const [planId, setPlanId] = useState(user.plan_id || "");
  const [isActive, setIsActive] = useState(user.is_active);
  const [isStopped, setIsStopped] = useState(user.is_stopped);
  const [newPassword, setNewPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [loading, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSave = async () => {
    if (!email || !fullName) {
      setError("Email и имя обязательны");
      return;
    }
    if (newPassword && newPassword !== passwordConfirm) {
      setError("Пароли не совпадают");
      return;
    }

    setSaving(true);
    setError(null);
    setSuccessMsg(null);

    try {
      // Update basic fields
      const updated = await patchAdminUser(user.id, {
        email,
        full_name: fullName,
        role,
        is_active: isActive,
        is_stopped: isStopped,
        plan_id: planId || null,
      });

      // Change password if provided
      if (newPassword) {
        await changeUserPassword(user.id, newPassword);
      }

      setSuccessMsg("Пользователь успешно обновлен");
      onSave(updated);
      setTimeout(onClose, 1500);
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail || "Ошибка при сохранении";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div
        className={styles.editModal}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>Редактирование пользователя</h2>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>

        {error && <div className={styles.errorBox}>{error}</div>}
        {successMsg && <div className={styles.successBox}>{successMsg}</div>}

        <div className={styles.modalBody}>
          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Email</label>
            <input
              type="email"
              className={styles.formInput}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Полное имя</label>
            <input
              type="text"
              className={styles.formInput}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Роль</label>
            <select
              className={styles.formSelect}
              value={role}
              onChange={(e) => setRole(e.target.value)}
              disabled={loading}
            >
              {ROLE_OPTIONS.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Тарификация</label>
            <select
              className={styles.formSelect}
              value={planId}
              onChange={(e) => setPlanId(e.target.value)}
              disabled={loading}
            >
              <option value="">— Нет плана —</option>
              {plans.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} (${p.price})
                </option>
              ))}
            </select>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formLabel}>Новый пароль (опционально)</label>
            <input
              type="password"
              className={styles.formInput}
              placeholder="Оставить пустым для сохранения текущего"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              disabled={loading}
            />
          </div>

          {newPassword && (
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Подтверждение пароля</label>
              <input
                type="password"
                className={styles.formInput}
                placeholder="Повторите пароль"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                disabled={loading}
              />
            </div>
          )}

          <div className={styles.formGroup}>
            <label className={styles.formCheckbox}>
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                disabled={loading}
              />
              <span>Активен</span>
            </label>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.formCheckbox}>
              <input
                type="checkbox"
                checked={isStopped}
                onChange={(e) => setIsStopped(e.target.checked)}
                disabled={loading}
              />
              <span>На стопе (заморозить аккаунт)</span>
            </label>
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button
            className={styles.btnSecondary}
            onClick={onClose}
            disabled={loading}
          >
            Отмена
          </button>
          <button
            className={styles.btnPrimary}
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? "Сохранение..." : "Сохранить"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);

  const load = useCallback(async (q?: string) => {
    setLoading(true);
    setError(null);
    try {
      const [usersData, plansData] = await Promise.all([
        fetchAdminUsers({ limit: 100, search: q || undefined }),
        fetchBillingPlans(),
      ]);
      setUsers(usersData);
      setPlans(plansData);
    } catch {
      setError("Не удалось загрузить данные.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load(search);
  };

  const handleEdit = (user: AdminUser) => {
    setEditingUser(user);
  };

  const handleSaveUser = (updated: AdminUser) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === updated.id ? updated : u))
    );
    setEditingUser(null);
  };


  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Пользователи</h1>
          <p className={styles.subtitle}>{users.length} пользователей</p>
        </div>
        <form className={styles.searchForm} onSubmit={handleSearch}>
          <input
            className={styles.searchInput}
            type="search"
            placeholder="Поиск по email или имени…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button className={styles.searchBtn} type="submit">
            Найти
          </button>
        </form>
      </header>

      {error && <p className={styles.error}>{error}</p>}

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Email</th>
              <th>Имя</th>
              <th>Роль</th>
              <th>План</th>
              <th>Статус</th>
              <th>Стоп</th>
              <th>Регистрация</th>
              <th>Действие</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={8} className={styles.loadingCell}>
                  Загрузка…
                </td>
              </tr>
            )}
            {!loading && users.length === 0 && (
              <tr>
                <td colSpan={8} className={styles.emptyCell}>
                  Пользователи не найдены
                </td>
              </tr>
            )}
            {users.map((u) => (
              <tr
                key={u.id}
                className={`${u.is_active ? "" : styles.rowInactive} ${
                  u.is_stopped ? styles.rowStopped : ""
                }`}
              >
                <td className={styles.cellEmail}>{u.email}</td>
                <td>{u.full_name}</td>
                <td>
                  <span className={`${styles.roleBadge} ${styles[`role_${u.role}`]}`}>
                    {ROLE_LABELS[u.role] ?? u.role}
                  </span>
                </td>
                <td className={styles.cellPlan}>
                  <span className={styles.planBadge}>
                    {u.plan_name || "—"}
                  </span>
                </td>
                <td>
                  <span
                    className={`${styles.statusBadge} ${
                      u.is_active ? styles.statusActive : styles.statusInactive
                    }`}
                  >
                    {u.is_active ? "✓ Активен" : "✗ Неактивен"}
                  </span>
                </td>
                <td>
                  <span
                    className={`${styles.stopBadge} ${
                      u.is_stopped ? styles.stopOn : styles.stopOff
                    }`}
                  >
                    {u.is_stopped ? "⏸ Стоп" : "—"}
                  </span>
                </td>
                <td className={styles.cellDate}>
                  {new Date(u.created_at).toLocaleDateString("ru")}
                </td>
                <td>
                  <button
                    className={styles.editBtn}
                    onClick={() => handleEdit(u)}
                    title="Редактировать"
                  >
                    Правка
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editingUser && (
        <EditUserModal
          user={editingUser}
          plans={plans}
          onSave={handleSaveUser}
          onClose={() => setEditingUser(null)}
        />
      )}
    </div>
  );
}
