import * as React from "react"

const variants = {
    default: "bg-blue-600 text-white hover:bg-blue-700",
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600",
    outline: "border border-gray-300 bg-transparent hover:bg-gray-100 dark:border-gray-600 dark:hover:bg-gray-800 text-gray-900 dark:text-gray-100",
    ghost: "hover:bg-gray-100 dark:hover:bg-gray-800",
}

const sizes = {
    default: "h-10 px-4 py-2",
    sm: "h-9 rounded-md px-3",
    lg: "h-11 rounded-md px-8",
    icon: "h-10 w-10",
}

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: keyof typeof variants
    size?: keyof typeof sizes
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className = "", variant = "default", size = "default", ...props }, ref) => {
        return (
            <button
                ref={ref}
                className={`inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${className}`}
                {...props}
            />
        )
    }
)
Button.displayName = "Button"

export { Button }
