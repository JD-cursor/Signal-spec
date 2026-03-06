const API_BASE = "http://localhost:8000/api";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, options);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export type Stats = {
  total_posts: number;
  analyzed: number;
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
  by_subreddit: Record<string, number>;
};

export type Trends = {
  posts_per_week: { week: string; count: number }[];
  categories_over_time: { week: string; category: string; count: number }[];
};

export type Post = {
  id: string;
  subreddit: string;
  title: string;
  selftext: string;
  author: string;
  score: number;
  num_comments: number;
  url: string;
  created_utc: number;
  collected_at: number;
  summary: string | null;
  category: string | null;
  severity: string | null;
  has_existing_solution: boolean | null;
  existing_solution_notes: string | null;
  willingness_to_pay: string | null;
  relevance_tags: string[];
  analyzed_at: number | null;
  favorite?: Favorite | null;
};

export type PostsResponse = {
  posts: Post[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
};

export type Favorite = {
  id: number;
  post_id: string;
  kanban_status: string;
  notes: string;
  favorited_at: number;
  updated_at: number;
};

export const api = {
  getStats: () => fetchJson<Stats>("/stats"),
  getTrends: () => fetchJson<Trends>("/trends"),
  getPosts: (params: Record<string, string | number>) => {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== "" && v !== undefined) qs.set(k, String(v));
    }
    return fetchJson<PostsResponse>(`/posts?${qs}`);
  },
  getPost: (id: string) => fetchJson<Post>(`/posts/${id}`),
  addFavorite: (postId: string) =>
    fetchJson<Favorite>(`/posts/${postId}/favorite`, { method: "POST" }),
  removeFavorite: (postId: string) =>
    fetchJson<{ detail: string }>(`/posts/${postId}/favorite`, { method: "DELETE" }),
  getFavorites: () => fetchJson<Record<string, (Post & Favorite)[]>>("/favorites"),
  updateFavorite: (id: number, data: { kanban_status?: string; notes?: string }) =>
    fetchJson<Favorite>(`/favorites/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
};
