---
description: Audit and setup SEO compliance based on Google Search guidelines
---

# SEO Setup Workflow

Comprehensive workflow to audit and optimize your site for Google Search compliance, based on the official [Google Search Central documentation](https://developers.google.com/search/docs).

---

## Quick Start

1. Run the **Technical Audit** (Phase 1) first
2. Fix any blocking issues before proceeding
3. Work through **On-Page SEO** (Phase 2) page by page
4. Implement **Structured Data** (Phase 3) for rich results
5. Set up **Monitoring** (Phase 4) for ongoing optimization

---

## Phase 1: Technical Requirements Audit

> Verify the bare minimum that Google needs to crawl and index your site.

### 1.1 Check robots.txt

// turbo
```bash
cat app/static/robots.txt 2>/dev/null || echo "robots.txt not found - create one"
```

**Expected content:**
```txt
User-agent: *
Allow: /

Sitemap: https://yourdomain.com/sitemap.xml

# Block admin/private areas
Disallow: /admin/
Disallow: /api/
Disallow: /user/
```

**Create if missing:**
```bash
cat > app/static/robots.txt << 'EOF'
User-agent: *
Allow: /

Sitemap: https://yourdomain.com/sitemap.xml

Disallow: /admin/
Disallow: /api/
Disallow: /user/
Disallow: /static/src/
EOF
```

### 1.2 Check Sitemap

// turbo
```bash
ls -la app/static/sitemap.xml 2>/dev/null || echo "sitemap.xml not found"
```

**Verify sitemap route exists:**
```bash
rg "sitemap" app/routes/ --type py
```

### 1.3 Verify HTTPS & Security Headers

Check `base.html` for security meta tags:
// turbo
```bash
rg "Content-Security-Policy|X-Frame-Options|csrf-token" app/templates/base.html
```

### 1.4 Mobile-Friendliness Check

Verify viewport meta tag:
// turbo
```bash
rg 'viewport.*width=device-width' app/templates/base.html
```

### 1.5 Page Speed Prerequisites

Check for render-blocking resources:
// turbo
```bash
rg 'defer|async' app/templates/base.html
```

**Best practices:**
- JavaScript should use `defer` attribute
- Critical CSS should be inline or loaded first
- Images should be lazy-loaded where appropriate

---

## Phase 2: On-Page SEO Checklist

> Optimize each page for search visibility.

### 2.1 Title Tags

**Pattern in Jinja2 templates:**
```html
{% block title %}Descriptive Page Title - Brand Name{% endblock %}
```

**Audit all templates:**
// turbo
```bash
rg "{% block title %}" app/templates/ --type html -l
```

**Check for generic titles:**
// turbo
```bash
rg "{% block title %}(Home|Page|Untitled)" app/templates/ --type html
```

**Best practices:**
- ✅ Unique for every page
- ✅ 50-60 characters ideal
- ✅ Primary keyword near beginning
- ✅ Brand name at end (after ` - ` or ` | `)
- ❌ No keyword stuffing
- ❌ No generic titles ("Home", "Page")

### 2.2 Meta Descriptions

**Pattern in Jinja2 templates:**
```html
{% block description %}Compelling description of page content. 
Include key information users care about. 150-160 chars ideal.{% endblock %}
```

**Audit templates:**
// turbo
```bash
rg "{% block description %}" app/templates/ --type html -l
```

**Best practices:**
- ✅ Unique for each page
- ✅ 150-160 characters
- ✅ Includes call-to-action
- ✅ Summarizes page content accurately
- ❌ No keyword stuffing
- ❌ No duplicate descriptions

### 2.3 Heading Structure

**Audit H1 tags (should be exactly one per page):**
// turbo
```bash
rg "<h1" app/templates/ --type html -c | sort -t: -k2 -n -r | head -20
```

**Best practices:**
- ✅ One `<h1>` per page
- ✅ H1 matches page topic
- ✅ Logical hierarchy (H1 → H2 → H3)
- ✅ Keywords in headings where natural

### 2.4 Image Alt Text

**Find images missing alt text:**
// turbo
```bash
rg '<img[^>]*(?<!alt=")[^>]*>' app/templates/ --type html
```

**Pattern with alt text:**
```html
<img src="{{ url_for('static', filename='images/hero.jpg') }}" 
     alt="Descriptive text about the image content"
     loading="lazy">
```

### 2.5 Internal Linking

**Check for crawlable links:**
```html
<!-- Good - crawlable -->
<a href="{{ url_for('main_routes.services') }}">Our Services</a>

<!-- Bad - not crawlable (JS-only navigation) -->
<span onclick="navigate('/services')">Our Services</span>
```

---

## Phase 3: Structured Data Implementation

> Enable rich results in Google Search.

### 3.1 Organization Schema (Site-wide)

Add to `base.html` in the `<head>` block:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{{ business_config.get('business_name', 'Company Name') }}",
  "url": "{{ request.url_root }}",
  "logo": "{{ url_for('static', filename='images/logo.png', _external=True) }}",
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "{{ business_config.get('phone', '') }}",
    "contactType": "customer service"
  }
}
</script>
```

### 3.2 WebSite Schema (for Sitelinks Search Box)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "{{ business_config.get('business_name', 'Site Name') }}",
  "url": "{{ request.url_root }}",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "{{ url_for('main_routes.search', _external=True) }}?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
</script>
```

### 3.3 BreadcrumbList Schema

For category/hierarchy pages:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "{{ url_for('main_routes.index', _external=True) }}"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "{{ category.name }}",
      "item": "{{ url_for('shop.category', slug=category.slug, _external=True) }}"
    }
  ]
}
</script>
```

### 3.4 Article Schema (Blog Posts)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{{ post.title }}",
  "image": "{{ post.featured_image_url }}",
  "author": {
    "@type": "Person",
    "name": "{{ post.author.display_name }}"
  },
  "publisher": {
    "@type": "Organization",
    "name": "{{ business_config.get('business_name') }}",
    "logo": {
      "@type": "ImageObject",
      "url": "{{ url_for('static', filename='images/logo.png', _external=True) }}"
    }
  },
  "datePublished": "{{ post.created_at.isoformat() }}",
  "dateModified": "{{ post.updated_at.isoformat() }}"
}
</script>
```

### 3.5 Product Schema (E-commerce)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ product.name }}",
  "image": "{{ product.image_url }}",
  "description": "{{ product.description }}",
  "sku": "{{ product.sku }}",
  "offers": {
    "@type": "Offer",
    "price": "{{ product.price }}",
    "priceCurrency": "USD",
    "availability": "{{ 'https://schema.org/InStock' if product.in_stock else 'https://schema.org/OutOfStock' }}",
    "url": "{{ url_for('shop.product', slug=product.slug, _external=True) }}"
  }
  {% if product.reviews %}
  ,"aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "{{ product.average_rating }}",
    "reviewCount": "{{ product.review_count }}"
  }
  {% endif %}
}
</script>
```

### 3.6 LocalBusiness Schema (Service Business)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "{{ business_config.get('business_name') }}",
  "image": "{{ url_for('static', filename='images/logo.png', _external=True) }}",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "{{ business_config.get('address') }}",
    "addressLocality": "{{ business_config.get('city') }}",
    "addressRegion": "{{ business_config.get('state') }}",
    "postalCode": "{{ business_config.get('zip') }}",
    "addressCountry": "US"
  },
  "telephone": "{{ business_config.get('phone') }}",
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "09:00",
      "closes": "17:00"
    }
  ]
}
</script>
```

### 3.7 Validate Structured Data

**Tools:**
- [Rich Results Test](https://search.google.com/test/rich-results) - Check if eligible for rich results
- [Schema Markup Validator](https://validator.schema.org/) - Validate JSON-LD syntax

---

## Phase 4: Monitoring & Analytics Setup

### 4.1 Google Search Console

1. Verify site ownership at [Search Console](https://search.google.com/search-console)
2. Submit sitemap URL
3. Check for crawl errors
4. Monitor Core Web Vitals

### 4.2 Google Analytics 4

Check GA4 is configured in `base.html`:
// turbo
```bash
rg "gtag|ga4_tracking_id" app/templates/base.html
```

### 4.3 PageSpeed Insights

Test key pages:
- Homepage
- Product listing page
- Product detail page
- Blog post page
- Contact/booking page

**Key metrics:**
- Largest Contentful Paint (LCP) < 2.5s
- First Input Delay (FID) < 100ms
- Cumulative Layout Shift (CLS) < 0.1

---

## Phase 5: Content Quality Audit

Based on Google's E-E-A-T guidelines.

### 5.1 Author Information

For blog/article content:
- [ ] Author bylines on articles
- [ ] Author bio/about pages
- [ ] Author credentials displayed

### 5.2 About & Contact Pages

// turbo
```bash
ls -la app/templates/about*.html app/templates/contact*.html 2>/dev/null
```

**Required elements:**
- [ ] About page explains company/service
- [ ] Contact information visible
- [ ] Physical address (for local businesses)
- [ ] Phone/email contact options

### 5.3 Privacy & Legal Pages

// turbo
```bash
ls -la app/templates/privacy*.html app/templates/terms*.html 2>/dev/null
```

---

## Verification Commands

### Full SEO Audit
// turbo
```bash
echo "=== SEO Audit Summary ===" && \
echo "" && \
echo "1. robots.txt:" && (test -f app/static/robots.txt && echo "✅ Found" || echo "❌ Missing") && \
echo "" && \
echo "2. Sitemap:" && (test -f app/static/sitemap.xml && echo "✅ Found" || rg -q "sitemap" app/routes/*.py && echo "✅ Dynamic route found" || echo "❌ Missing") && \
echo "" && \
echo "3. Title blocks:" && echo "$(rg -c '{% block title %}' app/templates/ --type html | wc -l) templates have title blocks" && \
echo "" && \
echo "4. Description blocks:" && echo "$(rg -c '{% block description %}' app/templates/ --type html | wc -l) templates have description blocks" && \
echo "" && \
echo "5. H1 tags:" && rg -c '<h1' app/templates/ --type html | sort -t: -k2 -n -r | head -5
```

---

## Next Steps After Audit

1. **Fix critical issues first** (robots.txt blocking, missing sitemaps)
2. **Prioritize high-traffic pages** for title/description optimization
3. **Implement structured data** starting with Organization and WebSite
4. **Monitor Search Console** weekly for new issues
5. **Re-run this workflow** quarterly for ongoing optimization

---

*Based on [Google Search Central Documentation](https://developers.google.com/search/docs)*
*Last updated: December 2024*
