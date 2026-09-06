import { cn } from "cn";

interface ChatBubbleProps {
  role: "user" | "assistant";
  children: React.ReactNode;
}

export function ChatBubble({ role, children }: ChatBubbleProps) {
  return (
    <div
      className={cn(
        "flex w-full",
        role === "user" ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2 text-sm",
          role === "user"
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground"
        )}
      >
        {children}
      </div>
    </div>
  );
}
