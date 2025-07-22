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
        className="px-2 py-1 border"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        Prev
      </button>
      <span>
        Page {page}
        {maxPage ? ` / ${maxPage}` : ''}
      </span>
      <button
        type="button"
        className="px-2 py-1 border"
        disabled={maxPage != null && page >= maxPage}
        onClick={() => onPageChange(page + 1)}
      >
        Next
      </button>
    </div>
  );
}
