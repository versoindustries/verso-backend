export interface User {
    isAuthenticated: boolean;
    firstName?: string;
    roles?: string[];
}

export interface BusinessConfig {
    site_name: string;
    primary_color: string;
    secondary_color: string;
    accent_color: string;
    font_family: string;
    ga4_tracking_id?: string;
    // Add other config keys as needed
}

export interface Urls {
    index: string;
    about: string;
    services: string;
    contact: string;
    login: string;
    register: string;
    logout: string;
    // Blog
    blogIndex: string;
    blogManage: string;
    blogNew: string;
    // Protected
    employeeDashboard: string;
    messaging: string;
    adminDashboard: string;
    // Language
    setLanguageEn: string;
    setLanguageEs: string;
}

export interface VersoContext {
    user: User;
    config: BusinessConfig;
    urls: Urls;
    unreadNotificationsCount: number;
    year: number;
    version: string;
}

declare global {
    interface Window {
        versoContext: VersoContext;
    }
}
