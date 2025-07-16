import React from 'react';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Accessible label for screen readers. Falls back to the
   * button's children when not provided.
   */
  ariaLabel?: string;
}

export function Button({
  children,
  ariaLabel,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-white ${className}`}
      aria-label={ariaLabel}
      {...props}
    >
      {children}
    </button>
  );
}
