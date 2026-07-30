import { Disc3 } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

interface CoverArtProps {
  coverArt: string | null;
  alt: string;
  className?: string;
}

/**
 * 封面图。cover_art 为空或加载失败时回退到占位图标。
 * 图片经后端 /api/v1/subsonic/cover 代理，前端无需持有 Subsonic 凭据。
 */
export function CoverArt({ coverArt, alt, className }: CoverArtProps) {
  const [errored, setErrored] = useState(false);

  if (!coverArt || errored) {
    return (
      <div
        className={cn(
          "flex items-center justify-center bg-accent text-muted-foreground",
          className,
        )}
      >
        <Disc3 className="h-7 w-7" />
      </div>
    );
  }

  return (
    <img
      src={`/api/v1/subsonic/cover/${encodeURIComponent(coverArt)}`}
      alt={alt}
      loading="lazy"
      onError={() => setErrored(true)}
      className={cn("object-cover", className)}
    />
  );
}
