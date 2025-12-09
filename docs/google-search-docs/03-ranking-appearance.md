# Ranking and Search Appearance

*Source: [Google Search Central Documentation](https://developers.google.com/search/docs/appearance)*

---

## Table of Contents

1. [Visual Elements Gallery](#visual-elements-gallery)
2. [Title Links](#title-links)
3. [Snippets and Meta Descriptions](#snippets-and-meta-descriptions)
4. [Image SEO](#image-seo)
5. [Video SEO](#video-seo)
6. [Structured Data](#structured-data)
7. [Favicons](#favicons)

---

## Visual Elements Gallery

Visual elements are the building blocks of Google Search results that users can perceive and interact with.

### Types of Search Results

| Type | Description |
|------|-------------|
| **Text Result** | Based on textual content of the page |
| **Rich Result** | Enhanced with structured data (review stars, recipes, etc.) |
| **Image Result** | Based on images embedded on the page |
| **Video Result** | Based on videos embedded on the page |
| **Exploration Features** | Related searches, related questions |

### Anatomy of a Text Result

```
┌─────────────────────────────────────────────────────────┐
│ 🌐 example.com › category › page                        │  ← Attribution
├─────────────────────────────────────────────────────────┤
│ Page Title That Links to Your Website                   │  ← Title Link
├─────────────────────────────────────────────────────────┤
│ This is the snippet that describes your page content    │  ← Snippet
│ and entices users to click through to learn more...     │
│ Dec 1, 2024                                             │  ← Byline Date
├─────────────────────────────────────────────────────────┤
│ ⭐⭐⭐⭐⭐ 4.8 (127 reviews) · $19.99                   │  ← Rich Attributes
└─────────────────────────────────────────────────────────┘
```

### Attribution Components

| Element | Description | Control |
|---------|-------------|---------|
| **Favicon** | Small icon for the site | [Set in HTML](https://developers.google.com/search/docs/appearance/favicon-in-search) |
| **Site Name** | Name of the website | [WebSite structured data](https://developers.google.com/search/docs/appearance/site-names) |
| **Domain** | The site address | Your domain choice |
| **Breadcrumb** | Page position in hierarchy | [Breadcrumb structured data](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb) |

---

## Title Links

The title link is the headline that links to your web page in search results.

### Sources for Title Links

Google uses these sources to determine title links:

1. Content in `<title>` elements (primary)
2. Main visual title on the page
3. Heading elements (`<h1>`, etc.)
4. `og:title` meta tags
5. Large/prominent text
6. Anchor text pointing to the page
7. WebSite structured data

### Best Practices

#### Do This ✓

```html
<title>How to Make Homemade Pizza - Joe's Kitchen</title>
```

- ✓ Unique for every page
- ✓ Descriptive and concise
- ✓ Uses natural language
- ✓ Includes brand concisely

#### Avoid This ✗

```html
<!-- Too generic -->
<title>Home</title>

<!-- Keyword stuffing -->
<title>Pizza, homemade pizza, make pizza, pizza recipe, best pizza</title>

<!-- Too long/boilerplate -->
<title>Joe's Kitchen - See recipes, videos, tips, tutorials, cooking guides</title>
```

### Common Issues Google Fixes

| Issue | What Google Does |
|-------|------------------|
| Half-empty titles | Uses heading text from page |
| Obsolete titles | Updates with current date from visible title |
| Inaccurate titles | Uses content that matches page better |
| Boilerplate titles | Creates unique title from page content |
| No clear main title | Uses first prominent heading |
| Language mismatch | Uses text matching primary content language |

### Title Best Practices Checklist

- [ ] Every page has a unique `<title>`
- [ ] Titles are descriptive and concise
- [ ] Main keyword appears near the beginning
- [ ] Brand name at the end (separated by ` | ` or ` - `)
- [ ] No keyword stuffing
- [ ] Same language as page content
- [ ] Avoid generic titles ("Home", "Page")

---

## Snippets and Meta Descriptions

The snippet is the description shown below the title link in search results.

### How Snippets Are Created

1. **Primary source**: Content on the page itself
2. **Secondary source**: Meta description tag
3. **Selection criteria**: What best relates to user's query

> Different queries may show different snippets for the same page.

### Meta Description Tag

```html
<meta name="description" content="Learn how to make authentic 
Neapolitan pizza at home with our step-by-step guide. Includes 
dough recipe, sauce tips, and baking instructions.">
```

### Controlling Snippets

```html
<!-- Prevent snippets entirely -->
<meta name="robots" content="nosnippet">

<!-- Limit snippet length (characters) -->
<meta name="robots" content="max-snippet:150">

<!-- Exclude specific text -->
<p>Public content here</p>
<span data-nosnippet>This won't appear in snippets</span>
```

### Writing Quality Meta Descriptions

#### Best Practices

1. **Unique for each page** - Identical descriptions aren't helpful
2. **Include relevant information** - Price, author, date, key features
3. **Descriptive, not just keywords** - Sentences that describe the page
4. **Appropriate length** - No limit, but truncated in results (~155 chars shown)

#### Examples

**Bad** (keywords only):
```
Pizza recipe homemade pizza dough pizza sauce pizza toppings
```

**Good** (descriptive):
```
Learn to make authentic Neapolitan pizza at home. Our 30-minute 
recipe includes tips for perfect dough, San Marzano tomato sauce, 
and achieving that crispy-yet-chewy crust.
```

**Bad** (same for every page):
```
Welcome to our website. We have the best content.
```

**Good** (page-specific):
```
Our margherita pizza recipe uses fresh mozzarella, basil, and a 
24-hour fermented dough for the perfect balance of flavors.
```

### Programmatic Descriptions

For large sites with database-driven content:

```html
<meta name="description" content="[Product Name] - [Price] - 
[Key Feature]. [Rating] stars from [Review Count] reviews. 
Free shipping on orders over $50.">
```

---

## Image SEO

Images help users discover your content visually through Google Images and text result images.

### Help Google Find Your Images

#### Use HTML Image Elements

**Good**:
```html
<img src="puppy.jpg" alt="Golden retriever puppy playing in park">
```

**Bad** (CSS background):
```css
.hero { background-image: url('puppy.jpg'); }
```

#### Use Image Sitemaps

```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>https://example.com/page</loc>
    <image:image>
      <image:loc>https://example.com/image.jpg</image:loc>
    </image:image>
  </url>
</urlset>
```

#### Responsive Images

```html
<img srcset="puppy-320w.jpg 320w,
             puppy-480w.jpg 480w,
             puppy-800w.jpg 800w"
     sizes="(max-width: 320px) 280px,
            (max-width: 480px) 440px,
            800px"
     src="puppy-800w.jpg"
     alt="Golden retriever puppy">
```

Or with `<picture>`:

```html
<picture>
  <source type="image/webp" srcset="puppy.webp">
  <source type="image/jpeg" srcset="puppy.jpg">
  <img src="puppy.jpg" alt="Golden retriever puppy">
</picture>
```

### Supported Formats

BMP, GIF, JPEG, PNG, WebP, SVG, AVIF

### Optimize Image Landing Pages

#### Good Page Titles and Descriptions

Images inherit context from the page they're on. Make sure:
- Page has descriptive title
- Page has relevant content around the image
- Meta description describes page content

#### Add Structured Data

Structured data can add badges (Recipe, Product, Video):

```json
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Chocolate Chip Cookies",
  "image": "https://example.com/cookies.jpg"
}
```

### Image Best Practices

#### Descriptive Filenames

**Good**: `golden-retriever-puppy-park.jpg`

**Bad**: `IMG00023.jpg`, `image1.jpg`

#### Alt Text

**Bad** (missing):
```html
<img src="cookies.jpg">
```

**Bad** (keyword stuffing):
```html
<img src="cookies.jpg" alt="cookies cookie recipe chocolate 
chip cookies best cookies homemade cookies">
```

**Good**:
```html
<img src="cookies.jpg" alt="Freshly baked chocolate chip 
cookies cooling on a wire rack">
```

#### Image Quality and Speed

- Use high-quality images (sharp, clear)
- But optimize for file size
- Use appropriate format (WebP for web)
- Test with PageSpeed Insights

---

## Video SEO

Videos can appear in Search, Google Videos, and Discover.

### Help Google Find Your Videos

#### Create Dedicated Pages

- Each video should have its own page
- Place video prominently on the page
- Add relevant text content around the video

#### Supported Formats

MP4, WebM, and most common video formats. Also supports:
- YouTube embeds
- Vimeo embeds
- Other third-party players

### Ensure Videos Can Be Indexed

1. **Public URL for video file**
2. **Valid structured data**
3. **Not blocked by robots.txt**
4. **Available in user's region**

### Video Structured Data

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "How to Make Pizza Dough",
  "description": "Step-by-step guide to making pizza dough from scratch",
  "thumbnailUrl": "https://example.com/thumbnail.jpg",
  "uploadDate": "2024-01-15",
  "duration": "PT10M30S",
  "contentUrl": "https://example.com/video.mp4",
  "embedUrl": "https://example.com/embed/video"
}
```

### Video Features

| Feature | Requirement |
|---------|-------------|
| **Thumbnail** | High-quality image, specific size requirements |
| **Key moments** | Clip structured data or YouTube chapters |
| **Live badge** | BroadcastEvent structured data |
| **Video previews** | Allow Google to fetch video file |

### Video Thumbnails

- Provide high-quality thumbnails
- Minimum 60px height in results
- Recommended: 1280x720 pixels
- Use structured data to specify

### Remove or Restrict Videos

**Remove completely**:
- Add `noindex` meta tag
- Remove from sitemap
- Return 404/410 status

**Restrict by location**:
- Use structured data `regionsAllowed` property
- Block by IP at server level

---

## Structured Data

Structured data helps Google understand your content and can enable rich results.

### What is Structured Data?

A standardized format for providing information about a page and classifying content.

### Formats Supported

- **JSON-LD** (recommended)
- **Microdata**
- **RDFa**

### Rich Result Types

| Type | Description |
|------|-------------|
| Articles | News articles, blog posts |
| Breadcrumbs | Navigation trail |
| Carousels | Multiple items in scrollable list |
| Events | Concerts, festivals, etc. |
| FAQ | Question and answer pairs |
| How-to | Step-by-step instructions |
| Products | E-commerce products with price |
| Recipes | Cooking recipes with ingredients |
| Reviews | Review snippets with ratings |
| Videos | Video content |
| And many more... | [Full gallery](https://developers.google.com/search/docs/appearance/structured-data/search-gallery) |

### Example: Recipe

```json
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Chocolate Chip Cookies",
  "image": ["https://example.com/cookies.jpg"],
  "author": {
    "@type": "Person",
    "name": "Jane Doe"
  },
  "datePublished": "2024-01-15",
  "description": "These cookies are soft, chewy, and full of chocolate chips.",
  "prepTime": "PT15M",
  "cookTime": "PT10M",
  "totalTime": "PT25M",
  "recipeYield": "24 cookies",
  "recipeIngredient": [
    "2 1/4 cups all-purpose flour",
    "1 cup butter, softened",
    "3/4 cup sugar"
  ],
  "recipeInstructions": [
    {
      "@type": "HowToStep",
      "text": "Preheat oven to 375°F"
    },
    {
      "@type": "HowToStep",
      "text": "Mix flour, baking soda, and salt"
    }
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "127"
  }
}
```

### Example: FAQPage

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is SEO?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "SEO stands for Search Engine Optimization..."
      }
    },
    {
      "@type": "Question",
      "name": "How long does SEO take?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "SEO results typically take 3-6 months..."
      }
    }
  ]
}
```

### Testing Structured Data

1. **[Rich Results Test](https://search.google.com/test/rich-results)** - Check if eligible for rich results
2. **[Schema Markup Validator](https://validator.schema.org/)** - Validate syntax
3. **Search Console** - Monitor errors and impressions

---

## Favicons

Favicons appear next to your site name in search results.

### Implementation

```html
<link rel="icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
```

### Guidelines

| Requirement | Details |
|-------------|---------|
| **Size** | Multiple of 48px (recommended: 48x48, 96x96, 144x144) |
| **Format** | ICO, PNG, SVG, GIF (static) |
| **Location** | Root of domain or specified in `<link>` |
| **Visibility** | Must be crawlable (not blocked by robots.txt) |

### Best Practices

1. **Use your logo or brand mark** (simplified for small sizes)
2. **Ensure good contrast** (visible on various backgrounds)
3. **Keep it simple** (details lost at small sizes)
4. **Test at 16x16** (smallest display size)
5. **No inappropriate content** (Google will remove offensive favicons)

### SVG Favicon

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
```

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
  <circle cx="24" cy="24" r="20" fill="#4285f4"/>
  <text x="24" y="32" text-anchor="middle" fill="white" font-size="24">V</text>
</svg>
```

---

## Quick Reference Checklist

### Every Page Should Have
- [ ] Unique, descriptive `<title>` element
- [ ] Unique meta description
- [ ] Relevant heading structure (H1, H2, etc.)
- [ ] Alt text on images
- [ ] Fast loading time
- [ ] Mobile-friendly design

### Rich Results
- [ ] Identify applicable structured data types
- [ ] Implement JSON-LD markup
- [ ] Test with Rich Results Test
- [ ] Monitor in Search Console

### Images
- [ ] Descriptive filenames
- [ ] Alt text on all images
- [ ] Responsive image implementation
- [ ] Image sitemap for important images

### Videos
- [ ] Dedicated page per video
- [ ] Video structured data
- [ ] High-quality thumbnail
- [ ] Relevant surrounding text

---

*Source: https://developers.google.com/search/docs/appearance*
