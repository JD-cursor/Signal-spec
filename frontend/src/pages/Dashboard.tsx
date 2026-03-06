import { useEffect, useState } from "react";
import { api, type Stats, type Trends } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";

const CATEGORY_COLORS: Record<string, string> = {
  missing_product: "#f97316",
  tooling_gap: "#8b5cf6",
  workflow_friction: "#06b6d4",
  integration_gap: "#ec4899",
  price_complaint: "#eab308",
  other: "#6b7280",
};

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [trends, setTrends] = useState<Trends | null>(null);

  useEffect(() => {
    api.getStats().then(setStats);
    api.getTrends().then(setTrends);
  }, []);

  if (!stats || !trends) {
    return <div className="text-muted-foreground">Loading...</div>;
  }

  const categoryData = Object.entries(stats.by_category)
    .filter(([k]) => k !== "not_relevant")
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  const severityData = Object.entries(stats.by_severity)
    .filter(([k]) => k !== null && k !== "null")
    .map(([name, count]) => ({ name, count }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Overview of discovered pain points
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-orange-50 to-pink-50 border-none shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Pain Points
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total_posts}</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-50 to-cyan-50 border-none shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Analyzed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.analyzed}</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-violet-50 to-fuchsia-50 border-none shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Top Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {categoryData[0]?.name.replace(/_/g, " ") ?? "—"}
            </div>
            <p className="text-sm text-muted-foreground">
              {categoryData[0]?.count ?? 0} posts
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">Posts Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trends.posts_per_week}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="week" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">By Category</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={categoryData} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 11 }}
                  width={120}
                  tickFormatter={(v: string) => v.replace(/_/g, " ")}
                />
                <Tooltip />
                <Bar
                  dataKey="count"
                  radius={[0, 6, 6, 0]}
                  fill="#8b5cf6"
                  barSize={24}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Severity breakdown */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">By Severity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-6">
            {severityData.map(({ name, count }) => (
              <div key={name} className="flex items-center gap-2">
                <div
                  className={`w-3 h-3 rounded-full ${
                    name === "high"
                      ? "bg-red-500"
                      : name === "medium"
                        ? "bg-yellow-500"
                        : "bg-green-500"
                  }`}
                />
                <span className="text-sm capitalize">{name}</span>
                <span className="text-sm font-semibold">{count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
