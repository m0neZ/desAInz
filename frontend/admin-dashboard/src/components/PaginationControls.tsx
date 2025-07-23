// @flow
import React from 'react';
import { motion } from 'framer-motion';

type Props = {
  page: number;
  total: number | null;
  limit: number;
  onPageChange: (newPage: number) => void;
};

export default function PaginationControls({
  page,
  total,
  limit,
  onPageChange,
}: Props) {
  const maxPage = total != null ? Math.ceil(total / limit) : null;

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'ArrowRight') {
      onPageChange(page + 1);
    }
    if (event.key === 'ArrowLeft' && page > 1) {
      onPageChange(page - 1);
    }
  };

  return (
    <motion.div
      className="flex items-center space-x-2 sm:space-x-4"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <button
        type="button"
        className="px-2 sm:px-3 py-1 sm:py-2 border focus:outline-none focus:ring"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        aria-label="Previous page"
      >
        Prev
      </button>
      <span>
        Page {page}
        {maxPage ? ` / ${maxPage}` : ''}
      </span>
      <button
        type="button"
        className="px-2 sm:px-3 py-1 sm:py-2 border focus:outline-none focus:ring"
        disabled={maxPage != null && page >= maxPage}
        onClick={() => onPageChange(page + 1)}
        aria-label="Next page"
      >
        Next
      </button>
    </motion.div>
  );
}
