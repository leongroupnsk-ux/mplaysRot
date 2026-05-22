export interface PlanFeature {
  label: string;
  value: string;
  available: boolean;
}

export interface Plan {
  id: string;
  name: string;
  price: number | null;
  priceLabel: string;
  period: string;
  description: string;
  highlighted: boolean;
  badge?: string;
  features: PlanFeature[];
  cta: string;
}

/** Plans shown as full cards on the landing (Free / Start / Business only). */
export const LANDING_PLANS: Plan[] = [
  {
    id: "free",
    name: "Free",
    price: 0,
    priceLabel: "0 ₽",
    period: "/мес",
    description: "Первое знакомство с платформой",
    highlighted: false,
    cta: "Начать бесплатно",
    features: [
      { label: "Магазины WB / Ozon", value: "1", available: true },
      { label: "Магазины Яндекс.Маркет", value: "1", available: true },
      { label: "Переходов / мес", value: "500", available: true },
      { label: "Рекламные кабинеты", value: "1 (Яндекс.Директ)", available: true },
      { label: "Модель атрибуции WB", value: "—", available: false },
      { label: "Look-alike аудитории", value: "—", available: false },
      { label: "Logistics Tracker", value: "—", available: false },
      { label: "ИИ-ассистент", value: "—", available: false },
    ],
  },
  {
    id: "start",
    name: "Start",
    price: 7190,
    priceLabel: "7 190 ₽",
    period: "/мес",
    description: "Для растущих магазинов",
    highlighted: false,
    cta: "Оформить подписку",
    features: [
      { label: "Магазины WB / Ozon", value: "2", available: true },
      { label: "Магазины Яндекс.Маркет", value: "1", available: true },
      { label: "Переходов / мес", value: "5 000", available: true },
      { label: "Рекламные кабинеты", value: "3", available: true },
      { label: "Модель атрибуции WB", value: "Базовая", available: true },
      { label: "Look-alike аудитории", value: "—", available: false },
      { label: "Logistics Tracker", value: "—", available: false },
      { label: "ИИ-ассистент", value: "—", available: false },
    ],
  },
  {
    id: "business",
    name: "Business",
    price: 19190,
    priceLabel: "19 190 ₽",
    period: "/мес",
    description: "Для зрелых команд",
    highlighted: true,
    badge: "Популярный",
    cta: "Оформить подписку",
    features: [
      { label: "Магазины WB / Ozon", value: "10", available: true },
      { label: "Магазины Яндекс.Маркет", value: "3", available: true },
      { label: "Переходов / мес", value: "50 000", available: true },
      { label: "Рекламные кабинеты", value: "Все", available: true },
      { label: "Модель атрибуции WB", value: "Продвинутая (ML)", available: true },
      { label: "Look-alike аудитории", value: "✓", available: true },
      { label: "Logistics Tracker", value: "Полный", available: true },
      { label: "ИИ-ассистент", value: "50 запросов/мес", available: true },
    ],
  },
];

export const PLANS: Plan[] = [
  ...LANDING_PLANS,
  {
    id: "enterprise",
    name: "Enterprise",
    price: null,
    priceLabel: "от 47 990 ₽",
    period: "/мес",
    description: "Для крупного бизнеса",
    highlighted: false,
    cta: "Связаться с нами",
    features: [
      { label: "Магазины WB / Ozon", value: "Без ограничений", available: true },
      { label: "Магазины Яндекс.Маркет", value: "Без ограничений", available: true },
      { label: "Переходов / мес", value: "Без ограничений", available: true },
      { label: "Рекламные кабинеты", value: "Все", available: true },
      { label: "Модель атрибуции WB", value: "ML + ручная верификация", available: true },
      { label: "Look-alike аудитории", value: "✓ + автоактивация", available: true },
      { label: "Logistics Tracker", value: "Полный + ИИ-рекомендации", available: true },
      { label: "ИИ-ассистент", value: "Без ограничений", available: true },
    ],
  },
];

export const LOGISTICS_TRACKER_MONTHLY = 3290;
export const LOGISTICS_TRACKER_YEARLY = 31000;
export const EXTRA_STORE_PRICE = 2390;
export const AMAZON_ANALYTICS_PRICE = 7190;
export const ANNUAL_DISCOUNT = 0.20;
