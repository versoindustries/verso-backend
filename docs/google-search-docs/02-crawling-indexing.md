# Crawling and Indexing

*Source: [Google Search Central Documentation](https://developers.google.com/search/docs/crawling-indexing)*

---

## Table of Contents

1. [Overview](#overview)
2. [Sitemaps](#sitemaps)
3. [robots.txt](#robotstxt)
4. [Meta Tags](#meta-tags)
5. [Canonicalization](#canonicalization)
6. [JavaScript SEO](#javascript-seo)
7. [Redirects](#redirects)
8. [Googlebot](#googlebot)

---

## Overview

The crawling and indexing topics describe how you can control Google's ability to find and parse your content in order to show it in Search and other Google properties.

### Key Topics

| Topic | Description |
|-------|-------------|
| File types | What Google can index |
| URL structure | How to organize URLs |
| Sitemaps | Providing page information to Google |
| Crawler management | Controlling how Google crawls |
| robots.txt | Blocking crawlers |
| Canonicalization | Handling duplicate content |
| Meta tags | Page-level indexing controls |
| JavaScript | SEO for JS-heavy sites |
| Removals | Keeping content out of search |
| Site moves | Handling URL changes |

---

## Sitemaps

A sitemap is a file where you provide information about pages, videos, and other files on your site, and relationships between them.

### What Sitemaps Do

- Tell search engines which pages you think are important
- Provide valuable metadata (last updated, alternate languages)
- Help with video, image, and news content discovery

### Types of Sitemap Content

1. **Video entries**: Running time, rating, age-appropriateness
2. **Image entries**: Location of images on pages
3. **News entries**: Article title, publication date

### Do You Need a Sitemap?

**You might need one if**:
- Your site is large (harder to ensure all pages are linked)
- Your site is new with few external links
- You have lots of rich media content (video, images)
- You're shown in Google News

**You might NOT need one if**:
- Your site is small (~500 pages or fewer)
- Site is comprehensively linked internally
- You don't need media files to appear in search results

### Sitemap Best Practices

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.example.com/page1</loc>
    <lastmod>2024-01-15</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

---

## robots.txt

A robots.txt file tells search engine crawlers which URLs they can access on your site.

### Purpose

- **Main use**: Manage crawler traffic to avoid overloading your site
- **NOT for**: Keeping pages out of Google (use `noindex` for that)

### What robots.txt Does NOT Do

> ⚠️ **Warning**: Don't use robots.txt to hide web pages from Google Search results. If other pages link to your page, it can still be indexed without Google visiting the page.

### Limitations

1. **Not all crawlers obey it** - Only respectable crawlers follow the rules
2. **Different syntax interpretations** - Crawlers may interpret rules differently
3. **Disallowed pages can still be indexed** - If linked from other sites

### Basic Syntax

```
User-agent: *
Disallow: /private/
Disallow: /admin/

User-agent: Googlebot
Allow: /public/
Disallow: /search

Sitemap: https://www.example.com/sitemap.xml
```

### Common Directives

| Directive | Purpose |
|-----------|---------|
| `User-agent` | Specifies which crawler the rules apply to |
| `Disallow` | Blocks crawler from accessing path |
| `Allow` | Allows access (overrides Disallow) |
| `Sitemap` | Location of sitemap file |

### What to Block vs Not Block

**Good to block**:
- Admin pages
- Internal search results
- Duplicate content (temporary solution)
- Unfinished sections

**Don't block**:
- CSS and JavaScript files Google needs to render pages
- Pages you want indexed
- Images you want in search results

---

## Meta Tags

Meta tags are HTML tags used to provide additional information about a page to search engines.

### Placement

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="description" content="Your page description">
    <meta name="robots" content="index, follow">
    <title>Page Title</title>
  </head>
</html>
```

### Supported Meta Tags

#### description

```html
<meta name="description" content="A description of the page">
```

May be used for the snippet shown in search results.

#### robots / googlebot

```html
<meta name="robots" content="noindex, nofollow">
<meta name="googlebot" content="nosnippet">
```

| Value | Effect |
|-------|--------|
| `index` | Allow indexing (default) |
| `noindex` | Prevent indexing |
| `follow` | Follow links (default) |
| `nofollow` | Don't follow links |
| `nosnippet` | Don't show snippet |
| `max-snippet:[number]` | Limit snippet length |
| `noarchive` | Don't show cached link |
| `noimageindex` | Don't index images |

#### notranslate

```html
<meta name="googlebot" content="notranslate">
```

Prevents Google from offering translated versions.

#### google-site-verification

```html
<meta name="google-site-verification" content="verification-token">
```

Used to verify site ownership in Search Console.

#### viewport

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

Indicates the page is mobile-friendly.

### Unsupported Tags

| Tag | Notes |
|-----|-------|
| `keywords` | Google doesn't use this |
| `lang` attribute | Not used for language detection |
| `rel="next/prev"` | No longer used |

---

## Canonicalization

When a site has duplicate content, Google chooses a canonical URL to show in search results.

### What is Canonicalization?

The process of selecting the representative URL for duplicate or similar content.

### Why It Matters

- Consolidates ranking signals to one URL
- Avoids splitting authority across duplicates
- Helps users find the right page

### Methods to Specify Canonical

#### 1. rel="canonical" Link Tag (Preferred)

```html
<link rel="canonical" href="https://example.com/preferred-page">
```

#### 2. HTTP Header

```
Link: <https://example.com/preferred-page>; rel="canonical"
```

Useful for non-HTML files (PDFs, etc.)

#### 3. Sitemap

Include only canonical URLs in your sitemap.

#### 4. 301 Redirects

Redirect duplicate URLs to the canonical version.

### Best Practices

1. **Be consistent** - Use the same canonical across all duplicates
2. **Use absolute URLs** - `https://example.com/page` not `/page`
3. **Match protocol** - If using HTTPS, canonicalize to HTTPS
4. **Match www/non-www** - Pick one and stick to it

### Common Canonicalization Issues

| Issue | Solution |
|-------|----------|
| HTTP and HTTPS versions | Redirect HTTP to HTTPS |
| www and non-www | Choose one, redirect the other |
| Trailing slashes | Be consistent, redirect duplicates |
| URL parameters | Use canonical to point to clean URL |
| Mobile pages | Use `rel="alternate"` with hreflang |

---

## JavaScript SEO

JavaScript is important, but requires extra consideration for SEO.

### How Google Processes JavaScript

1. **Crawling** - Fetches the page
2. **Rendering** - Executes JavaScript with headless Chromium
3. **Indexing** - Stores the rendered content

> Google uses an evergreen version of Chromium for rendering.

### Best Practices

#### 1. Unique Titles and Meta Descriptions

- Both can be set via JavaScript
- Make sure they're set before the page is rendered

#### 2. Write Compatible Code

- Use polyfills for unsupported APIs
- Test with feature detection
- Follow [web.dev guidelines](https://web.dev)

#### 3. Use Meaningful HTTP Status Codes

```javascript
// For single-page apps with client-side routing
if (!product.exists) {
  // Option 1: Redirect to 404 page
  window.location.href = '/not-found';
  
  // Option 2: Add noindex tag
  const metaRobots = document.createElement('meta');
  metaRobots.name = 'robots';
  metaRobots.content = 'noindex';
  document.head.appendChild(metaRobots);
}
```

#### 4. Use History API Instead of Fragments

**Bad** (fragments):
```html
<a href="#/products">Products</a>
```

**Good** (clean URLs):
```html
<a href="/products">Products</a>
```

#### 5. Properly Inject Canonical Tags

```javascript
const linkTag = document.createElement('link');
linkTag.setAttribute('rel', 'canonical');
linkTag.href = 'https://example.com/page';
document.head.appendChild(linkTag);
```

#### 6. Use Long-Lived Caching

- Google aggressively caches resources
- Use content fingerprinting: `main.2bb85551.js`
- Fingerprint changes when content changes

#### 7. Structured Data with JavaScript

JSON-LD can be injected via JavaScript and will be processed.

#### 8. Web Components

- Google flattens shadow DOM content
- Use `<slot>` elements for content projection
- Test with Rich Results Test

#### 9. Lazy Loading

- Implement lazy loading carefully
- Content must be visible when Googlebot renders
- Use Intersection Observer API

#### 10. Design for Accessibility

- Pages should be usable without JavaScript
- Test with JavaScript disabled
- Use semantic HTML

---

## Redirects

Redirects tell browsers and search engines that a page has moved.

### Types of Redirects

#### Server-Side Redirects (Preferred)

| Code | Type | Use Case |
|------|------|----------|
| 301 | Permanent | Page permanently moved |
| 302 | Temporary | Page temporarily moved |
| 307 | Temporary | Same as 302, preserves request method |
| 308 | Permanent | Same as 301, preserves request method |

#### Client-Side Redirects

**Meta Refresh** (not recommended):
```html
<meta http-equiv="refresh" content="0;url=https://example.com/new-page">
```

**JavaScript** (less ideal):
```javascript
window.location = 'https://example.com/new-page';
```

### When to Use Which

| Scenario | Redirect Type |
|----------|---------------|
| Site moved to new domain | 301 |
| Old page replaced by new | 301 |
| Temporary maintenance page | 302 |
| A/B testing | 302 |
| Seasonal content | 302 |

### Redirect Best Practices

1. **Use 301 for permanent moves** - Passes ranking signals
2. **Avoid redirect chains** - A → B → C slows crawling
3. **Keep redirects for at least 1 year** - For major site moves
4. **Update internal links** - Don't rely only on redirects
5. **Monitor in Search Console** - Check for redirect errors

---

## Googlebot

Googlebot is the generic name for Google's web crawler.

### How Googlebot Accesses Sites

- Crawls from distributed IP addresses
- Uses two versions: Desktop and Mobile (Smartphone)
- Mobile-first indexing means smartphone version is primary

### Googlebot Behavior

- Respects robots.txt
- Tries not to overload sites
- Slows down if it gets HTTP 500 errors
- Renders JavaScript like Chrome

### User Agent Strings

**Desktop**:
```
Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)
```

**Mobile**:
```
Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/W.X.Y.Z Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)
```

### Verifying Googlebot

1. Perform reverse DNS lookup on IP
2. IP should resolve to `googlebot.com` or `google.com`
3. Forward DNS lookup should return same IP

### Blocking Googlebot

via robots.txt:
```
User-agent: Googlebot
Disallow: /private/
```

> ⚠️ Remember: Blocking Googlebot prevents crawling but doesn't remove from index if page is linked elsewhere.

---

## Quick Implementation Checklist

### Essential Crawling Setup
- [ ] Create and submit sitemap.xml
- [ ] Set up robots.txt properly
- [ ] Verify site ownership in Search Console
- [ ] Check for crawl errors regularly

### Indexing Controls
- [ ] Use appropriate meta robots tags
- [ ] Set canonical URLs for duplicate content
- [ ] Handle URL parameters properly
- [ ] Implement proper redirects

### JavaScript Sites
- [ ] Ensure content is rendered for Googlebot
- [ ] Test with URL Inspection tool
- [ ] Use History API for routing
- [ ] Implement proper error handling

---

*Source: https://developers.google.com/search/docs/crawling-indexing*
