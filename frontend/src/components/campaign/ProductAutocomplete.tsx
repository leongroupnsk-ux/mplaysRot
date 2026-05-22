import {
  useState, useRef, useEffect, useCallback, type KeyboardEvent,
} from "react";
import { useQuery } from "@tanstack/react-query";
import { searchProducts, type Product } from "../../api/products";
import styles from "./ProductAutocomplete.module.css";

interface Props {
  marketplace?: string;
  value: Product[];
  onChange: (products: Product[]) => void;
  placeholder?: string;
}

export default function ProductAutocomplete({
  marketplace,
  value,
  onChange,
  placeholder = "Поиск по названию или артикулу…",
}: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [tooltipId, setTooltipId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  // Debounce search
  const [debouncedQ, setDebouncedQ] = useState("");
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(query), 280);
    return () => clearTimeout(t);
  }, [query]);

  const selectedIds = new Set(value.map((p) => p.id));

  const { data, isFetching } = useQuery({
    queryKey: ["products-search", debouncedQ, marketplace],
    queryFn: () =>
      searchProducts({
        q: debouncedQ,
        marketplace,
        expand_variations: true,
        limit: 15,
      }),
    enabled: open && debouncedQ.length >= 1,
    staleTime: 30_000,
  });

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const select = useCallback(
    (product: Product) => {
      if (selectedIds.has(product.id)) return;
      onChange([...value, product]);
      setQuery("");
      setOpen(false);
      inputRef.current?.focus();
    },
    [value, onChange, selectedIds]
  );

  const remove = useCallback(
    (id: string) => onChange(value.filter((p) => p.id !== id)),
    [value, onChange]
  );

  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !query && value.length > 0) {
      remove(value[value.length - 1].id);
    }
    if (e.key === "Escape") setOpen(false);
  };

  // Warn about out-of-stock selections
  const outOfStockCount = value.filter((p) => p.stock === 0).length;

  const options = data?.items.filter((p) => !selectedIds.has(p.id)) ?? [];

  return (
    <div className={styles.root} ref={rootRef}>
      <div
        className={styles.inputWrap}
        onClick={() => inputRef.current?.focus()}
      >
        {value.map((p) => (
          <span
            key={p.id}
            className={styles.chip}
            onMouseEnter={() => p.has_variations ? setTooltipId(p.id) : undefined}
            onMouseLeave={() => setTooltipId(null)}
          >
            {p.image_url && (
              <img src={p.image_url} alt="" className={styles.chipImg} />
            )}
            <span className={styles.chipLabel} title={p.title}>
              {p.external_product_id}
            </span>
            {p.has_variations && p.variations.length > 0 && (
              <span className={styles.chipVariants}>
                +{p.variations.length} вар.
              </span>
            )}
            <button
              className={styles.chipRemove}
              onClick={(e) => { e.stopPropagation(); remove(p.id); }}
              type="button"
            >
              ×
            </button>

            {/* Variation tooltip */}
            {tooltipId === p.id && p.variations.length > 0 && (
              <div className={styles.tooltip}>
                {p.variations.map((v) => (
                  <div key={v.external_product_id} className={styles.tooltipRow}>
                    <span>{v.external_product_id}</span>
                    <span style={{ color: v.stock === 0 ? "var(--red)" : undefined }}>
                      {v.stock} шт.
                    </span>
                  </div>
                ))}
              </div>
            )}
          </span>
        ))}

        <input
          ref={inputRef}
          className={styles.input}
          value={query}
          placeholder={value.length === 0 ? placeholder : ""}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKey}
          type="text"
          autoComplete="off"
        />
      </div>

      {open && (query.length >= 1) && (
        <div className={styles.dropdown}>
          {isFetching && <div className={styles.loading}>Поиск…</div>}
          {!isFetching && options.length === 0 && (
            <div className={styles.noResults}>Товары не найдены</div>
          )}
          {options.map((p) => (
            <div
              key={p.id}
              className={styles.option}
              onMouseDown={(e) => { e.preventDefault(); select(p); }}
            >
              {p.image_url ? (
                <img src={p.image_url} alt="" className={styles.optionImg} />
              ) : (
                <div className={styles.optionImg} />
              )}
              <div className={styles.optionInfo}>
                <div className={styles.optionTitle}>{p.title}</div>
                <div className={styles.optionMeta}>
                  <span>{p.external_product_id}</span>
                  <span>
                    {Number(p.price).toLocaleString("ru")} ₽
                  </span>
                  <span className={p.stock === 0 ? styles.outOfStock : undefined}>
                    {p.stock === 0 ? "Нет в наличии" : `${p.stock} шт.`}
                  </span>
                </div>
              </div>
              {p.has_variations && p.variations.length > 0 && (
                <span className={styles.variantsBadge}>
                  +{p.variations.length} вар.
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {outOfStockCount > 0 && (
        <div className={styles.outOfStockWarning}>
          ⚠ {outOfStockCount} из выбранных товаров отсутствуют на складе и будут
          исключены из активных объявлений
        </div>
      )}
    </div>
  );
}
