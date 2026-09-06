"use client";
import { useState } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface SplitViewProps {
  catalog: React.ReactNode;
  chat: React.ReactNode;
}

export function SplitView({ catalog, chat }: SplitViewProps) {
  const [activeTab, setActiveTab] = useState<"catalog" | "chat">("chat");

  return (
    <>
      <div className="hidden lg:flex h-[calc(100vh-64px)] min-h-0">
        <div className="flex-1 min-h-0 overflow-y-auto p-6">{catalog}</div>
        <div className="w-[480px] min-w-[360px] max-w-[560px] border-l flex flex-col min-h-0 overflow-hidden">
          {chat}
        </div>
      </div>
      <div className="lg:hidden h-[calc(100vh-64px)] min-h-0 flex flex-col">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "catalog" | "chat")}>
          <TabsList className="mx-4 mt-2">
            <TabsTrigger value="catalog" className="flex-1">Katalog</TabsTrigger>
            <TabsTrigger value="chat" className="flex-1">Chat</TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="flex-1 min-h-0 overflow-y-auto">
          {activeTab === "catalog" ? catalog : chat}
        </div>
      </div>
    </>
  );
}