import { useEffect, useState, useCallback } from "react";
import adminApi from "../../api/admin";
import styles from "./AdminBillingPage.module.css";

interface Plan {
  id: string; slug: string; name: string;
  price_monthly: number; price_yearly: number;
  is_active: boolean; sort_order: number;
}
interface Promo {
  id: string; code: string; discount_pct: number;
  max_uses: number | null; used_count: number;
  valid_until: string | null; plan_slug: string | null;
  is_active: boolean; created_at: string;
}

export default function AdminBillingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [promos, setPromos] = useState<Promo[]>([]);
  const [loading, setLoading] = useState(true);

  // New promo form
  const [newCode, setNewCode] = useState("");
  const [newDiscount, setNewDiscount] = useState("10");
  const [newMaxUses, setNewMaxUses] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, pr] = await Promise.all([
        adminApi.get<Plan[]>("/billing/plans").then((r) => r.data),
        adminApi.get<Promo[]>("/billing/promos").then((r) => r.data),
      ]);
      setPlans(p);
      setPromos(pr);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const togglePlan = async (plan: Plan) => {
    await adminApi.patch(`/billing/plans/${plan.id}`, { is_active: !plan.is_active });
    load();
  };

  const deletePromo = async (id: string) => {
    if (!confirm("Деактивировать промокод?")) return;
    await adminApi.delete(`/billing/promos/${id}`);
    load();
  };

  const createPromo = async () => {
    if (!newCode || !newDiscount) return;
    setCreating(true);
    setCreateError(null);
    try {
      await adminApi.post("/billing/promos", {
        code: newCode.toUpperCase(),
        discount_pct: Number(newDiscount) / 100,
        max_uses: newMaxUses ? Number(newMaxUses) : null,
      });
      setNewCode(""); setNewDiscount("10"); setNewMaxUses("");
      load();
    } catch {
      setCreateError("Ошибка при создании промокода (возможно, код уже существует).");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Биллинг</h1>
        <p className={styles.subtitle}>Управление тарифами и промокодами</p>
      </header>

      {/* Plans table */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Тарифные планы</h2>
        {loading ? <p className={styles.loading}>Загрузка…</p> : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr><th>Slug</th><th>Название</th><th>Цена / мес</th><th>Цена / год</th><th>Статус</th><th></th></tr>
              </thead>
              <tbody>
                {plans.map((p) => (
                  <tr key={p.id}>
                    <td><code className={styles.code}>{p.slug}</code></td>
                    <td>{p.name}</td>
                    <td>{p.price_monthly.toLocaleString("ru")} ₽</td>
                    <td>{p.price_yearly.toLocaleString("ru")} ₽</td>
                    <td>
                      <span className={p.is_active ? styles.statusOn : styles.statusOff}>
                        {p.is_active ? "Активен" : "Архив"}
                      </span>
                    </td>
                    <td>
                      <button className={styles.actionBtn} onClick={() => togglePlan(p)}>
                        {p.is_active ? "Архивировать" : "Восстановить"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Promo codes */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Промокоды</h2>

        {/* Create promo */}
        <div className={styles.promoCreate}>
          <input className={styles.input} placeholder="Код (напр. SUMMER25)"
            value={newCode} onChange={(e) => setNewCode(e.target.value)} />
          <input className={styles.input} placeholder="Скидка %" type="number" min="1" max="100"
            value={newDiscount} onChange={(e) => setNewDiscount(e.target.value)} style={{ width: 100 }} />
          <input className={styles.input} placeholder="Макс. использований" type="number" min="1"
            value={newMaxUses} onChange={(e) => setNewMaxUses(e.target.value)} style={{ width: 160 }} />
          <button className={styles.createBtn} onClick={createPromo} disabled={creating || !newCode}>
            {creating ? "Создание…" : "+ Создать"}
          </button>
        </div>
        {createError && <p className={styles.error}>{createError}</p>}

        {loading ? <p className={styles.loading}>Загрузка…</p> : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr><th>Код</th><th>Скидка</th><th>Использований</th><th>Действует до</th><th>Статус</th><th></th></tr>
              </thead>
              <tbody>
                {promos.length === 0 && (
                  <tr><td colSpan={6} className={styles.empty}>Промокодов пока нет</td></tr>
                )}
                {promos.map((pr) => (
                  <tr key={pr.id} className={pr.is_active ? "" : styles.rowOff}>
                    <td><code className={styles.code}>{pr.code}</code></td>
                    <td>{Math.round(pr.discount_pct * 100)}%</td>
                    <td>{pr.used_count}{pr.max_uses ? ` / ${pr.max_uses}` : ""}</td>
                    <td>{pr.valid_until ? new Date(pr.valid_until).toLocaleDateString("ru") : "∞"}</td>
                    <td>
                      <span className={pr.is_active ? styles.statusOn : styles.statusOff}>
                        {pr.is_active ? "Активен" : "Деакт."}
                      </span>
                    </td>
                    <td>
                      {pr.is_active && (
                        <button className={styles.deleteBtn} onClick={() => deletePromo(pr.id)}>✕</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
