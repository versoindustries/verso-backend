# SEO Fundamentals

*Source: [Google Search Central Documentation](https://developers.google.com/search/docs)*

---

## Table of Contents

1. [Google Search Essentials](#google-search-essentials)
2. [SEO Starter Guide](#seo-starter-guide)
3. [How Google Search Works](#how-google-search-works)
4. [Creating Helpful Content](#creating-helpful-content)
5. [E-E-A-T Guidelines](#e-e-a-t-guidelines)

---

## Google Search Essentials

*Formerly known as Webmaster Guidelines*

The Google Search Essentials make up the core parts of what makes your web-based content eligible to appear and perform well on Google Search.

### Three Core Components

1. **Technical Requirements**: What Google needs from a web page to show it in search results
2. **Spam Policies**: Behaviors and tactics that can lead to lower ranking or omission from results
3. **Key Best Practices**: Main things that improve your site's appearance in search results

> **Important**: It doesn't cost any money to appear in Google Search results. Just because a page meets all requirements doesn't guarantee Google will crawl, index, or serve its content.

### Technical Requirements

The technical requirements cover the bare minimum that Google Search needs from a web page to show it in search results. Most sites pass these requirements without even realizing it.

### Spam Policies

The spam policies detail behaviors and tactics that can lead to a page or entire site being ranked lower or completely omitted from Google Search. Sites that focus on providing the best content and experience for people are more likely to do well.

### Key Best Practices

- **Create helpful, reliable, people-first content**
- **Use words people would search for** - place them in prominent locations (title, main heading, alt text, link text)
- **Make your links crawlable** - so Google can find other pages on your site
- **Tell people about your site** - be active in communities where you can share your services and products
- **Include other content types properly** - images, videos, structured data, JavaScript
- **Enhance how your site appears** - enable features that make sense for your site
- **Control what's indexed** - use appropriate methods if content shouldn't appear in search results

---

## SEO Starter Guide

Search Engine Optimization is about helping search engines understand your content and helping users find your site through a search engine.

### How Google Search Works

Google is a fully automated search engine that uses programs called crawlers to explore the web constantly. You usually don't need to do anything except publish your site on the web.

### Timeline for Impact

- Some changes take effect in a few hours
- Others may take several months
- Wait a few weeks to assess if work had beneficial effects
- If not satisfied, try iterating with changes

### Help Google Find Your Content

**Check if you're indexed**: Use `site:yourwebsite.com` search operator to see if you're in the index.

**How Google discovers pages**:
- Through links from other pages it already crawled
- From sitemaps you submit
- Natural discovery over time

### Organize Your Site

#### Use Descriptive URLs

Good: `https://www.example.com/pets/cats.html`

Bad: `https://www.example.com/2/6772756D707920636174`

#### Group Similar Pages in Directories

Example:
- `/policies/return-policy.html` (seldom changes)
- `/promotions/new-promos.html` (changes frequently)

Google learns crawl frequency based on these patterns.

#### Reduce Duplicate Content

- Having duplicate content is NOT a spam violation
- But it can be a bad user experience
- Google chooses a canonical URL for each piece of content
- Consider using `rel="canonical"` or redirects

### Make Your Site Interesting and Useful

**Content Attributes**:
- Text is easy-to-read and well organized
- Content is unique (don't copy others)
- Content is up-to-date
- Content is helpful, reliable, and people-first

#### Expect Readers' Search Terms

Users might search differently:
- Some might search "charcuterie"
- Others might search "cheese board"

Don't worry about anticipating every variation—Google's language matching is sophisticated.

#### Link to Relevant Resources

- Links help users and search engines discover content
- Write good anchor text that describes the linked page
- Use `nofollow` for links to untrusted content
- Add nofollow automatically to user-generated content

### Influence How Your Site Looks in Google Search

#### Title Links

- The headline part of the search result
- Use unique, descriptive `<title>` elements
- Include site name/brand concisely
- Avoid keyword stuffing

#### Snippets

- The description shown below the title link
- Sourced from page content or meta description
- Write unique, descriptive meta descriptions
- Keep them relevant to the page

### Optimize Images

- Add high-quality images near relevant text
- Use descriptive alt text
- Place images in context of relevant content

### Optimize Videos

- Create high-quality video content
- Embed on standalone pages near relevant text
- Write descriptive titles and descriptions

### Promote Your Website

- Social media promotion
- Community engagement
- Word of mouth (most effective and lasting)
- Offline promotion (business cards, newsletters)

### Things NOT to Focus On

| Myth | Reality |
|------|---------|
| Keywords meta tag | Google doesn't use it |
| Keyword stuffing | Against spam policies |
| Domain name keywords | Hardly any ranking effect beyond breadcrumbs |
| Exact TLD (.com vs .org) | Doesn't matter unless targeting specific country |
| Content length | No magic "ideal" length |
| Semantic heading order | Doesn't matter to Google |
| E-A-T as a ranking factor | It's not a direct ranking factor |

---

## How Google Search Works

Google Search works in three main stages:

### Stage 1: Crawling

- Google downloads text, images, and videos from pages
- Uses automated programs called crawlers
- URLs discovered through links, sitemaps
- Googlebot uses algorithmic process to determine what to crawl and how often
- Renders JavaScript using recent version of Chrome

**Crawling can be blocked by**:
- Server problems
- Network issues
- robots.txt rules

### Stage 2: Indexing

- Google analyzes what the page is about
- Processes textual content, key tags, attributes
- Determines canonical URL for duplicate content
- Collects signals about content (language, location, usability)
- Stores information in the Google index

**Indexing issues**:
- Low quality content
- Robots meta rules disallowing indexing
- Website design making indexing difficult

### Stage 3: Serving Results

- When user searches, Google searches the index for matching pages
- Returns highest quality, most relevant results
- Relevancy determined by hundreds of factors (location, language, device)
- Different features appear based on query type

**Why indexed pages might not appear**:
- Content is irrelevant to users' queries
- Quality of content is low
- Robots meta rules prevent serving

---

## Creating Helpful Content

Google's automated ranking systems prioritize helpful, reliable information created to benefit people.

### Self-Assessment Questions

#### Content and Quality

- Does it provide original information, reporting, research, or analysis?
- Is it comprehensive?
- Does it provide insightful analysis beyond the obvious?
- Does it avoid simply copying or rewriting sources?
- Is the main heading descriptive and helpful?
- Is it the sort of page you'd bookmark or recommend?
- Does it provide substantial value compared to other pages?
- Is it produced well (not sloppy or hastily)?

#### Expertise Questions

- Does it present information in a trustworthy way?
- Is the site well-trusted or recognized as an authority?
- Is the content written by someone who knows the topic well?
- Are there easily-verified factual errors?

### People-First Content

Ask yourself:

1. Do you have an intended audience that would find the content useful?
2. Does content demonstrate first-hand expertise and depth of knowledge?
3. Does your site have a primary purpose or focus?
4. Will someone leave feeling they learned enough about a topic?
5. Will someone leave feeling they had a satisfying experience?

### Search Engine-First Content (Avoid This!)

Warning signs:

- Content primarily made to attract search engine visits
- Producing lots of content on many topics hoping some performs well
- Using extensive automation to produce content
- Mainly summarizing what others have said without adding value
- Writing about trending topics you don't typically cover
- Readers need to search again for better information
- Writing to a specific word count (Google has no preferred count!)
- Changing dates to seem "fresh" without substantial changes

---

## E-E-A-T Guidelines

**E-E-A-T**: Experience, Expertise, Authoritativeness, Trustworthiness

### Trust is Most Important

The others contribute to trust, but content doesn't need to demonstrate all of them.

### YMYL Topics

"Your Money or Your Life" - Topics that could significantly impact:
- Health
- Financial stability
- Safety
- Welfare and well-being of society

These topics require even stronger E-E-A-T signals.

### The "Who, How, Why" Framework

#### Who (created the content)

- Is it clear who authored the content?
- Do pages have bylines?
- Do bylines link to author information?
- What is the author's background and expertise?

#### How (the content was created)

- For reviews: How many products tested? What were results?
- For AI-generated content: Is use disclosed?
- Are you explaining why automation was useful?

#### Why (was the content created)

**Good**: Created primarily to help people
**Bad**: Created primarily to attract search engine visits

> Using automation to produce content for the primary purpose of manipulating search rankings is a spam policy violation.

---

## Quick Reference Checklist

### Technical Essentials
- [ ] Site is crawlable (no blocking in robots.txt for important pages)
- [ ] Pages are indexable (no noindex on important pages)
- [ ] Site uses HTTPS
- [ ] Mobile-friendly design
- [ ] Fast page loading

### Content Essentials
- [ ] Unique, helpful content on each page
- [ ] Descriptive, unique `<title>` elements
- [ ] Descriptive meta descriptions
- [ ] Proper heading hierarchy
- [ ] Alt text on images

### Best Practices
- [ ] Internal linking between relevant pages
- [ ] External links to authoritative sources
- [ ] Author information on articles
- [ ] Contact information available
- [ ] About page explaining site purpose

---

*Source: https://developers.google.com/search/docs/fundamentals*
