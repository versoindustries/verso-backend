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

export interface FeatureFlags {
    ecommerceEnabled: boolean;
    bookingEnabled: boolean;
    schedulingEnabled: boolean;
}

export interface PageEditorContext {
    contentType: 'page' | 'post' | 'product' | 'static';
    contentId: number;
    canEdit: boolean;
    initialData?: ContentFields;
}

export interface ContentFields {
    title?: string;
    content?: string;
    excerpt?: string;
    metaTitle?: string;
    metaDescription?: string;
    ogTitle?: string;
    ogDescription?: string;
    ogImage?: string;
    slug?: string;
}

export interface VersoContext {
    user: User;
    config: BusinessConfig;
    urls: Urls;
    unreadNotificationsCount: number;
    featureFlags?: FeatureFlags;
    pageEditor?: PageEditorContext;
    year: number;
    version: string;
    currentLanguage: string;
}

declare global {
    interface Window {
        versoContext: VersoContext;
    }
}

