import { Header } from "@/components/layout/Header";
import { SplitView } from "@/components/layout/SplitView";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { ProductGrid } from "@/components/catalog/ProductGrid";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <SplitView
        catalog={<ProductGrid />}
        chat={<ChatPanel />}
      />
    </div>
  );
}
