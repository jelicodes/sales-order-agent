"use client";

import { useEffect, useState } from "react";
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

export function ProductGrid() {
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    fetch("/api/products")
      .then((res) => res.json())
      .then((data) => setProducts(data))
      .catch(() => {
        setProducts([
          { id: 1, name: "Polo Premium Cotton", category: "Polo", base_price: 85000, moq: 100, description: "Kemeja polo berbahan katun premium", image_url: "/images/products/polo-premium-cotton.svg" },
          { id: 2, name: "Polo Basic", category: "Polo", base_price: 65000, moq: 100, description: "Polo standar dengan bahan katun nyaman", image_url: "/images/products/polo-basic.svg" },
          { id: 3, name: "Kaos Polos Premium", category: "Kaos", base_price: 55000, moq: 50, description: "Kaos polos berbahan katun combed 30s", image_url: "/images/products/kaos-polos-premium.svg" },
          { id: 4, name: "Kemeja Flanel Premium", category: "Kemeja", base_price: 95000, moq: 50, description: "Kemeja flanel premium dengan motif kotak", image_url: "/images/products/kemeja-flanel-premium.svg" },
          { id: 5, name: "Hoodie Zipper Premium", category: "Hoodie", base_price: 145000, moq: 30, description: "Hoodie zipper dengan bahan fleece tebal", image_url: "/images/products/hoodie-zipper-premium.svg" },
          { id: 6, name: "Celana Chino Slim Fit", category: "Celana", base_price: 105000, moq: 50, description: "Celana chino dengan potongan slim fit", image_url: "/images/products/celana-chino-slim-fit.svg" },
        ]);
      });
  }, []);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Katalog Produk</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {products.map((product) => (
          <Card key={product.id} className="overflow-hidden hover:shadow-md transition-shadow">
            <div className="aspect-square bg-muted flex items-center justify-center overflow-hidden">
              {product.image_url ? (
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = "none";
                    target.parentElement!.innerHTML = '<span class="text-4xl">👕</span>';
                  }}
                />
              ) : (
                <span className="text-4xl">👕</span>
              )}
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