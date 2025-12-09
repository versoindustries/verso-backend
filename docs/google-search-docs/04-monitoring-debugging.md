# Monitoring and Debugging

*Source: [Google Search Central Documentation](https://developers.google.com/search/docs/monitor-debug)*

---

## Table of Contents

1. [Getting Started with Search Console](#getting-started-with-search-console)
2. [Debugging Traffic Drops](#debugging-traffic-drops)
3. [Important Reports](#important-reports)
4. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Getting Started with Search Console

Search Console is a free tool from Google that helps you monitor and optimize your site's performance in Google Search.

### What Search Console Does

- Shows how Google crawls, indexes, and serves your site
- Provides performance data (clicks, impressions, position)
- Alerts you to issues via email
- Helps you submit and monitor sitemaps
- Shows structured data errors

### Getting Started Steps

#### Step 1: Verify Site Ownership

Options for verification:
- **HTML file upload** - Upload a file to your server
- **HTML tag** - Add meta tag to homepage
- **DNS record** - Add TXT record to domain
- **Google Analytics** - Use existing GA code
- **Google Tag Manager** - Use existing GTM container

#### Step 2: Check Index Coverage

Review the Index Coverage report to see:
- Pages successfully indexed
- Pages with errors
- Pages with warnings
- Excluded pages (and why)

#### Step 3: Submit Sitemap (Optional)

```
https://search.google.com/search-console/sitemaps
```

Benefits:
- Faster discovery of new pages
- Monitoring of sitemap status
- Error reporting for sitemap issues

#### Step 4: Monitor Performance

The Performance report shows:
- **Clicks** - How many times users clicked to your site
- **Impressions** - How often your site appeared in results
- **CTR** - Click-through rate (clicks ÷ impressions)
- **Position** - Average ranking position

---

## Debugging Traffic Drops

When traffic drops, use this systematic approach to identify the cause.

### Main Causes of Traffic Drops

```
┌────────────────────────────────────────────────┐
│ Large sudden drop                              │
│ → Algorithmic update, security/spam issue      │
├────────────────────────────────────────────────┤
│ Gradual decline over time                      │
│ → Seasonality, changing interests              │
├────────────────────────────────────────────────┤
│ Technical pattern                              │  
│ → Technical issue, crawl errors                │
├────────────────────────────────────────────────┤
│ Random fluctuation                             │
│ → Reporting glitch, normal variance            │
└────────────────────────────────────────────────┘
```

### Cause 1: Algorithmic Update

Google regularly updates its ranking systems.

**How to identify**:
- Check [Google Search Status Dashboard](https://status.search.google.com)
- Look for announcements about core updates
- Compare drop timing with update announcements

**What to do**:
- Review content quality
- Ensure E-E-A-T signals are strong
- Focus on people-first content
- Be patient—recovery can take months

### Position Changes

| Type | Example | Action |
|------|---------|--------|
| Small drop | Position 2 → 4 | Normal fluctuation, monitor |
| Large drop | Position 4 → 29 | Self-assess entire site for helpfulness |

### Cause 2: Technical Issues

Technical problems can prevent crawling or indexing.

**Common issues**:
- Server errors (5xx)
- robots.txt blocking important pages
- noindex tags accidentally added
- Slow server response
- SSL/HTTPS problems

**How to identify**:
- Check Crawl Stats report
- Check Page Indexing report
- Use URL Inspection tool

**What to do**:
- Fix server errors
- Review robots.txt changes
- Check for accidental noindex tags
- Improve server performance

### Cause 3: Security Issues

Malware or phishing can cause Google to display warnings.

**How to identify**:
- Check Security Issues report in Search Console
- Look for "This site may be hacked" warnings in results

**What to do**:
- Clean infected files
- Change passwords
- Submit reconsideration request after fixing

### Cause 4: Manual Actions (Spam)

Manual penalties are applied by human reviewers.

**How to identify**:
- Check Manual Actions report in Search Console

**What to do**:
- Review the specific issue listed
- Fix the problem
- Submit reconsideration request

### Cause 5: Seasonality

User interest naturally varies throughout the year.

**How to identify**:
- Use Google Trends to check query popularity
- Compare to same period last year
- Check if competitors saw similar drop

**What to do**:
- This is normal—plan for seasonal variations
- Consider content for off-peak seasons

### Cause 6: Site Migration

Moving to a new domain or URL structure can cause temporary drops.

**How to identify**:
- Did you recently change URLs?
- Check for redirect errors
- Look for crawl errors on old URLs

**What to do**:
- Ensure 301 redirects are in place
- Use Change of Address tool in Search Console
- Keep redirects for at least 1 year

---

## Important Reports

### Performance Report

Shows how your site appears in search results.

**Key metrics**:
| Metric | Description |
|--------|-------------|
| Clicks | Total clicks to your site |
| Impressions | Times your URL appeared in results |
| CTR | Clicks ÷ Impressions |
| Position | Average ranking position |

**Filtering options**:
- By query
- By page
- By country
- By device
- By search type (web, image, video)
- By date range

**Tips**:
- Set date range to 16 months for year-over-year comparison
- Filter by query to see which terms are declining
- Filter by page to see which pages are affected

### Index Coverage Report

Shows which pages Google could or couldn't index.

**Statuses**:
| Status | Meaning |
|--------|---------|
| Valid | Successfully indexed |
| Valid with warnings | Indexed but has issues |
| Error | Not indexed due to error |
| Excluded | Intentionally or unintentionally not indexed |

**Common errors**:
- Server errors (5xx)
- Redirect errors
- Soft 404 errors
- Blocked by robots.txt
- noindex tag present

### URL Inspection Tool

Inspect individual URLs for detailed information.

**What it shows**:
- Is URL in Google index?
- Canonical URL selected
- Mobile usability status
- Structured data detected
- Last crawl date

**Actions**:
- Request indexing
- Test live URL
- View rendered page
- View page source

### Core Web Vitals Report

Shows page experience metrics based on real user data.

**Metrics**:
| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP (Largest Contentful Paint) | ≤2.5s | 2.5-4s | >4s |
| INP (Interaction to Next Paint) | ≤200ms | 200-500ms | >500ms |
| CLS (Cumulative Layout Shift) | ≤0.1 | 0.1-0.25 | >0.25 |

### Security Issues Report

Shows if Google detected security threats.

**Issue types**:
- Malware
- Phishing
- Hacked content
- Harmful downloads
- Deceptive content

### Manual Actions Report

Shows if a human reviewer imposed a penalty.

**Common reasons**:
- Thin content
- Unnatural links to/from your site
- Cloaking
- Hidden text
- User-generated spam
- Structured data spam

---

## Common Issues and Solutions

### Issue: Pages Not Being Indexed

**Possible causes**:
1. robots.txt blocking Googlebot
2. noindex meta tag on page
3. Pages not linked from site
4. Server errors
5. Low quality content

**Solution steps**:
1. Check robots.txt doesn't block the URL
2. Check for noindex tag in page source
3. Add internal links to important pages
4. Check server status codes
5. Improve content quality

### Issue: Rankings Dropped Suddenly

**Possible causes**:
1. Algorithm update
2. Technical issue
3. Manual action
4. Content quality issue
5. Security issue

**Solution steps**:
1. Check Search Status Dashboard for updates
2. Check Crawl Stats and Index Coverage reports
3. Check Manual Actions report
4. Review content quality
5. Check Security Issues report

### Issue: CTR is Low

**Possible causes**:
1. Title not compelling
2. Meta description not relevant
3. No rich results
4. Low position in results

**Solution steps**:
1. Improve title tags
2. Write better meta descriptions
3. Add structured data for rich results
4. Improve content to increase rankings

### Issue: Sitemap Errors

**Possible causes**:
1. Invalid XML format
2. URLs blocked by robots.txt
3. URLs returning errors
4. Too many URLs (over 50,000)

**Solution steps**:
1. Validate XML syntax
2. Remove blocked URLs from sitemap
3. Fix server errors on listed URLs
4. Split into multiple sitemaps

---

## Monitoring Checklist

### Weekly Checks
- [ ] Review Performance report for unusual drops
- [ ] Check for new messages in Search Console
- [ ] Monitor Core Web Vitals

### Monthly Checks
- [ ] Review Index Coverage report
- [ ] Check for crawl errors
- [ ] Verify sitemap is up to date
- [ ] Review structured data errors

### After Site Changes
- [ ] Use URL Inspection tool on updated pages
- [ ] Request indexing for important pages
- [ ] Update sitemap if URLs changed
- [ ] Monitor for any negative impacts

### Useful Tools

| Tool | Purpose |
|------|---------|
| [Search Console](https://search.google.com/search-console) | Main monitoring dashboard |
| [PageSpeed Insights](https://pagespeed.web.dev) | Page speed analysis |
| [Rich Results Test](https://search.google.com/test/rich-results) | Test structured data |
| [Mobile-Friendly Test](https://search.google.com/test/mobile-friendly) | Check mobile usability |
| [Google Trends](https://trends.google.com) | Check search interest |
| [Google Status Dashboard](https://status.search.google.com) | Check for updates |

---

## Quick Reference: Search Console URLs

| Report | URL |
|--------|-----|
| Performance | `https://search.google.com/search-console/performance` |
| Index Coverage | `https://search.google.com/search-console/index` |
| URL Inspection | `https://search.google.com/search-console/inspect` |
| Sitemaps | `https://search.google.com/search-console/sitemaps` |
| Core Web Vitals | `https://search.google.com/search-console/core-web-vitals` |
| Manual Actions | `https://search.google.com/search-console/manual-actions` |
| Security Issues | `https://search.google.com/search-console/security-issues` |

---

*Source: https://developers.google.com/search/docs/monitor-debug*
