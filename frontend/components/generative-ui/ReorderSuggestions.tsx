import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ReorderItem {
  product_id: number;
  product_name: string;
  last_qty: number;
  last_price: number;
  last_order_date: string;
  image_url: string;
}

interface ReorderSuggestionsProps {
  data: Record<string, unknown>;
}

export function ReorderSuggestions({ data }: ReorderSuggestionsProps) {
  const items = (data.items as ReorderItem[]) || [];
  const customerName = data.customer_name as string;

  if (items.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Saran Reorder untuk {customerName}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.product_id} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-muted rounded flex items-center justify-center text-lg">👕</div>
                <div>
                  <p className="text-sm font-medium">{item.product_name}</p>
                  <p className="text-xs text-muted-foreground">
                    Terakhir: {item.last_qty} pcs @ Rp {item.last_price.toLocaleString("id-ID")}
                  </p>
                </div>
              </div>
              <Button size="sm" variant="outline">Pesan Ulang</Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
