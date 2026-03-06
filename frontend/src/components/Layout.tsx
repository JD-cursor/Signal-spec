import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, Rss, Columns3 } from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard", icon: BarChart3 },
  { to: "/feed", label: "Feed", icon: Rss },
  { to: "/board", label: "Board", icon: Columns3 },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 flex items-center h-14 gap-8">
          <span className="font-semibold text-lg tracking-tight">Signal Scanner</span>
          <div className="flex gap-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent"
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                {label}
              </NavLink>
            ))}
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
