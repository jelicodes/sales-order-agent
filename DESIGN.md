# DESIGN.md — Style Guide for Generative UI Frontend

> Referensi desain untuk implementasi frontend Next.js + shadcn/ui
> Berdasarkan riset web design patterns untuk B2B wholesale fashion platform

---

## 1. Color Palette

### Primary Colors

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Primary** | Deep Navy | `#1B2A4A` | Headers, primary buttons, brand anchor |
| **Primary Light** | Slate Blue | `#3B5998` | Hover states, secondary actions |
| **Accent** | Warm Gold | `#C9A84C` | CTAs, badges, premium indicators |
| **Accent Light** | Soft Gold | `#E8D5A3` | Hover states, backgrounds |

### Status Colors

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Success** | Emerald | `#10B981` | Stock available, order confirmed |
| **Warning** | Amber | `#F59E0B` | Low stock, pending status |
| **Error** | Rose | `#EF4444` | Out of stock, errors |
| **Info** | Sky Blue | `#3B82F6` | Informational messages |

### Neutral (Light Mode)

| Role | Color | Hex |
|------|-------|-----|
| Background | White | `#FFFFFF` |
| Surface | Soft Gray | `#F8FAFC` |
| Surface Alt | Light Gray | `#F1F5F9` |
| Border | Medium Gray | `#E2E8F0` |
| Text Primary | Charcoal | `#1E293B` |
| Text Secondary | Slate | `#64748B` |

### Neutral (Dark Mode)

| Role | Color | Hex |
|------|-------|-----|
| Background | Deep Dark | `#0F172A` |
| Surface | Dark Slate | `#1E293B` |
| Surface Alt | Slate | `#334155` |
| Border | Dim Gray | `#475569` |
| Text Primary | Off White | `#F1F5F9` |
| Text Secondary | Light Gray | `#CBD5E1` |

### Rules
- **60-30-10**: 60% neutral, 30% surfaces, 10% accent
- **Never use pure black** (`#000000`) for backgrounds
- **Never use pure white** (`#FFFFFF`) for text in dark mode
- **WCAG 2.1 AA**: 4.5:1 contrast ratio for text

---

## 2. Typography

### Font Stack

| Role | Font | Weight | Usage |
|------|------|--------|-------|
| **Headings** | Inter | 600-700 | H1-H6, card titles |
| **Body** | Inter | 400-500 | Paragraphs, descriptions |
| **Display** | Playfair Display | 700 | Hero sections, branding |
| **Monospace** | JetBrains Mono | 400 | Code, SKU numbers |

### Type Scale

| Token | Size | Line Height | Usage |
|-------|------|-------------|-------|
| `text-xs` | 12px | 1rem | Captions |
| `text-sm` | 14px | 1.25rem | Labels |
| `text-base` | 16px | 1.5rem | Body |
| `text-lg` | 18px | 1.75rem | Lead |
| `text-xl` | 20px | 1.75rem | Card titles |
| `text-2xl` | 24px | 2rem | Section headings |
| `text-3xl` | 30px | 2.25rem | Page titles |
| `text-4xl` | 36px | 2.5rem | Hero text |

### Rules
- Max 2 font families (Inter + Playfair Display)
- Line height 1.5 for body, 1.2-1.3 for headings
- Letter spacing `-0.02em` for headings
- Use `tabular-nums` for price alignment

---

## 3. Spacing & Sizing

### Spacing Scale (8px Grid)

| Token | Value | Usage |
|-------|-------|-------|
| `gap-1` | 4px | Icon to text |
| `gap-2` | 8px | Inner padding |
| `gap-3` | 12px | Compact card |
| `gap-4` | 16px | Standard card |
| `gap-6` | 24px | Card grid gap |
| `gap-8` | 32px | Section spacing |
| `gap-12` | 48px | Page sections |

### Layout Dimensions

| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| Max content | 1280px | 100% | 100% |
| Chat panel | 480px fixed | 100% (stack) | 100% (stack) |
| Catalog panel | flex-1 | 100% | 100% |
| Header height | 64px | 64px | 56px |
| Product card min | 280px | 240px | 100% |
| Grid columns | 3-4 | 2-3 | 1-2 |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-sm` | 4px | Badges |
| `rounded-md` | 6px | Buttons, inputs |
| `rounded-lg` | 8px | Cards, dialogs |
| `rounded-xl` | 12px | Feature cards |
| `rounded-full` | 9999px | Avatars, pills |

---

## 4. Split View Layout

### Structure

```
┌──────────────────────────────────────────────────────────────┐
│ Header (64px) — Logo | Navigation | Search | Theme Toggle   │
├──────────────────────────────┬───────────────────────────────┤
│ Catalog Panel (flex-1)       │ Chat Panel (480px fixed)     │
│                              │                               │
│ [Category Tabs]              │ [Chat Header]                 │
│ [Product Grid]               │ [Message List]                │
│                              │   - Text bubbles              │
│                              │   - ProductCard               │
│                              │   - PriceTable                │
│                              │   - OrderSummary              │
│                              │ [Input Area]                  │
└──────────────────────────────┴───────────────────────────────┘
```

### Responsive Breakpoints

| Breakpoint | Layout | Behavior |
|------------|--------|----------|
| `≥1024px` | Side-by-side | Catalog + Chat (480px) |
| `768px-1023px` | Tabbed | Toggle between views |
| `<768px` | Stacked | Full-width with bottom tabs |

### CSS Implementation

```css
.split-view {
  display: flex;
  height: calc(100vh - 64px);
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
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.chat-input {
  border-top: 1px solid var(--border);
  padding: 16px;
  position: sticky;
  bottom: 0;
}
```

---

## 5. Chat Interface

### Message Types

| Type | Alignment | Styling |
|------|-----------|---------|
| User message | Right | `bg-primary text-primary-foreground rounded-2xl rounded-br-sm` |
| Agent text | Left | `bg-muted rounded-2xl rounded-bl-sm` |
| Product Card | Left | Inline rich component |
| Price Table | Left | Structured table |
| Order Summary | Left | Confirmation card |

### Chat Bubble Code

```tsx
// User
<div className="flex justify-end mb-4">
  <div className="bg-primary text-primary-foreground rounded-2xl rounded-br-sm px-4 py-2 max-w-[80%]">
    {message}
  </div>
</div>

// Agent
<div className="flex justify-start mb-4">
  <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-2 max-w-[80%]">
    {message}
  </div>
</div>
```

### Input Area

```tsx
<div className="border-t bg-background p-4">
  <div className="flex items-end gap-2">
    <Textarea placeholder="Ketik pesan Anda..." className="min-h-[44px] max-h-[120px] resize-none" rows={1} />
    <Button size="icon" className="h-[44px] w-[44px] shrink-0">
      <SendIcon className="h-4 w-4" />
    </Button>
  </div>
  <p className="text-xs text-muted-foreground mt-2">Enter untuk mengirim</p>
</div>
```

---

## 6. Generative UI Components

### ProductCard

```tsx
<Card className="overflow-hidden">
  <div className="aspect-square relative">
    <Image src={product.image} alt={product.name} fill className="object-cover" />
    {product.stock < 10 && (
      <Badge variant="destructive" className="absolute top-2 right-2">Stok Terbatas</Badge>
    )}
  </div>
  <CardHeader className="p-4">
    <CardTitle className="text-sm line-clamp-2">{product.name}</CardTitle>
  </CardHeader>
  <CardContent className="p-4 pt-0">
    <div className="flex items-baseline gap-1">
      <span className="text-lg font-bold text-primary">
        Rp {product.price.toLocaleString("id-ID")}
      </span>
      <span className="text-xs text-muted-foreground">/pcs</span>
    </div>
    <p className="text-xs text-muted-foreground mt-2">
      MOQ: {product.moq} | Stok: {product.stock}
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
        </TableRow>
      </TableHeader>
      <TableBody>
        {tiers.map((tier, i) => (
          <TableRow key={i} className={selected ? "bg-primary/5" : ""}>
            <TableCell>{tier.minQty} - {tier.maxQty ?? "∞"} pcs</TableCell>
            <TableCell className="text-right font-medium">
              Rp {tier.unitPrice.toLocaleString("id-ID")}
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
<Card>
  <CardHeader>
    <div className="flex items-center justify-between">
      <CardTitle className="text-sm">Ringkasan Pesanan</CardTitle>
      <Badge variant={status === "confirmed" ? "success" : "warning"}>
        {statusLabels[status]}
      </Badge>
    </div>
    <CardDescription>#{orderId}</CardDescription>
  </CardHeader>
  <CardContent>
    <div className="space-y-2">
      {items.map((item, i) => (
        <div key={i} className="flex justify-between text-sm">
          <span className="text-muted-foreground">{item.name} x{item.qty}</span>
          <span>Rp {item.subtotal.toLocaleString("id-ID")}</span>
        </div>
      ))}
      <Separator />
      <div className="flex justify-between font-medium">
        <span>Total</span>
        <span className="text-primary">Rp {total.toLocaleString("id-ID")}</span>
      </div>
    </div>
  </CardContent>
  <CardFooter className="gap-2">
    <Button className="flex-1">Konfirmasi Pesanan</Button>
    <Button variant="outline">Ubah</Button>
  </CardFooter>
</Card>
```

---

## 7. Component Organization

```
components/
├── ui/                    # shadcn primitives
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   ├── table.tsx
│   └── badge.tsx
├── chat/                  # Chat-specific
│   ├── ChatPanel.tsx
│   ├── ChatBubble.tsx
│   ├── ChatInput.tsx
│   └── ComponentRenderer.tsx
├── generative-ui/         # Rich components
│   ├── ProductCard.tsx
│   ├── ProductCarousel.tsx
│   ├── PriceTable.tsx
│   ├── OrderSummary.tsx
│   └── ReorderSuggestions.tsx
├── catalog/               # Product catalog
│   ├── ProductGrid.tsx
│   └── ProductFilters.tsx
└── layout/                # Layout
    ├── Header.tsx
    └── SplitView.tsx
```

---

## 8. Dark Mode

### Implementation

```tsx
// app/layout.tsx
<ThemeProvider attribute="class" defaultTheme="system" enableSystem>
  {children}
</ThemeProvider>

// ThemeToggle component
export function ThemeToggle() {
  const { setTheme, theme } = useTheme();
  return (
    <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
```

### Considerations
- Product images need subtle borders in dark mode
- Test color contrast in both modes
- Use CSS variables for all colors

---

## 9. Quick Reference

### shadcn/ui Patterns
- Use `cn()` for class merging
- Import from `@/components/ui/`
- CSS variables for theming
- Never hardcode colors

### Price Formatting
```tsx
Rp {price.toLocaleString("id-ID")}  // → Rp 85.000
```

### Touch Targets
- Minimum 44px x 44px for mobile

### Font Loading
```tsx
// app/layout.tsx
import { Inter, Playfair_Display } from "next/font/google";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-display" });
```
