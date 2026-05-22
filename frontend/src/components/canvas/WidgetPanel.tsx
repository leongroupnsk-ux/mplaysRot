import type { WidgetType } from "../../api/canvas";
import { DEFAULT_SIZES } from "./InfiniteCanvas";
import css from "./WidgetPanel.module.css";

interface WidgetDef {
  type: WidgetType;
  icon: string;
  name: string;
  desc: string;
  defaultData?: Record<string, any>;
  defaultStyle?: Record<string, any>;
}

const DATA_WIDGETS: WidgetDef[] = [
  {
    type: "product_card",
    icon: "🛍",
    name: "Карточка товара",
    desc: "Продажи, остатки, цена, маржа",
  },
  {
    type: "logistics",
    icon: "📦",
    name: "Логистика",
    desc: "Остатки по складам, дни запаса",
  },
  {
    type: "ad_connector",
    icon: "📢",
    name: "Рекламный коннектор",
    desc: "ROMI, CPC, расход кампании",
  },
  {
    type: "mini_chart",
    icon: "📈",
    name: "График",
    desc: "Продажи, ROMI, возвраты",
    defaultData: { metric: "sales", period: "7d" },
  },
];

const NOTE_WIDGETS: WidgetDef[] = [
  {
    type: "sticker",
    icon: "📝",
    name: "Стикер",
    desc: "Цветная заметка с текстом",
    defaultData: { content: "", color: "#FFF3D6" },
  },
  {
    type: "text",
    icon: "✏️",
    name: "Текстовый блок",
    desc: "Свободный текст, Markdown",
    defaultData: { content: "", color: "#ffffff" },
  },
  {
    type: "kpi_table",
    icon: "📊",
    name: "Таблица KPI",
    desc: "Сводные метрики по товарам",
  },
];

interface Props {
  onAddWidget: (
    type: WidgetType,
    size: { w: number; h: number },
    data?: Record<string, any>,
    style?: Record<string, any>
  ) => void;
}

export default function WidgetPanel({ onAddWidget }: Props) {
  const renderItem = (w: WidgetDef) => {
    const size = DEFAULT_SIZES[w.type] ?? { w: 300, h: 200 };
    return (
      <div
        key={w.type}
        className={css.widgetItem}
        onClick={() => onAddWidget(w.type, size, w.defaultData, w.defaultStyle)}
        title={`Добавить: ${w.name}`}
      >
        <div className={css.widgetIcon}>{w.icon}</div>
        <div className={css.widgetInfo}>
          <div className={css.widgetName}>{w.name}</div>
          <div className={css.widgetDesc}>{w.desc}</div>
        </div>
      </div>
    );
  };

  return (
    <div className={css.panel}>
      <div className={css.panelHeader}>Виджеты</div>

      <div className={css.section}>
        <div className={css.sectionLabel}>Данные в реальном времени</div>
        {DATA_WIDGETS.map(renderItem)}
      </div>

      <div className={css.divider} />

      <div className={css.section}>
        <div className={css.sectionLabel}>Заметки и контент</div>
        {NOTE_WIDGETS.map(renderItem)}
      </div>

      <div className={css.tip}>
        💡 Нажмите на виджет, чтобы добавить его в центр холста. Перетаскивайте за заголовок.
      </div>
    </div>
  );
}
