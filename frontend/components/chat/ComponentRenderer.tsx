import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ComponentRendererProps {
  type: string;
  data: Record<string, unknown>;
}

export function ComponentRenderer({ type, data }: ComponentRendererProps) {
  switch (type) {
    case "product_cards":
      return <ProductCards data={data} />;
    case "price_breakdown":
      return <PriceTable data={data} />;
    case "order_summary":
      return <OrderSummary data={data} />;
    case "reorder_suggestions":
      return <ReorderSuggestions data={data} />;
    default:
      return null;
  }
}

function ProductCards({ data }: { data: Record<string, unknown> }) {
  const products = (data.products as Array<Record<string, unknown>>) || [];

  return (
    <div className="flex gap-2 overflow-x-auto pb-2">
      {products.map((product, i) => (
        <Card key={i} size="sm" className="min-w-[200px] shrink-0">
          <CardHeader>
            <CardTitle className="text-sm">
              {String(product.name || "Produk")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              {String(product.description || "")}
            </p>
            {product.price != null && (
              <p className="mt-1 text-sm font-medium">
                Rp {Number(product.price).toLocaleString("id-ID")}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function PriceTable({ data }: { data: Record<string, unknown> }) {
  const items = (data.items as Array<Record<string, unknown>>) || [];
  const total = data.total as number | undefined;

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="text-sm">Rincian Harga</CardTitle>
      </CardHeader>
      <CardContent>
        <table className="w-full text-sm">
          <tbody>
            {items.map((item, i) => (
              <tr key={i} className="border-b last:border-0">
                <td className="py-1 text-muted-foreground">
                  {String(item.label || "")}
                </td>
                <td className="py-1 text-right">
                  Rp {Number(item.value || 0).toLocaleString("id-ID")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {total != null && (
          <div className="mt-2 flex justify-between border-t pt-2 font-medium">
            <span>Total</span>
            <span>Rp {total.toLocaleString("id-ID")}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function OrderSummary({ data }: { data: Record<string, unknown> }) {
  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="text-sm">Ringkasan Pesanan</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="space-y-1 text-sm">
          {Object.entries(data).map(([key, value]) => (
            <div key={key} className="flex justify-between">
              <dt className="text-muted-foreground">{key}</dt>
              <dd>{String(value)}</dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
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
