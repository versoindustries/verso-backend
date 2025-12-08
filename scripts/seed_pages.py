from app import create_app, db
from app.models import Page

app = create_app()

def seed_pages():
    with app.app_context():
        # About Us Content
        about_content = """
<div class="section-spacer"></div>

<!-- Hero Section -->
<section id="hero-image" class="hero-section">
    <div class="image-container">
        <img src="/static/images/hero-about.jpg" alt="Custom Business Website">
        <div class="image-overlay"></div>
        <div class="hero-content">
            <h1>About Us</h1>
            <p>We architect Sovereign Monoliths—Python/SQL systems that run on commodity hardware, keep auth/content/scheduling in-house, and let founders sleep through DDoS headlines.</p>
        </div>
    </div>
</section>

<div class="small-spacer"></div>

<!-- Our Vision Section -->
<section id="our-vision" class="vision">
    <div class="container">
        <div class="row vision-row">
            <div class="col-md-6 vision-text">
                <h2>Our Vision: Digital Sovereignty</h2>
                <p>We reject rental economics and hype-driven architectures. Verso designs systems that can be deployed to a $5 VPS, a factory floor Jetson, or a classified enclave—with the same code. The objective: founders own their margins, their data, and their uptime.</p>
            </div>
            <div class="col-md-6 vision-image">
                <div class="image-set">
                    <img src="/static/images/vision-image1.jpg" alt="Connected Ecosystem">
                </div>
            </div>
        </div>
    </div>
</section>

<div class="small-spacer"></div>

<!-- Meet Our Team Section -->
<section id="team" class="team">
    <div class="container">
        <h2>Meet Our Team – The Innovators Behind Verso Industries</h2>
        <p>We ship boring, durable software so operators can run profitable businesses.</p>
        <div class="row team-row">
            <div class="col-md-6">
                <article class="team-card">
                    <img src="/static/images/Michael-CEO.jpg" alt="Michael Zimmerman">
                    <h3>Michael Zimmerman</h3>
                    <h4>Chief Executive Officer</h4>
                    <p>Michael leads the Sovereign Monolith Protocol. Background: information systems, product design, and the refusal to outsource core infrastructure. He sets the bar for unit-economics-first engineering and ships architectures that run for a decade, not a quarter.</p>
                </article>
            </div>
            <div class="small-spacer"></div>
            <div class="col-md-6">
                <article class="team-card">
                    <img src="/static/images/jacob.jpg" alt="Jacob Godina">
                    <h3>Jacob Godina</h3>
                    <h4>Developer/Videographer</h4>
                    <p>Jacob runs delivery and narrative. He pairs AI/video craft with disciplined ops to keep releases lean, observable, and on-message. The mandate: clarity, speed, and zero trend-chasing dependencies.</p>
                </article>
            </div>
        </div>
    </div>
</section>

<div class="small-spacer"></div>

<!-- Our Mission Section -->
<section id="mission" class="mission">
    <div class="mission-background">
        <img src="/static/images/mission-background.jpg" alt="Digital and Physical Transformation">
    </div>
    <div class="mission-content">
        <h2>Our Mission</h2>
        <p>Build fixed-cost, Lindy-grade software so operators keep their margins intact. Eliminate vendor lock-in, hydration bugs, and surprise cloud bills. Deliver systems that can be air-gapped, audited, and trusted.</p>
    </div>
</section>

<div class="small-spacer"></div>

<!-- Commitment to Quality and Innovation Section -->
<section id="commitment" class="commitment">
    <div class="container">
        <h2>Commitment to Quality and Innovation</h2>
        <p>Our bar is boring reliability: predictable deploys, deterministic migrations, and server-rendered truth. We innovate where it reduces cost or cognitive load—not to chase release notes.</p>
        <div class="row commitment-row">
            <div class="col-md-4">
                <article class="commitment-item">
                    <i class="fas fa-lightbulb fa-2x"></i>
                    <h3>Innovation</h3>
                    <p>Innovation is scoped to cost and stability gains, not novelty.</p>
                </article>
            </div>
            <div class="col-md-4">
                <article class="commitment-item">
                    <i class="fas fa-check-circle fa-2x"></i>
                    <h3>Quality Standards</h3>
                    <p>We prioritize maintainability, auditability, and clear ownership of every dependency.</p>
                </article>
            </div>
            <div class="col-md-4">
                <article class="commitment-item">
                    <i class="fas fa-leaf fa-2x"></i>
                    <h3>Sustainability</h3>
                    <p>Fixed-cost deployments and minimal external services keep operations sustainable.</p>
                </article>
            </div>
        </div>
    </div>
</section>

<div class="small-spacer"></div>

<!-- Vision for the Future Section -->
<section id="future-vision" class="future-vision">
    <div class="future-vision-content">
        <h2>A Vision for the Future</h2>
        <p>We see a web rebuilt on durable stacks and owned data. Verso will keep shipping the monoliths, the runbooks, and the proofs that fixed-cost architecture wins.</p>
        <p>Choose sovereignty over hype. Keep your platform, your customers, and your margins.</p>
    </div>
</section>

<div class="small-spacer"></div>

<section class="community-section">
    <div class="community-container">
        <h2>Support the Mission</h2>
        <p>If the Sovereign Monolith Protocol trims your cloud bill or restores your sanity, keep it sustainable.</p>
        <a class="btn btn-primary" href="https://github.com/sponsors/versoindustries" target="_blank" rel="noopener">Donate via GitHub Sponsors</a>
    </div>
</section>
        """

        page = Page.query.filter_by(slug='about').first()
        if not page:
            page = Page(
                slug='about',
                title='About Us',
                html_content=about_content,
                meta_description='Verso Industries builds sovereign, fixed-cost software systems.',
                is_published=True
            )
            db.session.add(page)
            print("Seeded 'about' page.")
        else:
            print("'about' page already exists.")

        # Services Page (Placeholder)
        services_content = """
<div class="section-spacer"></div>
<div class="container">
    <h1>Our Services</h1>
    <p>Coming soon...</p>
</div>
        """
        page = Page.query.filter_by(slug='services').first()
        if not page:
            page = Page(
                slug='services',
                title='Services',
                html_content=services_content,
                meta_description='Our Services',
                is_published=True
            )
            db.session.add(page)
            print("Seeded 'services' page.")
        else:
            print("'services' page already exists.")

        db.session.commit()

if __name__ == '__main__':
    seed_pages()
