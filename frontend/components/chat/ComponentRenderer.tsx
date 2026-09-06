import { ProductCards } from "@/components/generative-ui/ProductCards";
import { PriceTable } from "@/components/generative-ui/PriceTable";
import { OrderSummary } from "@/components/generative-ui/OrderSummary";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ComponentRendererProps {
  type: string;
  data: Record<string, unknown>;
}

export function ComponentRenderer({ type, data }: ComponentRendererProps) {
  switch (type) {
    case "product_cards":
      return <ProductCards data={data as unknown as { data: Array<{ product_id: string; name: string; category: string; price: number; moq: number; stock: number; image_url: string; description: string }> }} />;
    case "price_breakdown":
      return <PriceTable data={data as unknown as { tiers: Array<{ min_qty: number; max_qty: number; price_per_unit: number }>; product_name: string; quantity: number; total: number }} />;
    case "order_summary":
      return <OrderSummary data={data as unknown as { items: Array<{ product_id: string; product_name: string; qty: number; price_per_unit: number; subtotal: number }>; status: "pending" | "confirmed" | "processing" | "shipped" | "delivered"; order_id: string; total_price: number }} />;
    case "reorder_suggestions":
      return <ReorderSuggestions data={data} />;
    default:
      return null;
  }
}

function ReorderSuggestions({ data }: { data: Record<string, unknown> }) {
  const suggestions = (data.suggestions as Array<Record<string, unknown>>) || [];

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="text-sm">Saran Pemesanan Ulang</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-1 text-sm">
          {suggestions.map((item, i) => (
            <li key={i} className="flex justify-between">
              <span className="text-muted-foreground">
                {String(item.name || "")}
              </span>
              <span>{String(item.reason || "")}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
