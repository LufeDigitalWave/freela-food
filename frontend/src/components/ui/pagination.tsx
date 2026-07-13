"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const totalPages = Math.ceil(total / pageSize);

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-3 pt-4">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="rounded-full h-9 w-9 p-0"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      <span className="text-sm text-gray-500">
        Página <span className="font-medium text-gray-900">{page}</span> de{" "}
        <span className="font-medium text-gray-900">{totalPages}</span>
      </span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="rounded-full h-9 w-9 p-0"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}
