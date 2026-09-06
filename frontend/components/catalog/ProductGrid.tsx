import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Product {
  id: number;
  name: string;
  category: string;
  base_price: number;
  moq: number;
  description: string;
  image_url?: string;
}

const PLACEHOLDER_PRODUCTS: Product[] = [
  { id: 1, name: "Kemeja Flanel Premium", category: "Kemeja", base_price: 85000, moq: 12, description: "Kemeja flanel premium" },
  { id: 2, name: "Kaos Polo Sport", category: "Polo", base_price: 65000, moq: 24, description: "Kaos polo sport" },
  { id: 3, name: "Hoodie Zipper Premium", category: "Hoodie", base_price: 125000, moq: 10, description: "Hoodie zipper premium" },
  { id: 4, name: "Celana Chino Slim Fit", category: "Celana", base_price: 95000, moq: 12, description: "Celana chino slim fit" },
  { id: 5, name: "Jaket Denim Klasik", category: "Jaket", base_price: 155000, moq: 8, description: "Jaket denim klasik" },
  { id: 6, name: "Kemeja Batik Premium", category: "Kemeja", base_price: 110000, moq: 12, description: "Kemeja batik premium" },
];

export function ProductGrid() {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Katalog Produk</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {PLACEHOLDER_PRODUCTS.map((product) => (
          <Card key={product.id} className="overflow-hidden hover:shadow-md transition-shadow">
            <div className="aspect-square bg-muted flex items-center justify-center">
              <span className="text-4xl">👕</span>
            </div>
            <CardHeader className="p-4">
              <CardTitle className="text-sm">{product.name}</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="flex items-baseline gap-1">
                <span className="text-lg font-bold text-primary">
                  Rp {product.base_price.toLocaleString("id-ID")}
                </span>
                <span className="text-xs text-muted-foreground">/pcs</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">MOQ: {product.moq} pcs</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}