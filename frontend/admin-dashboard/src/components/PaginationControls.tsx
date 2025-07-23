// @flow
import React from 'react';

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
  return (
    <div className="flex items-center space-x-2">
      <button
        type="button"
        className="px-2 py-1 border focus:outline-none focus:ring"
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
        className="px-2 py-1 border focus:outline-none focus:ring"
        disabled={maxPage != null && page >= maxPage}
        onClick={() => onPageChange(page + 1)}
        aria-label="Next page"
      >
        Next
      </button>
    </div>
  );
}
