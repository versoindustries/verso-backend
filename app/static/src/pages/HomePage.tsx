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
    // content loops over static items, urls not used for linking yet or hardcoded
    // const { urls } = context;

    return (
        <div className={`transition-opacity duration-1000 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
            {/* Hero Section */}
            <section className="relative h-[80vh] flex items-center justify-center overflow-hidden">
                <div className="absolute inset-0 z-0">
                    <img src="/static/images/hero-bg.jpg" alt="Hero Background" className="w-full h-full object-cover opacity-60" />
                    <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/50 to-black/90"></div>
                </div>
                <div className="relative z-10 text-center px-4 max-w-4xl mx-auto">
                    <h1 className="font-neon-heavy text-5xl md:text-7xl text-white tracking-widest uppercase mb-6 drop-shadow-neon animate-slide-up">
                        Ship Sovereign Software
                    </h1>
                    <p className="text-xl md:text-2xl text-gray-200 mb-8 font-light animate-slide-up animation-delay-200">
                        Verso Backend is an opinionated Flask + SQL monolith that keeps your auth, content, and scheduling under one roof.
                    </p>
                    <div className="flex flex-col sm:flex-row justify-center gap-4 animate-slide-up animation-delay-400">
                        <a href="https://github.com/versoindustries/verso-backend" target="_blank" rel="noopener noreferrer" className="btn-primary flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg font-bold uppercase tracking-wider transition-all transform hover:scale-105 shadow-lg hover:shadow-blue-500/50">
                            <Code className="w-5 h-5" /> Get the Code
                        </a>
                        <a href="#features" className="btn-secondary flex items-center justify-center gap-2 bg-transparent border-2 border-white/20 hover:border-white/50 text-white px-8 py-4 rounded-lg font-bold uppercase tracking-wider transition-all hover:bg-white/10">
                            Explore Features
                        </a>
                    </div>
                </div>
            </section>

            <div className="h-20"></div>

            {/* Complexity Containment Field */}
            <section className="py-20 px-4 bg-gradient-to-r from-gray-900 to-black relative overflow-hidden">
                <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                    <div className="order-2 lg:order-1">
                        <h2 className="text-3xl md:text-4xl font-neon-heavy text-white mb-6">The Complexity Containment Field</h2>
                        <p className="text-lg text-gray-300 mb-6">
                            One repo. One database. Zero SaaS rent. Verso ships finished truths to the browser and keeps latency inside the box.
                        </p>
                        <ul className="space-y-4">
                            {[
                                { icon: Lock, text: "Identity & Access Core: Own your user table and RBAC—no MAU tax." },
                                { icon: FileText, text: "Sovereign Narrative Engine: First-party CMS for posts and pages." },
                                { icon: Database, text: "Single Latency Domain: SQL joins instead of N+1 API calls." },
                                { icon: Server, text: "Fixed-Cost Hosting: Runs quietly on $5–$20 VPS or on-prem edge boxes." }
                            ].map((item, index) => (
                                <li key={index} className="flex items-start gap-3 bg-white/5 p-4 rounded-lg hover:bg-white/10 transition-colors">
                                    <item.icon className="w-6 h-6 text-blue-500 flex-shrink-0 mt-1" />
                                    <span className="text-gray-200">{item.text}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="order-1 lg:order-2 grid grid-cols-2 gap-4">
                        <div className="bg-blue-900/20 p-8 rounded-2xl border border-blue-500/20 backdrop-blur-sm flex items-center justify-center aspect-square">
                            <Terminal className="w-16 h-16 text-blue-400" />
                        </div>
                        <div className="bg-purple-900/20 p-8 rounded-2xl border border-purple-500/20 backdrop-blur-sm flex items-center justify-center aspect-square mt-8">
                            <Database className="w-16 h-16 text-purple-400" />
                        </div>
                        <div className="bg-teal-900/20 p-8 rounded-2xl border border-teal-500/20 backdrop-blur-sm flex items-center justify-center aspect-square -mt-8">
                            <Shield className="w-16 h-16 text-teal-400" />
                        </div>
                        <div className="bg-indigo-900/20 p-8 rounded-2xl border border-indigo-500/20 backdrop-blur-sm flex items-center justify-center aspect-square">
                            <Box className="w-16 h-16 text-indigo-400" />
                        </div>
                    </div>
                </div>
            </section>

            <div className="h-20"></div>

            {/* Gallery Section */}
            <section className="py-20 px-4">
                <div className="max-w-7xl mx-auto">
                    <h2 className="text-3xl md:text-4xl font-neon-heavy text-white mb-12 text-center">Gallery</h2>
                    <ImageGallery
                        images={galleryImages}
                        columns={4}
                        gap={16}
                        lightbox={true}
                        lazyLoad={true}
                    />
                </div>
            </section>

            <div className="h-20"></div>

            {/* Modules Grid */}
            <section id="features" className="py-20 px-4 bg-gray-900/50">
                <div className="max-w-7xl mx-auto">
                    <h2 className="text-3xl md:text-4xl font-neon-heavy text-white mb-4 text-center">Modules of Sovereignty</h2>
                    <p className="text-center text-gray-400 mb-12">Each module is a subscription you no longer pay for:</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            { icon: Lock, title: "Identity & Access Core", desc: "Own your auth table, roles, and decorators. No per-MAU tax." },
                            { icon: Database, title: "SQL Ground Truth", desc: "Server-side joins keep latency and consistency in one place." },
                            { icon: FileText, title: "Sovereign Narrative Engine", desc: "Publish content with the built-in CMS; marketing moves without SaaS gates." },
                            { icon: Mail, title: "Signals Not Spam", desc: "Email hooks for notifications and resets—no external message rent." },
                            { icon: ArrowRight, title: "Admin Command", desc: "Role-aware dashboards for governance without extra dashboards-in-a-box." },
                            { icon: Server, title: "Fixed-Cost Deploy", desc: "Deploy to VPS/Heroku/Dokku or on-prem edge with the same code." },
                            { icon: Box, title: "Bounded Contexts", desc: "Blueprint modularity without the microservice overhead." }
                        ].map((feature, idx) => (
                            <div key={idx} className="bg-black/40 border border-white/10 p-8 rounded-xl hover:border-blue-500/50 hover:bg-black/60 transition-all group">
                                <feature.icon className="w-10 h-10 text-blue-500 mb-4 group-hover:scale-110 transition-transform" />
                                <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
                                <p className="text-gray-400">{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <div className="h-20"></div>

            {/* Call to Action */}
            <section className="py-20 px-4">
                <div className="max-w-4xl mx-auto text-center bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-white/10 p-12 rounded-2xl backdrop-blur-md">
                    <h2 className="text-3xl md:text-4xl font-neon-heavy text-white mb-6">Declare Independence</h2>
                    <p className="text-xl text-gray-300 mb-8">
                        Spin up the Sovereign Monolith locally. Use it, fork it, or keep it air-gapped. The prize is sovereignty.
                    </p>
                    <a href="https://github.com/versoindustries/verso-backend" target="_blank" rel="noopener noreferrer" className="inline-block bg-white text-black px-8 py-4 rounded-lg font-bold uppercase tracking-wider hover:bg-gray-200 transition-colors">
                        Start Building Now
                    </a>
                </div>
            </section>
            <div className="h-20"></div>
        </div>
    );
};

export default HomePage;
