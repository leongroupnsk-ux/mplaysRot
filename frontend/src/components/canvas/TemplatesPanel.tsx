import { useQuery } from "@tanstack/react-query";
import { listTemplates, type BoardTemplate } from "../../api/canvas";
import css from "./TemplatesPanel.module.css";

const CATEGORY_LABELS: Record<string, string> = {
  pnl_sku:          "P&L",
  brand_rollout:    "Запуск",
  traffic_analysis: "Аналитика",
  logistics:        "Логистика",
  competitor:       "Конкуренты",
  blank:            "Пустой",
};

interface Props {
  onClose: () => void;
  onSelectTemplate: (templateId: string | null, title: string) => void;
}

export default function TemplatesPanel({ onClose, onSelectTemplate }: Props) {
  const { data: templates = [], isLoading } = useQuery<BoardTemplate[]>({
    queryKey: ["canvas-templates"],
    queryFn: listTemplates,
  });

  return (
    <div className={css.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={css.modal}>
        <div className={css.header}>
          <span className={css.title}>Выберите шаблон</span>
          <button className={css.closeBtn} onClick={onClose}>×</button>
        </div>

        <div className={css.body}>
          {/* Blank board */}
          <div
            className={`${css.templateCard} ${css.blankCard}`}
            onClick={() => onSelectTemplate(null, "Новый канвас")}
          >
            <div className={css.templateEmoji}>➕</div>
            <div className={css.templateName}>Пустой холст</div>
            <div className={css.templateDesc}>Начните с чистого листа</div>
            <span className={css.templateCategory}>Пустой</span>
          </div>

          {isLoading && (
            <div style={{ gridColumn: "1/-1", textAlign: "center", color: "#94a3b8", padding: 40 }}>
              Загрузка шаблонов…
            </div>
          )}

          {templates.map((tpl) => (
            <div
              key={tpl.id}
              className={css.templateCard}
              onClick={() => onSelectTemplate(tpl.id, tpl.name)}
            >
              <div className={css.templateEmoji}>{tpl.thumbnail_emoji}</div>
              <div className={css.templateName}>{tpl.name}</div>
              <div className={css.templateDesc}>{tpl.description}</div>
              <span className={css.templateCategory}>
                {CATEGORY_LABELS[tpl.category] ?? tpl.category}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
