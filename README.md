# Verso Backend: Your All-in-One Solution for Smarter, Affordable Web Apps

![Verso Backend Mockup](app/static/images/gallery/ZNH-Mockup.jpg)

**Verso Backend** is the ultimate Flask-based web application template that empowers businesses to launch professional, scalable websites quickly and affordably. Deployable on Heroku for just $7/month, it’s packed with ready-to-use features like secure user authentication, a powerful blogging CMS, and seamless appointment scheduling. Whether you’re a small business, startup, or growing enterprise, Verso Backend is the cost-effective, SEO-optimized solution you didn’t know you needed—until now.

## Why Choose Verso Backend?

In a digital world where every business needs a strong online presence, Verso Backend delivers everything you need in one sleek package. Say goodbye to juggling multiple tools or paying thousands for custom development. Here’s what makes Verso Backend a game-changer:

- **Launch Fast, Save Big**: Deploy a fully functional web app in days on Heroku for only $7/month—no expensive hosting or lengthy builds required.
- **SEO Supercharged**: Built-in sitemap generation, JSON-LD structured data, and server-side rendering boost your Google rankings and drive organic traffic.
- **All-in-One Features**: From secure logins to appointment booking and blogging, it’s got everything businesses need to succeed online.
- **Scalable & Flexible**: Modular design with Flask Blueprints lets you grow without limits, integrating with React, Vue, or Webflow.
- **Business-Friendly**: Streamline operations, engage customers, and cut costs with a platform designed for real-world impact.

## Powerful Features, Ready to Go

Verso Backend comes loaded with tools to simplify your digital strategy:

- **Secure User Authentication**: Easy registration, login, and password resets with role-based access (admin, user, blogger, commercial) using Flask-Login and bcrypt.
- **Dynamic Blogging CMS**: Create engaging blog posts with CKEditor’s rich text editing, perfect for driving traffic and showcasing expertise.
- **Smart Appointment Scheduling**: AppointQix, our native system, uses FullCalendar for intuitive booking with timezone support via pytz.
- **Admin Dashboard**: Manage users, roles, services, appointments, and settings from one powerful interface.
- **SEO Optimization**: Automated sitemap submission to Bing and structured data for better search visibility.
- **Image & Email Support**: Upload blog images with compression and send notifications via Flask-Mail (with plans for SendGrid integration).
- **Mobile-First Design**: Responsive Jinja2 templates and Tailwind CSS ensure your site looks great on any device.

## Who’s It For?

Verso Backend is designed for businesses ready to level up their online game without the hassle or high costs:

- **Small Businesses**: Salons, plumbers, or local shops can offer online booking and share updates via blogs—all for less than a coffee per month.
- **Startups**: Get your big idea online fast with a scalable foundation that grows with you.
- **Growing Companies**: Manage clients, publish thought leadership, and streamline operations from one platform.

## Get Started in Minutes

Ready to transform your online presence? Follow these simple steps to set up Verso Backend:

1. **Clone or Create Your Repository**:
   - Use the template on [GitHub](https://github.com/versoindustries/verso-backend) to start your own project.
   - Or clone it:  
     ```bash
     git clone https://github.com/versoindustries/verso-backend.git
     cd verso-backend
     ```

2. **Set Up Locally**:
   - Create a virtual environment and install dependencies:
     ```bash
     python -m venv env
     source env/bin/activate  # On Windows: env\Scripts\activate
     pip install -r requirements.txt
     ```
   - Configure your `.env` file with a secure key, database, and email settings:
     ```
     FLASK_APP=app
     SECRET_KEY=your_secure_random_key
     DATABASE_URL=sqlite:///mydatabase.sqlite
     MAIL_SERVER=smtp.example.com
     MAIL_PORT=587
     MAIL_USE_TLS=True
     MAIL_USERNAME=your_email
     MAIL_PASSWORD=your_password
     MAIL_DEFAULT_SENDER=your_email
     ```
   - Initialize the database and roles:
     ```bash
     python dbl.py
     flask db init
     flask db migrate
     flask db upgrade
     flask create-roles
     flask seed-business-config
     ```
   - Run the app:
     ```bash
     flask run --host=0.0.0.0 --debug
     ```
   - Visit `http://localhost:5000` to see your site in action!

3. **Deploy to Heroku**:
   - Install Heroku CLI and log in:
     ```bash
     heroku login
     ```
   - Create a Heroku app and set environment variables:
     ```bash
     heroku create your-app-name
     heroku config:set FLASK_APP=app SECRET_KEY=your_key DATABASE_URL=your_database_url
     heroku config:set MAIL_SERVER=your_mail_server MAIL_PORT=587 MAIL_USE_TLS=True
     heroku config:set MAIL_USERNAME=your_mail_username MAIL_PASSWORD=your_mail_password
     heroku config:set MAIL_DEFAULT_SENDER=your_default_sender
     ```
   - Push and migrate:
     ```bash
     git push heroku main
     heroku run flask db upgrade
     heroku run flask create-roles
     heroku run flask seed-business-config
     ```
   - Your site is live for just $7/month!

## Why Businesses Love Verso Backend

- **Cost-Effective**: Save thousands compared to other platforms and developments, while getting premium features.
- **Time-Saving**: Launch in days, not months, with pre-built tools for authentication, blogging, and scheduling.
- **SEO Advantage**: Climb search rankings with automated sitemaps and structured data.
- **Future-Proof**: Modular design and API endpoints support headless CMS or modern frameworks.
- **Community-Driven**: Join our [Discord](https://discord.gg/pBrSPbaMnM) and contribute to an open-source project under the Apache 2.0 License.

## Real-World Impact

Imagine a local salon letting customers book appointments online while sharing styling tips through a blog. Or a consulting firm managing client meetings and publishing industry insights—all from one platform. Verso Backend makes it happen, delivering happier customers and a stronger online presence.

## Support the Future of Verso Backend

Love what we’re building? Here’s how you can help:

- **Contribute**: Fork the repo, add features, and submit pull requests on [GitHub](https://github.com/versoindustries/verso-backend).
- **Sponsor**: Support development with tiers starting at $5/month via [GitHub Sponsors](https://github.com/sponsors/versoindustries) or Stripe (see below).
- **Share**: Spread the word on X (@bigmikez99z) or your favorite platforms.

## Sponsorship Tiers for Verso Backend

Support **Verso Backend**, a Flask-based open-source CMS backend with secure authentication, appointment booking, and AI-driven extensibility via Grok3. Your sponsorship fuels innovation and community growth. Choose a tier via GitHub Sponsors or Stripe.

### Community Supporter
- **Monthly Amount**: $5
- **Benefits**:
  - Name listed on GitHub Sponsors page and README.md.
  - Access to supporters-only Discord channel.
- **Description**: Ideal for open-source enthusiasts.
- **Sponsor Link**: [Sponsor Now](https://buy.stripe.com/fZu14nfiYgTYelU6Cygfu0J)

### Developer Advocate
- **Monthly Amount**: $15
- **Benefits**:
  - All Community Supporter benefits.
  - Early access to updates and beta features via email or private repository.
- **Description**: For developers tracking Verso Backend’s progress.
- **Sponsor Link**: [Sponsor Now](https://buy.stripe.com/cNi9AT6Ms8nsb9I7GCgfu0K)

### Project Patron
- **Monthly Amount**: $50
- **Benefits**:
  - All Developer Advocate benefits.
  - Personal thank-you via email or X post from @bigmikez99z.
  - Acknowledgment in documentation or blog posts.
- **Description**: For supporters making a significant impact.
- **Sponsor Link**: [Sponsor Now](https://buy.stripe.com/14A3cv0o49rwb9I1iegfu0L)

### Corporate Sponsor
- **Monthly Amount**: $6,000
- **Benefits**:
  - All Project Patron benefits.
  - Company logo on GitHub README and future website.
  - Priority queue for feature requests or bug fixes.
- **Description**: For businesses using Verso Backend in production.
- **Sponsor Link**: [Sponsor Now](https://buy.stripe.com/3cIaEX4Ek9rw6Ts6Cygfu0M)

### Strategic Partner
- **Annual Amount**: $150,000
- **Benefits**:
  - All Corporate Sponsor benefits.
  - Quarterly virtual meetings with maintainers.
  - Propose features or integrations (e.g., API endpoints).
  - Early access to new modules or AI features.
- **Description**: For organizations shaping Verso Backend’s roadmap.
- **Sponsor Link**: [Sponsor Now](https://buy.stripe.com/6oUcN51s88nsdhQ5yugfu0N)

### Premier Sponsor
- **Annual Amount**: $300,000
- **Benefits**:
  - All Strategic Partner benefits.
  - Co-branding opportunities (e.g., “Verso Backend, Powered by [Sponsor]”).
  - Dedicated development sprint for one feature per year.
  - Dedicated support channel for technical queries.
  - Naming rights for a module or feature.
- **Description**: For enterprise stakeholders integrating Verso Backend.
- **Sponsor Link**: [Sponsor Now](https://buy.stripe.com/fZu4gz6Ms1Z45Po1iegfu0O)

---

## Why Sponsor Verso Backend?

- **Innovative Technology**: Support a Flask-based CMS with Grok3 integration for AI-driven development.
- **Business Value**: Heroku-ready backend reduces development costs for web applications.
- **Community Impact**: Build a community-driven project and gain visibility.
- **Influence**: Higher tiers offer roadmap input and feature prioritization.

## Join the Community

Connect with other Verso Backend users and developers:

- **Discord**: [Join us](https://discord.gg/pBrSPbaMnM)
- **Email**: zimmermanmb99@gmail.com
- **X**: @bigmikez99z
- **Website**: Coming soon at www.versoindustries.com

## What’s Next?

Led by Michael B. Zimmerman, founder of Verso Industries, we’re building a community-driven CMS that’s affordable, powerful, and easy to use. Future plans include enhanced blogging features, robust APIs, and a Windows tool to simplify setup. Clone the repo today and start building your dream website!

---

**Verso Backend**: The smart, affordable way to power your business online. Deploy now and see the difference.

**Contributors**:
- **Michael Zimmerman**: Founder and CEO of Verso Industries, creator of HighNoon LLM and HSMN architecture, Lead Developer.
- **Jacob Godina**: President and Co-Founder of Verso Industries, contributor to code, design, and marketing.

**License**: Licensed under the [Apache License 2.0](LICENSE).