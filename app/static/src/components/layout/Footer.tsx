import React from 'react';
import { useVersoContext } from '../../hooks/useVersoContext';

const Footer: React.FC = () => {
    const context = useVersoContext();
    if (!context) return null;

    const { urls, year, version } = context;

    return (
        <footer className="verso-footer">
            <div className="verso-footer__inner">
                <div className="verso-footer__grid">
                    {/* Brand Column */}
                    <div className="verso-footer__brand">
                        <span className="verso-footer__logo">Verso</span>
                        <p className="verso-footer__tagline">
                            The Sovereign Monolith Protocol. Ship finished truths.
                        </p>
                    </div>

                    {/* Navigation Column */}
                    <div className="verso-footer__column">
                        <h3 className="verso-footer__heading">Navigation</h3>
                        <ul className="verso-footer__links">
                            <li><a href={urls.index} className="verso-footer__link">Home</a></li>
                            <li><a href={urls.about} className="verso-footer__link">About</a></li>
                            <li><a href={urls.services} className="verso-footer__link">Services</a></li>
                            <li><a href={urls.blogIndex} className="verso-footer__link">Blog</a></li>
                        </ul>
                    </div>

                    {/* Connect Column */}
                    <div className="verso-footer__column">
                        <h3 className="verso-footer__heading">Connect</h3>
                        <ul className="verso-footer__links">
                            <li><a href={urls.contact} className="verso-footer__link">Contact Us</a></li>
                            <li><a href="https://github.com/versoindustries" target="_blank" rel="noopener noreferrer" className="verso-footer__link">GitHub</a></li>
                        </ul>
                    </div>

                    {/* Language Column */}
                    <div className="verso-footer__column">
                        <h3 className="verso-footer__heading">Language</h3>
                        <div className="verso-footer__languages">
                            <a href={urls.setLanguageEn} className="verso-footer__lang-link">English</a>
                            <span className="verso-footer__lang-divider">|</span>
                            <a href={urls.setLanguageEs} className="verso-footer__lang-link">Español</a>
                        </div>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="verso-footer__bottom">
                    <p className="verso-footer__copyright">
                        &copy; <span id="current-year">{year}</span> Verso Industries. All rights reserved.
                    </p>
                    <p className="verso-footer__version">
                        Empowered by our own backend! v{version}
                    </p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
