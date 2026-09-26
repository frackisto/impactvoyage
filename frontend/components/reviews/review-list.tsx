import { QuoteIcon } from "lucide-react";

import { Rating } from "@/components/common/rating";
import type { Review } from "@/types";

/** Avis clients validés (CdC § 20), en cartes. */
export function ReviewList({ reviews }: { reviews: Review[] }) {
  return (
    <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {reviews.map((review) => (
        <li key={review.id} className="flex flex-col gap-4 rounded-2xl border bg-card p-6">
          <QuoteIcon aria-hidden="true" className="size-8 text-sunset-500" />
          <blockquote className="flex-1 text-ocean-950">{review.comment}</blockquote>
          <div className="flex items-center justify-between gap-2">
            <span className="font-semibold text-ocean-900">{review.author_name}</span>
            <Rating value={review.rating} />
          </div>
        </li>
      ))}
    </ul>
  );
}
