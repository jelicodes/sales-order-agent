import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ProductCard {
  product_id: string;
  name: string;
  category: string;
  price: number;
  moq: number;
  stock: number;
  image_url: string;
  description: string;
}

interface ProductCardsProps {
  data: {
    data: ProductCard[];
  };
}

export function ProductCards({ data }: ProductCardsProps) {
  const products = data.data || [];

  if (products.length === 0) {
    return (
      <Card size="sm">
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">
            Tidak ada produk yang ditemukan.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      {products.map((product) => (
        <Card key={product.product_id} size="sm" className="overflow-hidden">
          {product.image_url && (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-32 object-cover"
            />
          )}
          <CardHeader>
            <div className="flex items-start justify-between gap-2">
              <CardTitle className="text-sm">{product.name}</CardTitle>
              {product.stock < 10 && (
                <Badge variant="destructive" className="shrink-0">
                  Stok Terbatas
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-xs text-muted-foreground line-clamp-2">
              {product.description}
            </p>
            <div className="space-y-1">
              <p className="text-sm font-semibold">
                Rp {product.price.toLocaleString("id-ID")}
              </p>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>MOQ: {product.moq}</span>
                <span>Stok: {product.stock}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
