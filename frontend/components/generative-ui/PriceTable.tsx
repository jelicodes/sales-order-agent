import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface PriceTier {
  min_qty: number;
  max_qty: number;
  price_per_unit: number;
}

interface PriceTableProps {
  data: {
    tiers: PriceTier[];
    product_name: string;
    quantity: number;
    total: number;
  };
}

export function PriceTable({ data }: PriceTableProps) {
  const { tiers, product_name, quantity, total } = data;

  if (!tiers || tiers.length === 0) {
    return (
      <Card size="sm">
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">
            Tidak ada informasi harga tersedia.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="text-sm">Rincian Harga: {product_name}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Jumlah</TableHead>
              <TableHead className="text-right">Harga/pcs</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tiers.map((tier, index) => {
              const isSelected =
                quantity >= tier.min_qty &&
                (tier.max_qty === null || quantity <= tier.max_qty);
              return (
                <TableRow
                  key={index}
                  className={isSelected ? "bg-muted font-medium" : ""}
                >
                  <TableCell>
                    {tier.max_qty
                      ? `${tier.min_qty} - ${tier.max_qty}`
                      : `≥ ${tier.min_qty}`}
                  </TableCell>
                  <TableCell className="text-right">
                    Rp {tier.price_per_unit.toLocaleString("id-ID")}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
        {quantity > 0 && (
          <div className="mt-3 flex justify-between border-t pt-3 text-sm font-medium">
            <span>Total ({quantity} pcs)</span>
            <span>Rp {total.toLocaleString("id-ID")}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
