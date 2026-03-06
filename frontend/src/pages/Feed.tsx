import { useEffect, useState, useCallback } from "react";
import { api, type Post, type PostsResponse } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Heart, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";

const CATEGORY_COLORS: Record<string, string> = {
  missing_product: "bg-orange-100 text-orange-800",
  tooling_gap: "bg-violet-100 text-violet-800",
  workflow_friction: "bg-cyan-100 text-cyan-800",
  integration_gap: "bg-pink-100 text-pink-800",
  price_complaint: "bg-yellow-100 text-yellow-800",
  other: "bg-gray-100 text-gray-800",
};

const SEVERITY_DOT: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-yellow-500",
  low: "bg-green-500",
};

export default function Feed() {
  const [data, setData] = useState<PostsResponse | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [subreddit, setSubreddit] = useState("all");
  const [category, setCategory] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [favorited, setFavorited] = useState<Set<string>>(new Set());

  const load = useCallback(() => {
    const params: Record<string, string | number> = { page, per_page: 20 };
    if (search) params.search = search;
    if (subreddit !== "all") params.subreddit = subreddit;
    if (category !== "all") params.category = category;
    if (severity !== "all") params.severity = severity;
    api.getPosts(params).then(setData);
  }, [page, search, subreddit, category, severity]);

  useEffect(() => {
    load();
  }, [load]);

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleFavorite = async (post: Post) => {
    try {
      if (favorited.has(post.id)) {
        await api.removeFavorite(post.id);
        setFavorited((prev) => {
          const next = new Set(prev);
          next.delete(post.id);
          return next;
        });
      } else {
        await api.addFavorite(post.id);
        setFavorited((prev) => new Set(prev).add(post.id));
      }
    } catch {
      // 409 = already favorited, still toggle UI
    }
  };

  if (!data) return <div className="text-muted-foreground">Loading...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Feed</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Discover pain points from Reddit
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Search posts..."
          className="w-60"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <Select
          value={subreddit}
          onValueChange={(v) => {
            setSubreddit(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Subreddit" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All subreddits</SelectItem>
            {data.posts
              .map((p) => p.subreddit)
              .filter((v, i, a) => a.indexOf(v) === i)
              .sort()
              .map((s) => (
                <SelectItem key={s} value={s}>
                  r/{s}
                </SelectItem>
              ))}
          </SelectContent>
        </Select>
        <Select
          value={category}
          onValueChange={(v) => {
            setCategory(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All categories</SelectItem>
            <SelectItem value="missing_product">Missing product</SelectItem>
            <SelectItem value="tooling_gap">Tooling gap</SelectItem>
            <SelectItem value="workflow_friction">Workflow friction</SelectItem>
            <SelectItem value="integration_gap">Integration gap</SelectItem>
            <SelectItem value="price_complaint">Price complaint</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={severity}
          onValueChange={(v) => {
            setSeverity(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All severity</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Post cards */}
      <div className="max-w-3xl space-y-4">
        {data.posts.map((post) => {
          const isExpanded = expanded.has(post.id);
          const isFav = favorited.has(post.id);
          return (
            <Card key={post.id} className="shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="pt-5 space-y-3">
                {/* Summary */}
                <p className="font-medium leading-snug">{post.summary}</p>

                {/* Meta row */}
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <Badge variant="secondary" className="font-normal">
                    r/{post.subreddit}
                  </Badge>
                  {post.category && (
                    <Badge
                      className={`font-normal border-none ${CATEGORY_COLORS[post.category] ?? CATEGORY_COLORS.other}`}
                    >
                      {post.category.replace(/_/g, " ")}
                    </Badge>
                  )}
                  {post.severity && (
                    <span className="flex items-center gap-1">
                      <span
                        className={`w-2 h-2 rounded-full ${SEVERITY_DOT[post.severity] ?? ""}`}
                      />
                      <span className="text-muted-foreground capitalize">
                        {post.severity}
                      </span>
                    </span>
                  )}
                  {post.willingness_to_pay && post.willingness_to_pay !== "unlikely" && (
                    <Badge
                      variant="outline"
                      className="font-normal text-green-700 border-green-300"
                    >
                      WTP: {post.willingness_to_pay}
                    </Badge>
                  )}
                  {post.has_existing_solution && (
                    <Badge variant="outline" className="font-normal text-amber-700 border-amber-300">
                      Has solution
                    </Badge>
                  )}
                  <span className="text-muted-foreground ml-auto">
                    {post.score} pts · {post.num_comments} comments
                  </span>
                </div>

                {/* Expand/collapse */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleExpand(post.id)}
                    className="text-muted-foreground"
                  >
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 mr-1" />
                    ) : (
                      <ChevronDown className="w-4 h-4 mr-1" />
                    )}
                    {isExpanded ? "Less" : "More"}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleFavorite(post)}
                    className={isFav ? "text-red-500" : "text-muted-foreground"}
                  >
                    <Heart
                      className="w-4 h-4 mr-1"
                      fill={isFav ? "currentColor" : "none"}
                    />
                    {isFav ? "Saved" : "Save"}
                  </Button>
                </div>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="border-t pt-3 space-y-2 text-sm">
                    <p className="font-medium">{post.title}</p>
                    {post.selftext && (
                      <p className="text-muted-foreground whitespace-pre-wrap">
                        {post.selftext}
                      </p>
                    )}
                    {post.existing_solution_notes && (
                      <div className="bg-amber-50 rounded-md p-3 text-amber-900">
                        <span className="font-medium">Existing solutions: </span>
                        {post.existing_solution_notes}
                      </div>
                    )}
                    {post.relevance_tags && post.relevance_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {post.relevance_tags.map((tag) => (
                          <Badge key={tag} variant="secondary" className="text-xs font-normal">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                    <a
                      href={post.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-blue-600 hover:underline"
                    >
                      View on Reddit <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Pagination */}
      {data.total_pages > 1 && (
        <div className="flex items-center gap-4 justify-center">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {data.page} of {data.total_pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= data.total_pages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
