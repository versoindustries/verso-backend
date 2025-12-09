# Site-Specific Guides

*Source: [Google Search Central Documentation](https://developers.google.com/search/docs/specialty)*

---

## Table of Contents

1. [E-commerce SEO](#e-commerce-seo)
2. [International and Multilingual Sites](#international-and-multilingual-sites)

---

## E-commerce SEO

E-commerce sites have unique SEO challenges including product pages, category structures, and inventory changes.

### Key Challenges for E-commerce

| Challenge | Description |
|-----------|-------------|
| Large number of pages | Thousands of product pages to manage |
| Duplicate content | Same product on multiple URLs |
| Out-of-stock products | How to handle unavailable items |
| Faceted navigation | Filters creating parameter-heavy URLs |
| Product variations | Color, size, etc. creating separate URLs |
| User-generated content | Reviews, Q&A sections |

### Product Page Optimization

#### Title Tags

```html
<title>[Product Name] - [Key Feature] | [Brand]</title>
```

Example:
```html
<title>Blue Cotton T-Shirt - Organic, Women's Size S-XL | EcoWear</title>
```

#### Meta Descriptions

Include:
- Product name
- Key features/benefits
- Price (optional)
- Availability
- Call to action

```html
<meta name="description" content="Shop our organic cotton t-shirt 
in ocean blue. Available in women's S-XL. Made from 100% GOTS 
certified cotton. Free shipping on orders over $50.">
```

#### Product Structured Data

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Blue Cotton T-Shirt",
  "image": "https://example.com/photos/tshirt-blue.jpg",
  "description": "Soft organic cotton t-shirt in ocean blue",
  "brand": {
    "@type": "Brand",
    "name": "EcoWear"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/product/blue-tshirt",
    "priceCurrency": "USD",
    "price": "29.99",
    "availability": "https://schema.org/InStock",
    "priceValidUntil": "2025-12-31"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "89"
  }
}
```

### Category Page Optimization

- Use descriptive headings
- Add unique category descriptions
- Include breadcrumb navigation
- Optimize for category keywords

```html
<h1>Women's Organic Cotton T-Shirts</h1>
<p>Discover our collection of sustainably made organic cotton 
t-shirts for women. Each shirt is GOTS certified and made 
with eco-friendly dyes.</p>
```

### Handling Out-of-Stock Products

| Scenario | Recommendation |
|----------|----------------|
| Temporarily out of stock | Keep page, mark as "Out of Stock" |
| Permanently discontinued | 301 redirect to similar product |
| Seasonal products | Keep page, update availability dates |
| Category empty | Show message, link to related categories |

**Structured data for unavailable items**:
```json
"availability": "https://schema.org/OutOfStock"
```

### Faceted Navigation

Faceted navigation (filters) can create crawling issues.

**Problem URLs**:
```
/shoes?color=red&size=10&brand=nike&sort=price
/shoes?size=10&color=red&brand=nike&sort=price
```

**Solutions**:

1. **Canonical tags** - Point filter URLs to main category
```html
<link rel="canonical" href="https://example.com/shoes">
```

2. **robots.txt** - Block parameter URLs (use carefully)
```
Disallow: /*?*color=
Disallow: /*?*sort=
```

3. **noindex, follow** - Index main page, follow links
```html
<meta name="robots" content="noindex, follow">
```

4. **URL parameter handling** in Search Console

### Image Optimization for Products

- Use high-quality product images
- Multiple angles (front, back, detail)
- Alt text describing product
- Image sitemap for discovery

```html
<img src="blue-tshirt-front.jpg" 
     alt="Women's blue organic cotton t-shirt - front view">
<img src="blue-tshirt-back.jpg" 
     alt="Women's blue organic cotton t-shirt - back view">
```

### Reviews and Ratings

Implement Review structured data:

```json
{
  "@type": "Review",
  "author": {
    "@type": "Person",
    "name": "Jane Smith"
  },
  "datePublished": "2024-01-15",
  "reviewBody": "Super soft and fits perfectly!",
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "5",
    "bestRating": "5"
  }
}
```

### E-commerce SEO Checklist

- [ ] Unique title and description for each product
- [ ] Product structured data implemented
- [ ] High-quality product images with alt text
- [ ] Breadcrumb structured data
- [ ] Review/rating structured data
- [ ] Canonical URLs for product variations
- [ ] Faceted navigation handled properly
- [ ] Out-of-stock products managed appropriately
- [ ] Fast page loading
- [ ] Mobile-friendly design

---

## International and Multilingual Sites

Serving content in multiple languages or targeting multiple countries requires additional SEO considerations.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Geotargeting** | Targeting specific countries |
| **Multilingual** | Content in multiple languages |
| **hreflang** | Signals language/region variants |
| **ccTLD** | Country-code top-level domains (.fr, .de) |

### URL Structure Options

| Structure | Example | Pros | Cons |
|-----------|---------|------|------|
| ccTLD | example.fr | Clear country signal | Expensive, separate SEO |
| Subdomain | fr.example.com | Easy to set up | Weaker country signal |
| Subdirectory | example.com/fr/ | Single domain | Needs hreflang |
| Parameters | example.com?lang=fr | Easy to implement | Not recommended |

**Recommended**: Subdirectory or ccTLD for most cases.

### hreflang Implementation

hreflang tells Google which language/region version to show users.

**HTML head (for few languages)**:
```html
<link rel="alternate" hreflang="en" href="https://example.com/page">
<link rel="alternate" hreflang="en-gb" href="https://example.com/uk/page">
<link rel="alternate" hreflang="fr" href="https://example.com/fr/page">
<link rel="alternate" hreflang="de" href="https://example.com/de/page">
<link rel="alternate" hreflang="x-default" href="https://example.com/page">
```

**HTTP header (for non-HTML files)**:
```
Link: <https://example.com/page>; rel="alternate"; hreflang="en",
      <https://example.com/fr/page>; rel="alternate"; hreflang="fr"
```

**Sitemap (recommended for many languages)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://example.com/page</loc>
    <xhtml:link rel="alternate" hreflang="en" href="https://example.com/page"/>
    <xhtml:link rel="alternate" hreflang="fr" href="https://example.com/fr/page"/>
    <xhtml:link rel="alternate" hreflang="de" href="https://example.com/de/page"/>
  </url>
</urlset>
```

### hreflang Values

| Format | Example | Meaning |
|--------|---------|---------|
| Language | `fr` | French (any country) |
| Language-Region | `fr-ca` | French for Canada |
| x-default | `x-default` | Fallback for unspecified |

**Common language codes**:
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `ja` - Japanese
- `zh` - Chinese
- `pt` - Portuguese

**Adding region**:
- `en-us` - English for US
- `en-gb` - English for UK
- `es-mx` - Spanish for Mexico
- `pt-br` - Portuguese for Brazil

### Important hreflang Rules

1. **Self-referencing** - Each page must include a link to itself
2. **Bidirectional** - If A links to B, B must link to A
3. **Absolute URLs** - Use full URLs, not relative
4. **Valid language codes** - Use ISO 639-1 format
5. **x-default** - Include for fallback/language selector pages

### Geotargeting in Search Console

For generic TLDs (.com, .org), you can set a target country:
1. Go to Search Console
2. Settings → International Targeting
3. Select target country

> Note: ccTLDs (.fr, .de) automatically target their country.

### Content Considerations

#### Translation Quality

- Use professional human translation
- Don't use automatic translation as final content
- Consider cultural differences, not just language
- Localize currency, date formats, phone numbers

#### Duplicate Content

- hreflang prevents duplicate content penalties
- Each language version should be on a unique URL
- Don't use cookies/IP for language selection (Googlebot crawls from US)

#### Language Detection

**Don't do this**:
- Auto-redirect based on IP or browser language
- Block users from accessing other language versions

**Do this**:
- Show a banner suggesting the user's language version
- Allow users to easily switch languages
- Keep URLs consistent across languages

### Language Selector Best Practices

```html
<!-- Use language names in their native form -->
<nav aria-label="Language selector">
  <a href="/en/" hreflang="en">English</a>
  <a href="/fr/" hreflang="fr">Français</a>
  <a href="/de/" hreflang="de">Deutsch</a>
  <a href="/ja/" hreflang="ja">日本語</a>
</nav>
```

- Use native language names (Français not French)
- Link to equivalent pages, not just homepage
- Place in consistent, visible location
- Don't use flags alone (one country ≠ one language)

### International SEO Checklist

- [ ] Choose appropriate URL structure
- [ ] Implement hreflang annotations correctly
- [ ] Include x-default for fallback
- [ ] Ensure bidirectional hreflang links
- [ ] Self-reference on each page
- [ ] Use professional translations
- [ ] Set geotargeting in Search Console (if applicable)
- [ ] Allow users to switch languages
- [ ] Don't auto-redirect based on IP
- [ ] Localize content beyond just text (dates, currency)

---

## Additional Site-Specific Topics

### News Sites

- Follow Google News guidelines
- Use Article structured data
- Include publication date
- Update NewsArticle schema

### Educational Sites

- Use Course structured data
- Consider FAQ schema for common questions
- Implement proper pagination

### Local Businesses

- Claim Google Business Profile
- Use LocalBusiness structured data
- Include NAP (Name, Address, Phone)
- Collect and respond to reviews

### Healthcare Sites

- High E-E-A-T standards (YMYL)
- Cite authoritative sources
- Include author credentials
- Use MedicalWebPage schema where appropriate

---

## Quick Reference: Common Structured Data Types

| Site Type | Primary Schema Types |
|-----------|---------------------|
| E-commerce | Product, Offer, AggregateRating, Review |
| News | NewsArticle, Article |
| Recipes | Recipe, HowTo |
| Events | Event |
| Courses | Course |
| Local Business | LocalBusiness, Organization |
| FAQ | FAQPage, Question |
| How-to content | HowTo, Step |
| Reviews | Review, AggregateRating |
| Videos | VideoObject |
| Podcasts | PodcastEpisode, PodcastSeries |

---

*Source: https://developers.google.com/search/docs/specialty*
