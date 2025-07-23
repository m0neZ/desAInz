// @flow
import React from 'react';
import { motion } from 'framer-motion';

/**
 * Reusable button styled for the admin dashboard.
 */

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
    <motion.button
      className={`inline-flex items-center justify-center rounded-md bg-blue-600 px-3 sm:px-4 py-1 sm:py-2 text-white focus:outline-none focus:ring ${className}`}
      whileTap={{ scale: 0.95 }}
      aria-label={ariaLabel}
      {...props}
    >
      {children}
    </motion.button>
  );
}
