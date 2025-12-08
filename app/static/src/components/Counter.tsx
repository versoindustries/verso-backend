import { useState } from 'react'
import { Button } from './ui/button'

export default function Counter({ initialCount = 0 }: { initialCount?: number }) {
    const [count, setCount] = useState(initialCount)

    return (
        <div className="p-4 border rounded-lg shadow-sm bg-white dark:bg-gray-800">
            <h3 className="text-lg font-medium mb-2">React Counter</h3>
            <div className="flex items-center gap-4">
                <Button
                    variant="outline"
                    onClick={() => setCount(c => c - 1)}
                >
                    -
                </Button>
                <span className="text-2xl font-bold w-8 text-center">{count}</span>
                <Button
                    variant="default"
                    onClick={() => setCount(c => c + 1)}
                >
                    +
                </Button>
            </div>
        </div>
    )
}
