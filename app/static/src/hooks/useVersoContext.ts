import { useEffect, useState } from 'react';
import { VersoContext } from '../types';

export const useVersoContext = () => {
    // Initialize with the global context if available to avoid a null first render
    const [context, setContext] = useState<VersoContext | null>(() => {
        if (typeof window !== 'undefined' && window.versoContext) {
            return window.versoContext;
        }
        return null;
    });

    useEffect(() => {
        if (window.versoContext) {
            setContext(window.versoContext);
        } else {
            console.warn('VersoContext not found on window object');
        }
    }, []);

    return context;
};
