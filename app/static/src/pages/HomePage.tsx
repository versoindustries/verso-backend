import React, { useEffect, useState } from 'react';
import { useVersoContext } from '../hooks/useVersoContext';
import { ArrowRight, Lock, Database, FileText, Mail, Shield, Server, Box, Terminal, Code } from 'lucide-react';
import ImageGallery from '../components/features/interactive/ImageGallery';

const HomePage: React.FC = () => {
    const context = useVersoContext();
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setIsVisible(true);
    }, []);

    const galleryImages = [
        { src: "/static/images/gallery/VersoIndustries-Social-Dashboard.jpg", alt: "Verso dashboard screenshot" },
        { src: "/static/images/gallery/DumpsterDudes.jpg", alt: "Verso booking experience" },
        { src: "/static/images/gallery/ZNH-Mockup.jpg", alt: "UTC-safe calendar mockup" },
        { src: "/static/images/gallery/nwauto.jpg", alt: "Inventory landing page" },
        { src: "/static/images/gallery/Notus-Auto-Sales-Mockup.jpg", alt: "SSR marketing page" },
        { src: "/static/images/gallery/cprism.jpg", alt: "Content engine view" },
        { src: "/static/images/gallery/GarageCafe-Mockup.jpg", alt: "Service showcase page" },
        { src: "/static/images/gallery/rockymtnburial.jpg", alt: "Static-resilient memorial site" }
    ];

    if (!context) return null;

    return (
        <div className={`verso-homepage ${isVisible ? 'verso-animate-slide-up' : ''}`}>
            {/* Hero Section */}
            <section className="verso-hero">
                <div className="verso-hero__bg">
                    <img src="/static/images/hero-bg.jpg" alt="Hero Background" className="verso-hero__bg-image" />
                    <div className="verso-hero__bg-overlay"></div>
                </div>
                <div className="verso-hero__content">
                    <h1 className="verso-hero__title verso-animate-slide-up">
                        Ship Sovereign Software
                    </h1>
                    <p className="verso-hero__subtitle verso-animate-slide-up verso-animate-delay-200">
                        Verso Backend is an opinionated Flask + SQL monolith that keeps your auth, content, and scheduling under one roof.
                    </p>
                    <div className="verso-hero__actions verso-animate-slide-up verso-animate-delay-400">
                        <a href="https://github.com/versoindustries/verso-backend" target="_blank" rel="noopener noreferrer" className="verso-hero__btn verso-hero__btn--primary">
                            <Code className="verso-hero__btn-icon" /> Get the Code
                        </a>
                        <a href="#features" className="verso-hero__btn verso-hero__btn--secondary">
                            Explore Features
                        </a>
                    </div>
                </div>
            </section>

            <div className="verso-section-spacer"></div>

            {/* Complexity Containment Field */}
            <section className="verso-feature-section verso-feature-section--gradient">
                <div className="verso-feature-section__inner">
                    <div className="verso-feature-section__content">
                        <h2 className="verso-feature-section__title">The Complexity Containment Field</h2>
                        <p className="verso-feature-section__description">
                            One repo. One database. Zero SaaS rent. Verso ships finished truths to the browser and keeps latency inside the box.
                        </p>
                        <ul className="verso-feature-list">
                            {[
                                { icon: Lock, text: "Identity & Access Core: Own your user table and RBAC—no MAU tax." },
                                { icon: FileText, text: "Sovereign Narrative Engine: First-party CMS for posts and pages." },
                                { icon: Database, text: "Single Latency Domain: SQL joins instead of N+1 API calls." },
                                { icon: Server, text: "Fixed-Cost Hosting: Runs quietly on $5–$20 VPS or on-prem edge boxes." }
                            ].map((item, index) => (
                                <li key={index} className="verso-feature-list__item">
                                    <item.icon className="verso-feature-list__icon" />
                                    <span className="verso-feature-list__text">{item.text}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="verso-feature-section__visual">
                        <div className="verso-visual-card">
                            <Terminal className="verso-visual-card__icon" />
                        </div>
                        <div className="verso-visual-card">
                            <Database className="verso-visual-card__icon" />
                        </div>
                        <div className="verso-visual-card">
                            <Shield className="verso-visual-card__icon" />
                        </div>
                        <div className="verso-visual-card">
                            <Box className="verso-visual-card__icon" />
                        </div>
                    </div>
                </div>
            </section>

            <div className="verso-section-spacer"></div>

            {/* Gallery Section */}
            <section className="verso-gallery-section">
                <div className="verso-gallery-section__inner">
                    <h2 className="verso-section-title">Gallery</h2>
                    <ImageGallery
                        images={galleryImages}
                        columns={4}
                        gap={16}
                        lightbox={true}
                        lazyLoad={true}
                    />
                </div>
            </section>

            <div className="verso-section-spacer"></div>

            {/* Modules Grid */}
            <section id="features" className="verso-modules-section">
                <div className="verso-modules-section__inner">
                    <h2 className="verso-section-title">Modules of Sovereignty</h2>
                    <p className="verso-section-subtitle">Each module is a subscription you no longer pay for:</p>

                    <div className="verso-modules-grid">
                        {[
                            { icon: Lock, title: "Identity & Access Core", desc: "Own your auth table, roles, and decorators. No per-MAU tax." },
                            { icon: Database, title: "SQL Ground Truth", desc: "Server-side joins keep latency and consistency in one place." },
                            { icon: FileText, title: "Sovereign Narrative Engine", desc: "Publish content with the built-in CMS; marketing moves without SaaS gates." },
                            { icon: Mail, title: "Signals Not Spam", desc: "Email hooks for notifications and resets—no external message rent." },
                            { icon: ArrowRight, title: "Admin Command", desc: "Role-aware dashboards for governance without extra dashboards-in-a-box." },
                            { icon: Server, title: "Fixed-Cost Deploy", desc: "Deploy to VPS/Heroku/Dokku or on-prem edge with the same code." },
                            { icon: Box, title: "Bounded Contexts", desc: "Blueprint modularity without the microservice overhead." }
                        ].map((feature, idx) => (
                            <div key={idx} className="verso-module-card">
                                <feature.icon className="verso-module-card__icon" />
                                <h3 className="verso-module-card__title">{feature.title}</h3>
                                <p className="verso-module-card__description">{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <div className="verso-section-spacer"></div>

            {/* Call to Action */}
            <section className="verso-cta-section">
                <div className="verso-cta-section__inner">
                    <h2 className="verso-cta-section__title">Declare Independence</h2>
                    <p className="verso-cta-section__description">
                        Spin up the Sovereign Monolith locally. Use it, fork it, or keep it air-gapped. The prize is sovereignty.
                    </p>
                    <a href="https://github.com/versoindustries/verso-backend" target="_blank" rel="noopener noreferrer" className="verso-cta-section__btn">
                        Start Building Now
                    </a>
                </div>
            </section>

            <div className="verso-section-spacer"></div>
        </div>
    );
};

export default HomePage;
