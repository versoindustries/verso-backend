import { useEffect, useState } from 'react';
import { VersoContext } from '../types';

export const useVersoContext = () => {
    const [context, setContext] = useState<VersoContext | null>(null);

    useEffect(() => {
        if (window.versoContext) {
            setContext(window.versoContext);
        } else {
            console.warn('VersoContext not found on window object');
        }
    }, []);

    return context;
};
