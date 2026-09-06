# Web Design Patterns for B2B Wholesale Fashion Platform

> Research compiled 2026-09-06 | Sources: web search, shadcn/ui docs, LangChain docs, B2B design studies

---

## 1. B2B Wholesale Platform UI/UX Patterns

### Common Patterns Across Major Platforms

| Pattern | Description | Examples |
|---------|-------------|----------|
| **Quick Order Form** | Bulk SKU entry with quantity fields, CSV upload | Alibaba, Shopify B2B, Tokopedia B2B |
| **Tiered Pricing Display** | Volume-based pricing tables visible on product cards | Alibaba, WizCommerce |
| **Customer-Specific Catalogs** | Personalized product views per buyer account | Shopify B2B, B2Bridge |
| **Reorder from History** | One-click reorder from past purchases | Shopify B2B, Amazon Business |
| **Request for Quote (RFQ)** | Interactive quote submission and negotiation flow | Alibaba, Global Sources |
| **MOQ Badges** | Minimum order quantity prominently displayed on cards | Alibaba, Tokopedia |
| **Stock Status Indicators** | Real-time availability badges (In Stock / Low Stock / Out) | All platforms |

### Key B2B UX Principles (2025-2026)

1. **B2C-like experience for B2B buyers** — buyers now expect consumer-grade UX
2. **Self-service tools** — quick order forms, saved carts, reorder tools reduce sales rep dependency
3. **Personalized pricing** — customer-specific and volume-based pricing displayed contextually
4. **Mobile-first** — 60%+ of B2B research happens on mobile
5. **Fast checkout** — one-click reorder, saved payment terms, streamlined flows
6. **Hybrid B2B/B2C support** — same storefront serves wholesale and retail with access control

### Indonesian Market Specifics (Tokopedia/Tokopedia B2B)

- Clean, minimalist home page with prominent search bar
- Category icons in grid layout for quick navigation
- Promotional banners with clear CTAs
- Red accent color for urgency/alerts
- Minimalist product cards with image, name, price, seller rating
- Strong seller trust indicators (years active, transaction count, rating)

---

## 2. Color Palette for Fashion B2B

### Recommended Primary Palette

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Primary** | Deep Navy | `#1B2A4A` | Headers, primary buttons, brand anchor |
| **Primary Light** | Slate Blue | `#3B5998` | Hover states, secondary actions |
| **Accent** | Warm Gold | `#C9A84C` | CTAs, badges, premium indicators |
| **Accent Light** | Soft Gold | `#E8D5A3` | Hover states, backgrounds |
| **Success** | Emerald | `#10B981` | Stock available, order confirmed |
| **Warning** | Amber | `#F59E0B` | Low stock, pending status |
| **Error** | Rose | `#EF4444` | Out of stock, errors |
| **Info** | Sky Blue | `#3B82F6` | Informational messages |

### Neutral Palette (Light Mode)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Background** | White | `#FFFFFF` | Page background |
| **Surface** | Soft Gray | `#F8FAFC` | Card backgrounds, sidebars |
| **Surface Alt** | Light Gray | `#F1F5F9` | Alternate row, hover states |
| **Border** | Medium Gray | `#E2E8F0` | Card borders, dividers |
| **Text Primary** | Charcoal | `#1E293B` | Headings, primary text |
| **Text Secondary** | Slate | `#64748B` | Descriptions, labels |
| **Text Muted** | Light Slate | `#94A3B8` | Placeholders, captions |

### Neutral Palette (Dark Mode)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Background** | Deep Dark | `#0F172A` | Page background |
| **Surface** | Dark Slate | `#1E293B` | Card backgrounds |
| **Surface Alt** | Slate | `#334155` | Alternate row, hover |
| **Border** | Dim Gray | `#475569` | Card borders, dividers |
| **Text Primary** | Off White | `#F1F5F9` | Headings, primary text |
| **Text Secondary** | Light Gray | `#CBD5E1` | Descriptions, labels |
| **Text Muted** | Muted Gray | `#94A3B8` | Placeholders, captions |

### Color Application Rules

- **60-30-10 Rule**: 60% neutral background, 30% secondary surfaces, 10% accent
- **WCAG 2.1 AA compliance**: 4.5:1 contrast ratio for text, 3:1 for large text
- **Fashion accent**: Gold tones convey premium wholesale value
- **Never use pure black** (`#000000`) for backgrounds — use `#0F172A` or `#1E293B`
- **Never use pure white** (`#FFFFFF`) for text in dark mode — use `#F1F5F9`

### CSS Variables Implementation

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;      /* Deep Navy */
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --accent: 43 74% 55%;               /* Warm Gold */
  --accent-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 222.2 84% 4.9%;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;
  --primary: 210 40% 98%;
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  --accent: 43 74% 55%;
  --accent-foreground: 210 40% 98%;
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 212.7 26.8% 83.9%;
}
```

---

## 3. Typography Recommendations

### Primary Font Stack

| Role | Font | Fallback | Weight | Usage |
|------|------|----------|--------|-------|
| **Headings** | Inter | system-ui, sans-serif | 600-700 | H1-H6, card titles |
| **Body** | Inter | system-ui, sans-serif | 400-500 | Paragraphs, descriptions |
| **Monospace** | JetBrains Mono | monospace | 400 | Code, SKU numbers, prices |
| **Display** | Playfair Display | serif | 700 | Hero sections, fashion branding |

### Why Inter?

- Designed for screens, excellent legibility at all sizes
- Variable font support (one file, all weights)
- Tabular numbers for price alignment
- Free, open-source, Google Fonts
- Used by: Vercel, shadcn/ui default, GitHub

### Type Scale (Tailwind)

```css
--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', monospace;
--font-display: 'Playfair Display', serif;
```

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `text-xs` | 0.75rem / 12px | 1rem | 400 | Captions, fine print |
| `text-sm` | 0.875rem / 14px | 1.25rem | 400 | Labels, metadata |
| `text-base` | 1rem / 16px | 1.5rem | 400 | Body text |
| `text-lg` | 1.125rem / 18px | 1.75rem | 400 | Lead paragraphs |
| `text-xl` | 1.25rem / 20px | 1.75rem | 500 | Card titles |
| `text-2xl` | 1.5rem / 24px | 2rem | 600 | Section headings |
| `text-3xl` | 1.875rem / 30px | 2.25rem | 600 | Page titles |
| `text-4xl` | 2.25rem / 36px | 2.5rem | 700 | Hero text |

### Typography Rules

- **Maximum 2 font families** per project (Inter + Playfair Display)
- **Line height 1.5** for body text, **1.2-1.3** for headings
- **Letter spacing**: `-0.02em` for headings, `0` for body
- **Price numbers**: Use tabular-nums for aligned decimals
- **Bahasa Indonesia**: Inter handles Latin characters well, ensure proper Unicode support

---

## 4. Spacing & Sizing Guidelines

### Spacing Scale (8px Grid)

| Token | Value | Usage |
|-------|-------|-------|
| `gap-1` | 4px | Tight spacing (icon to text) |
| `gap-2` | 8px | Default inner padding |
| `gap-3` | 12px | Compact card padding |
| `gap-4` | 16px | Standard card padding |
| `gap-5` | 20px | Section internal spacing |
| `gap-6` | 24px | Card gap in grid |
| `gap-8` | 32px | Section spacing |
| `gap-10` | 40px | Major section breaks |
| `gap-12` | 48px | Page section spacing |
| `gap-16` | 64px | Hero section padding |

### Layout Dimensions

| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| **Max content width** | 1280px | 100% | 100% |
| **Chat panel width** | 480px (fixed) | 100% (stack) | 100% (stack) |
| **Catalog panel width** | flex-1 (remaining) | 100% | 100% |
| **Sidebar width** | 256px (collapsible) | 0 (drawer) | 0 (drawer) |
| **Header height** | 64px | 64px | 56px |
| **Product card min** | 280px | 240px | 100% (full width) |
| **Product grid columns** | 3-4 | 2-3 | 1-2 |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-sm` | 0.25rem / 4px | Badges, small elements |
| `rounded-md` | 0.375rem / 6px | Buttons, inputs |
| `rounded-lg` | 0.5rem / 8px | Cards, dialogs |
| `rounded-xl` | 0.75rem / 12px | Feature cards, modals |
| `rounded-full` | 9999px | Avatars, pills |

---

## 5. Split View Layout Pattern

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Header (64px) — Logo, Search, User Menu            │
├──────────────────────┬──────────────────────────────┤
│                      │                              │
│   Catalog Panel      │      Chat Panel             │
│   (flex-1)           │      (480px fixed)          │
│                      │                              │
│   - Product Grid     │   - Message List            │
│   - Filters          │   - Product Cards (inline)  │
│   - Pagination       │   - Price Tables            │
│                      │   - Order Summaries         │
│                      │   - Quick Reply Buttons     │
│                      │                              │
│                      │   ┌──────────────────────┐  │
│                      │   │ Input Area           │  │
│                      │   │ (sticky bottom)      │  │
│                      │   └──────────────────────┘  │
└──────────────────────┴──────────────────────────────┘
```

### CSS Implementation

```css
.split-view {
  display: flex;
  height: calc(100vh - 64px); /* minus header */
  overflow: hidden;
}

.catalog-panel {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.chat-panel {
  width: 480px;
  min-width: 360px;
  max-width: 560px;
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: var(--background);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.chat-input {
  border-top: 1px solid var(--border);
  padding: 16px;
  background: var(--background);
}
```

### Tailwind Implementation

```tsx
<div className="flex h-[calc(100vh-64px)] overflow-hidden">
  {/* Catalog Panel */}
  <div className="flex-1 overflow-y-auto p-6">
    <ProductGrid />
  </div>

  {/* Chat Panel */}
  <div className="w-[480px] min-w-[360px] max-w-[560px] border-l flex flex-col">
    <div className="flex-1 overflow-y-auto p-4">
      <MessageList />
    </div>
    <div className="border-t p-4">
      <ChatInput />
    </div>
  </div>
</div>
```

### Responsive Breakpoints

| Breakpoint | Layout | Behavior |
|------------|--------|----------|
| `≥1024px` | Side-by-side | Catalog + Chat (480px) |
| `768px - 1023px` | Tabbed or collapsible | Toggle between views |
| `<768px` | Stacked | Full-width panels with tab navigation |

### Visual Treatment

- **Divider**: 1px solid `var(--border)` between panels
- **Panel backgrounds**: Same `var(--background)` for cohesion
- **Chat panel shadow**: Optional `shadow-lg` on left edge for depth
- **Catalog panel**: Scrollable independently, sticky filters at top
- **Chat input**: Sticky bottom, always visible

---

## 6. Chat Interface Design Patterns

### Message Types

| Type | Styling | Example |
|------|---------|---------|
| **User message** | Right-aligned, primary color bg | "Saya cari baju Muslimah ukuran L" |
| **Agent text** | Left-aligned, muted bg | "Berikut produk yang sesuai..." |
| **Product Card** | Inline rich component | Product image, name, price, stock |
| **Price Table** | Structured table in chat | Tiered pricing for different qty |
| **Order Summary** | Confirmation card | Items, totals, status |
| **Quick Reply** | Horizontal button row | [Lihat Semua] [Pesan Sekarang] |

### Rich Component Rules (from research)

1. **Keep cards compact** — tool cards sit inline with chat messages
2. **Always handle 3 states**: `running`, `finished`, `error`
3. **Show loading indicators** during streaming
4. **Validate before rendering** — check required fields exist
5. **Progressive rendering** — show fields as they arrive
6. **Text fallback** — always include plain-text fallback for rich components

### Chat Bubble Styling

```tsx
// User message
<div className="flex justify-end mb-4">
  <div className="bg-primary text-primary-foreground rounded-2xl rounded-br-sm px-4 py-2 max-w-[80%]">
    {message}
  </div>
</div>

// Agent message
<div className="flex justify-start mb-4">
  <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-2 max-w-[80%]">
    {message}
  </div>
</div>

// Agent message with rich component
<div className="flex justify-start mb-4">
  <div className="max-w-[90%]">
    <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-2 mb-2">
      {textMessage}
    </div>
    <ProductCard product={productData} />
  </div>
</div>
```

### Input Area Design

```tsx
<div className="border-t bg-background p-4">
  <div className="flex items-end gap-2">
    <div className="flex-1 relative">
      <Textarea
        placeholder="Ketik pesan Anda..."
        className="min-h-[44px] max-h-[120px] resize-none"
        rows={1}
      />
    </div>
    <Button size="icon" className="h-[44px] w-[44px] shrink-0">
      <SendIcon className="h-4 w-4" />
    </Button>
  </div>
  <p className="text-xs text-muted-foreground mt-2">
    Tekan Enter untuk mengirim, Shift+Enter untuk baris baru
  </p>
</div>
```

---

## 7. Generative UI Component Design

### ProductCard

```tsx
// Schema
interface ProductCardProps {
  type: "product_card";
  props: {
    id: string;
    name: string;
    sku: string;
    price: number;
    unit: string;
    image: string;
    stock: number;
    moq: number;
    rating?: number;
    category: string;
    colors?: string[];
    sizes?: string[];
    actions: Array<{
      label: string;
      variant: "primary" | "secondary";
      action: string;
    }>;
  };
}

// Visual Design
<Card className="overflow-hidden">
  <div className="aspect-square relative">
    <Image src={product.image} alt={product.name} fill className="object-cover" />
    {product.stock < 10 && (
      <Badge variant="destructive" className="absolute top-2 right-2">
        Stok Terbatas
      </Badge>
    )}
  </div>
  <CardHeader className="p-4">
    <CardTitle className="text-sm line-clamp-2">{product.name}</CardTitle>
    <CardDescription className="text-xs">{product.sku}</CardDescription>
  </CardHeader>
  <CardContent className="p-4 pt-0">
    <div className="flex items-baseline gap-1">
      <span className="text-lg font-bold text-primary">
        Rp {product.price.toLocaleString("id-ID")}
      </span>
      <span className="text-xs text-muted-foreground">/{product.unit}</span>
    </div>
    <div className="flex gap-1 mt-2">
      {product.colors?.map((color) => (
        <Badge key={color} variant="secondary" className="text-xs">
          {color}
        </Badge>
      ))}
    </div>
    <p className="text-xs text-muted-foreground mt-2">
      MOQ: {product.moq} pcs | Stok: {product.stock}
    </p>
  </CardContent>
  <CardFooter className="p-4 pt-0 gap-2">
    <Button size="sm" className="flex-1">Pesan</Button>
    <Button size="sm" variant="outline">Detail</Button>
  </CardFooter>
</Card>
```

### PriceTable

```tsx
// Schema
interface PriceTableProps {
  type: "price_table";
  props: {
    productName: string;
    tiers: Array<{
      minQty: number;
      maxQty: number | null;
      unitPrice: number;
      discount?: number;
    }>;
    currency: string;
  };
}

// Visual Design
<Card>
  <CardHeader>
    <CardTitle className="text-sm">Harga Grosir — {productName}</CardTitle>
  </CardHeader>
  <CardContent>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Jumlah</TableHead>
          <TableHead className="text-right">Harga/pcs</TableHead>
          <TableHead className="text-right">Diskon</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tiers.map((tier, i) => (
          <TableRow key={i} className={i === tiers.length - 1 ? "bg-primary/5" : ""}>
            <TableCell>
              {tier.minQty} - {tier.maxQty ?? "∞"} pcs
            </TableCell>
            <TableCell className="text-right font-medium">
              Rp {tier.unitPrice.toLocaleString("id-ID")}
            </TableCell>
            <TableCell className="text-right">
              {tier.discount ? (
                <Badge variant="success">-{tier.discount}%</Badge>
              ) : (
                <span className="text-muted-foreground">—</span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </CardContent>
</Card>
```

### OrderSummary

```tsx
// Schema
interface OrderSummaryProps {
  type: "order_summary";
  props: {
    orderId: string;
    items: Array<{
      name: string;
      qty: number;
      unitPrice: number;
      subtotal: number;
    }>;
    total: number;
    status: "pending" | "confirmed" | "processing" | "shipped";
    estimatedDelivery?: string;
  };
}

// Visual Design
<Card>
  <CardHeader>
    <div className="flex items-center justify-between">
      <CardTitle className="text-sm">Ringkasan Pesanan</CardTitle>
      <Badge variant={
        status === "confirmed" ? "success" :
        status === "pending" ? "warning" : "default"
      }>
        {statusLabels[status]}
      </Badge>
    </div>
    <CardDescription>#{orderId}</CardDescription>
  </CardHeader>
  <CardContent>
    <div className="space-y-2">
      {items.map((item, i) => (
        <div key={i} className="flex justify-between text-sm">
          <span className="text-muted-foreground">
            {item.name} x{item.qty}
          </span>
          <span>Rp {item.subtotal.toLocaleString("id-ID")}</span>
        </div>
      ))}
      <Separator />
      <div className="flex justify-between font-medium">
        <span>Total</span>
        <span className="text-primary">Rp {total.toLocaleString("id-ID")}</span>
      </div>
    </div>
    {estimatedDelivery && (
      <p className="text-xs text-muted-foreground mt-4">
        Estimasi pengiriman: {estimatedDelivery}
      </p>
    )}
  </CardContent>
  <CardFooter className="gap-2">
    <Button className="flex-1">Konfirmasi Pesanan</Button>
    <Button variant="outline">Ubah</Button>
  </CardFooter>
</Card>
```

### QuickReply Buttons

```tsx
// Schema
interface QuickReplyProps {
  type: "quick_reply";
  props: {
    options: Array<{
      label: string;
      value: string;
      icon?: string;
    }>;
  };
}

// Visual Design
<div className="flex flex-wrap gap-2">
  {options.map((option) => (
    <Button
      key={option.value}
      variant="outline"
      size="sm"
      className="rounded-full"
      onClick={() => handleQuickReply(option.value)}
    >
      {option.icon && <span className="mr-1">{option.icon}</span>}
      {option.label}
    </Button>
  ))}
</div>
```

---

## 8. shadcn/ui Best Practices

### Component Organization

```
components/
├── ui/                    # shadcn primitives (button, card, input)
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   └── ...
├── chat/                  # Chat-specific components
│   ├── message-list.tsx
│   ├── chat-input.tsx
│   ├── product-card.tsx
│   ├── price-table.tsx
│   └── order-summary.tsx
├── catalog/               # Catalog-specific components
│   ├── product-grid.tsx
│   ├── product-filters.tsx
│   └── product-detail.tsx
└── layout/                # Layout components
    ├── header.tsx
    ├── sidebar.tsx
    └── split-view.tsx
```

### Key Patterns

1. **Use `cn()` for class merging** — never use template literals for conditional classes
2. **Import from `@/components/ui/`** — not from `@shadcn/ui`
3. **CSS variables for theming** — never hardcode color values
4. **React Hook Form + Zod** for form validation
5. **`cva` (class-variance-authority)** for component variants
6. **Copy-paste ownership** — components live in your codebase, not a package

### Card Spacing (shadcn/ui v2+)

```tsx
// Use --card-spacing CSS variable for consistent spacing
<Card className="[--card-spacing:--spacing(6)]">
  <CardHeader>...</CardHeader>
  <CardContent>...</CardContent>
  <CardFooter>...</CardFooter>
</Card>

// Small variant uses tighter spacing
<Card size="sm">...</Card>
```

### Data Table Pattern (for order lists, stock tables)

```tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>SKU</TableHead>
      <TableHead>Nama Produk</TableHead>
      <TableHead className="text-right">Stok</TableHead>
      <TableHead className="text-right">Harga</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {products.map((product) => (
      <TableRow key={product.id}>
        <TableCell className="font-mono">{product.sku}</TableCell>
        <TableCell>{product.name}</TableCell>
        <TableCell className="text-right">{product.stock}</TableCell>
        <TableCell className="text-right">
          Rp {product.price.toLocaleString("id-ID")}
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

---

## 9. Responsive Design Patterns

### Breakpoint Strategy (Tailwind)

```css
/* Mobile-first approach */
/* sm: 640px   — Large phones */
/* md: 768px   — Tablets */
/* lg: 1024px  — Small desktops */
/* xl: 1280px  — Desktops */
/* 2xl: 1536px — Large desktops */
```

### Split View Responsive Behavior

```tsx
<div className="flex h-[calc(100vh-64px)] overflow-hidden">
  {/* Catalog Panel */}
  <div className={cn(
    "flex-1 overflow-y-auto p-4 md:p-6",
    // Mobile: full width, hidden when chat active
    "max-md:absolute max-md:inset-0 max-md:z-0",
    activeView === "chat" && "max-md:hidden"
  )}>
    <ProductGrid />
  </div>

  {/* Chat Panel */}
  <div className={cn(
    "border-l flex flex-col",
    // Desktop: fixed width sidebar
    "md:w-[480px] md:min-w-[360px] md:max-w-[560px]",
    // Mobile: full screen overlay
    "max-md:absolute max-md:inset-0 max-md:z-10",
    activeView === "catalog" && "max-md:hidden"
  )}>
    <div className="flex-1 overflow-y-auto p-4">
      <MessageList />
    </div>
    <div className="border-t p-4">
      <ChatInput />
    </div>
  </div>

  {/* Mobile Tab Bar */}
  <div className="md:hidden fixed bottom-0 inset-x-0 border-t bg-background z-20">
    <div className="flex">
      <button
        className={cn("flex-1 py-3 text-sm font-medium", activeView === "catalog" && "text-primary border-b-2")}
        onClick={() => setActiveView("catalog")}
      >
        Katalog
      </button>
      <button
        className={cn("flex-1 py-3 text-sm font-medium", activeView === "chat" && "text-primary border-b-2")}
        onClick={() => setActiveView("chat")}
      >
        Chat AI
      </button>
    </div>
  </div>
</div>
```

### Product Grid Responsive

```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
  {products.map((product) => (
    <ProductCard key={product.id} product={product} />
  ))}
</div>
```

### Mobile-First Checklist

- [ ] Touch targets minimum 44px x 44px
- [ ] Font size minimum 16px for body (prevents iOS zoom)
- [ ] No horizontal scrolling
- [ ] Thumb-friendly navigation (bottom tab bar)
- [ ] Swipe gestures for chat/catalog switching
- [ ] Bottom sheet for filters on mobile
- [ ] Fixed CTA button on mobile product views

---

## 10. Dark Mode / Light Mode

### Recommendation: Support Both

**Yes, support both.** Here's why:

| Factor | Light Mode | Dark Mode |
|--------|-----------|-----------|
| **Readability** | Better for text-heavy content | Better in low-light environments |
| **Eye strain** | Can cause fatigue in long sessions | Reduces strain for extended use |
| **Battery** | Standard consumption | Saves battery on OLED screens |
| **Perception** | Clean, trustworthy, professional | Sophisticated, modern, premium |
| **B2B context** | Default for most business apps | Preferred by technical audiences |

### Implementation Strategy

```tsx
// 1. Use next-themes for theme management
import { ThemeProvider } from "next-themes";

// app/layout.tsx
<ThemeProvider attribute="class" defaultTheme="system" enableSystem>
  {children}
</ThemeProvider>

// 2. Theme toggle component
"use client";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Sun, Moon } from "lucide-react";

export function ThemeToggle() {
  const { setTheme, theme } = useTheme();
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}

// 3. Prevent flash of wrong theme (inline in <head>)
<script dangerouslySetInnerHTML={{ __html: `
  (function() {
    var t = localStorage.getItem('theme') ||
      (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', t);
  })();
`}} />
```

### Dark Mode Considerations for B2B

1. **Product images** — ensure they have subtle borders or backgrounds to prevent blending into dark surfaces
2. **Status badges** — test color contrast in both modes
3. **Charts/graphs** — use CSS variables for chart colors that adapt to theme
4. **Email templates** — keep moderate contrast that works in both modes
5. **WCAG AA compliance** — validate both themes independently

### When to Skip Dark Mode

- Audience is dominantly non-technical and older demographics
- Brand identity is inherently light/airy
- Engineering resources are extremely limited (2-4 weeks additional work)

**For this project**: Support both modes. The B2B wholesale audience includes tech-savvy buyers who value dark mode, and shadcn/ui makes it trivial with CSS variables.

---

## 11. Component Design Specs Summary

### Component Catalog for Generative UI

| Component | Schema Type | Description |
|-----------|------------|-------------|
| `ProductCard` | `product_card` | Product with image, name, price, stock, actions |
| `ProductCarousel` | `product_carousel` | Horizontal scrollable product list |
| `PriceTable` | `price_table` | Tiered pricing table |
| `OrderSummary` | `order_summary` | Order confirmation with items and total |
| `StockStatus` | `stock_status` | Stock indicator badge |
| `QuickReply` | `quick_reply` | Button list for quick actions |
| `ComparisonTable` | `comparison_table` | Side-by-side product comparison |
| `CategoryGrid` | `category_grid` | Product category navigation |

### Validation Rules

- All schemas should be flat (max 2 levels deep)
- Required fields: `type` (string literal), `props` (object)
- Every component needs a text fallback
- Validate with Zod before rendering

```tsx
import { z } from "zod";

const ProductCardSchema = z.object({
  type: z.literal("product_card"),
  props: z.object({
    id: z.string(),
    name: z.string(),
    sku: z.string(),
    price: z.number().positive(),
    image: z.string().url(),
    stock: z.number().nonnegative(),
    moq: z.number().positive(),
  }),
});
```

---

## 12. References

### shadcn/ui & Component Libraries
- shadcn/ui docs: https://ui.shadcn.com
- shadcn/ui Card component: https://ui.shadcn.com/docs/components/card
- SERP UI E-commerce Blocks: https://blocks.serp.co/blocks/product-list
- CommerCN (shadcn e-commerce): https://commercn.com
- Shadcn Space: https://shadcnspace.com

### B2B E-commerce Design
- B2Bridge B2B Best Practices: https://b2bridge.io/blog/b2b-ecommerce-best-practices/
- Shopify B2B: https://www.shopify.com/enterprise/blog/b2b-ecommerce-best-practices
- WizCommerce B2B UX: https://wizcommerce.com/blog/b2b-ecommerce-best-practices/
- Orbix B2B Design: https://www.orbix.studio/blogs/b2b-website-design

### Generative UI & AI Chat
- LangChain Structured Output: https://docs.langchain.com/oss/python/langchain/frontend/structured-output
- LangChain Generative UI: https://docs.langchain.com/oss/python/langchain/frontend/declarative-generative-ui
- Vercel AI SDK: https://ai-sdk.dev
- CopilotKit: https://github.com/CopilotKit/CopilotKit
- Awesome Generative UI: https://github.com/narrowin/awesome-generative-ui
- Alhena Rich Product Cards: https://alhena.ai/blog/rich-product-cards-ai-chat-visual-commerce/

### Color & Typography
- E-commerce Color Palettes: https://minitoolshub.com/blog/color-palettes-ecommerce
- Fashion Color Trends 2025-2026: https://coloracci.ai/blog/fashion-color-trends-2025-2026
- Best E-commerce Fonts: https://fontalternatives.com/best-fonts-for/ecommerce/
- Typography Trends 2026: https://graphicdesignjunction.com/2026/01/2026-typography-trends/

### Responsive & Dark Mode
- Responsive Breakpoints 2025: https://dev.to/gerryleonugroho/responsive-design-breakpoints-2025-playbook-53ih
- Dark Mode B2B: https://mantasauk.com/articles/dark-mode-effect-b2b-website-conversion/
- Dark Mode UX Principles: https://www.influencers-time.com/design-dark-mode-ux-usability-principles-and-best-practices/

### Split View & Layout
- Infor Design System Split Screen: https://design.infor.com/patterns/page-layouts/split-screen/
- Split Screen Layout Guide: https://framerwebsites.com/blog/split-screen-layout-design
- Two-Panel Selector UX: https://medium.com/design-bootcamp/side-by-side-exploring-the-power-of-the-two-panel-selector-in-ux-design-5cf8b1905bae
