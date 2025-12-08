import React from 'react';
import { useVersoContext } from '../../hooks/useVersoContext';

const Footer: React.FC = () => {
    const context = useVersoContext();
    if (!context) return null;

    const { urls, year, version } = context;

    return (
        <footer className="bg-black/80 backdrop-blur-md border-t border-white/10 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    <div className="col-span-1 md:col-span-1">
                        <span className="font-neon-heavy text-2xl text-white tracking-widest uppercase">Verso</span>
                        <p className="mt-4 text-sm text-gray-400">
                            The Sovereign Monolith Protocol. Ship finished truths.
                        </p>
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-gray-200 uppercase tracking-wider mb-4">Navigation</h3>
                        <ul className="space-y-2">
                            <li><a href={urls.index} className="text-gray-400 hover:text-white text-sm transition-colors">Home</a></li>
                            <li><a href={urls.about} className="text-gray-400 hover:text-white text-sm transition-colors">About</a></li>
                            <li><a href={urls.services} className="text-gray-400 hover:text-white text-sm transition-colors">Services</a></li>
                            <li><a href={urls.blogIndex} className="text-gray-400 hover:text-white text-sm transition-colors">Blog</a></li>
                        </ul>
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-gray-200 uppercase tracking-wider mb-4">Connect</h3>
                        <ul className="space-y-2">
                            <li><a href={urls.contact} className="text-gray-400 hover:text-white text-sm transition-colors">Contact Us</a></li>
                            <li><a href="https://github.com/versoindustries" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white text-sm transition-colors">GitHub</a></li>
                        </ul>
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-gray-200 uppercase tracking-wider mb-4">Language</h3>
                        <div className="flex space-x-4">
                            <a href={urls.setLanguageEn} className="text-gray-400 hover:text-white text-sm transition-colors">English</a>
                            <span className="text-gray-600">|</span>
                            <a href={urls.setLanguageEs} className="text-gray-400 hover:text-white text-sm transition-colors">Español</a>
                        </div>
                    </div>
                </div>

                <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center">
                    <p className="text-sm text-gray-400">
                        &copy; <span id="current-year">{year}</span> Verso Industries. All rights reserved.
                    </p>
                    <p className="text-sm text-gray-500 mt-2 md:mt-0">
                        Empowered by our own backend! v{version}
                    </p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
