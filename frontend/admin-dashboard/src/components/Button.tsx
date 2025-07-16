import React from 'react';

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement>;

export function Button({ children, className = '', ...props }: ButtonProps) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-white ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
