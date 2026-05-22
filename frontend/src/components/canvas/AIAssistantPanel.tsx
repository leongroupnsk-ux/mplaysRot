import { useState, useRef, useEffect } from "react";
import { sendAICommand } from "../../api/canvas";
import type { WidgetType } from "../../api/canvas";
import { DEFAULT_SIZES } from "./InfiniteCanvas";
import css from "./AIAssistantPanel.module.css";

interface Message {
  id: string;
  role: "ai" | "user";
  text: string;
  actions?: Array<{ type: string; widget_type?: WidgetType; label?: string }>;
}

const SUGGESTIONS = [
  "Добавь стикер с заметкой",
  "Добавь карточку товара",
  "Покажи логистику склада",
  "Добавь график продаж",
  "Добавь рекламный коннектор",
  "Как соединить виджеты?",
];

const WELCOME: Message = {
  id: "welcome",
  role: "ai",
  text: "Привет! Я AI-ассистент MPlays Canvas. Скажи мне, что добавить на холст — виджет товара, график, стикер, логистику или рекламу. Или задай вопрос о работе с канвасом.",
};

interface Props {
  boardId: string;
  onAddWidget: (
    type: WidgetType,
    size: { w: number; h: number },
    x: number,
    y: number,
    data?: Record<string, any>
  ) => void;
}

export default function AIAssistantPanel({ boardId, onAddWidget }: Props) {
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg: Message = { id: Date.now().toString(), role: "user", text: text.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendAICommand(boardId, text.trim());
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "ai",
        text: res.message,
        actions: res.actions,
      };
      setMessages((m) => [...m, aiMsg]);

      // Execute add_widget actions
      for (const action of res.actions) {
        if (action.type === "add_widget") {
          const wt = action.widget_type as WidgetType;
          const size = DEFAULT_SIZES[wt] ?? { w: 300, h: 200 };
          // Place near center of canvas (rough estimate)
          onAddWidget(wt, size, action.x ?? 200, action.y ?? 200, action.data);
        }
      }
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: (Date.now() + 1).toString(),
          role: "ai",
          text: "Произошла ошибка. Попробуй ещё раз.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={css.panel}>
      {/* Header */}
      <div className={css.header}>
        <div className={css.headerIcon}>🤖</div>
        <div className={css.headerInfo}>
          <div className={css.headerTitle}>AI-ассистент</div>
          <div className={css.headerSub}>Canvas Sidekick</div>
        </div>
      </div>

      {/* Messages */}
      <div className={css.messages}>
        {messages.map((msg) =>
          msg.role === "ai" ? (
            <div key={msg.id} className={css.msgAI}>
              <div className={css.msgAvatar}>🤖</div>
              <div>
                <div className={css.msgBubble}>{msg.text}</div>
                {msg.actions && msg.actions.length > 0 && (
                  <div className={css.msgActions}>
                    {msg.actions.map((a, i) => (
                      <span key={i} className={css.actionChip}>
                        {a.type === "add_widget" ? `✓ Добавлен ${a.widget_type}` : a.type}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div key={msg.id} className={css.msgUser}>
              <div className={css.msgUserBubble}>{msg.text}</div>
            </div>
          )
        )}
        {loading && (
          <div className={css.msgAI}>
            <div className={css.msgAvatar}>🤖</div>
            <div className={css.msgBubble} style={{ color: "#94a3b8" }}>
              Думаю…
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      <div className={css.suggestions}>
        <div className={css.suggLabel}>Примеры команд</div>
        {SUGGESTIONS.slice(0, 3).map((s) => (
          <button key={s} className={css.sugg} onClick={() => send(s)}>
            {s}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className={css.inputRow}>
        <textarea
          className={css.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          placeholder="Напишите команду… (Enter для отправки)"
          rows={2}
        />
        <button
          className={css.sendBtn}
          disabled={!input.trim() || loading}
          onClick={() => send(input)}
        >
          ↑
        </button>
      </div>
    </div>
  );
}
