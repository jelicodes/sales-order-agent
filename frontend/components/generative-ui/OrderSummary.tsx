import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface OrderItem {
  product_id: string;
  product_name: string;
  qty: number;
  price_per_unit: number;
  subtotal: number;
}

type OrderStatus = "pending" | "confirmed" | "processing" | "shipped" | "delivered";

interface OrderSummaryProps {
  data: {
    items: OrderItem[];
    status: OrderStatus;
    order_id: string;
    total_price: number;
  };
  onConfirm?: () => void;
  onEdit?: () => void;
}

const statusConfig: Record<OrderStatus, { label: string; variant: "default" | "secondary" | "outline" | "destructive" }> = {
  pending: { label: "Menunggu", variant: "secondary" },
  confirmed: { label: "Dikonfirmasi", variant: "default" },
  processing: { label: "Diproses", variant: "default" },
  shipped: { label: "Dikirim", variant: "outline" },
  delivered: { label: "Selesai", variant: "default" },
};

export function OrderSummary({ data, onConfirm, onEdit }: OrderSummaryProps) {
  const { items, status, order_id, total_price } = data;

  if (!items || items.length === 0) {
    return (
      <Card size="sm">
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">
            Tidak ada item dalam pesanan.
          </p>
        </CardContent>
      </Card>
    );
  }

  const statusInfo = statusConfig[status] || statusConfig.pending;

  return (
    <Card size="sm">
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-sm">Ringkasan Pesanan</CardTitle>
          <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
        </div>
        <p className="text-xs text-muted-foreground">ID: {order_id}</p>
      </CardHeader>
      <CardContent className="space-y-3">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Produk</TableHead>
              <TableHead className="text-right">Qty</TableHead>
              <TableHead className="text-right">Harga</TableHead>
              <TableHead className="text-right">Subtotal</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.product_id}>
                <TableCell className="font-medium">{item.product_name}</TableCell>
                <TableCell className="text-right">{item.qty}</TableCell>
                <TableCell className="text-right">
                  Rp {item.price_per_unit.toLocaleString("id-ID")}
                </TableCell>
                <TableCell className="text-right">
                  Rp {item.subtotal.toLocaleString("id-ID")}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <div className="flex justify-between border-t pt-3 text-sm font-semibold">
          <span>Total</span>
          <span>Rp {total_price.toLocaleString("id-ID")}</span>
        </div>

        <div className="flex gap-2 pt-2">
          <Button variant="outline" size="sm" className="flex-1" onClick={onEdit}>
            Edit
          </Button>
          <Button variant="default" size="sm" className="flex-1" onClick={onConfirm}>
            Konfirmasi
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
