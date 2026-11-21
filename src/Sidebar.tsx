import {
  LayoutDashboard,
  Image,
  PawPrint,
  Map,
  Bell,
  ClipboardCheck,
  BarChart2,
} from "lucide-react";

import { NavLink } from "react-router-dom";

const navigation = [
  {
    name: "Dashboard",
    icon: LayoutDashboard,
    path: "/",
  },
  {
    name: "Image Processing",
    icon: Image,
    path: "/processing",
  },
  {
    name: "Tiger Database",
    icon: PawPrint,
    path: "/tigers",
  },
  {
    name: "Movement & Map",
    icon: Map,
    path: "/movement",
  },
  {
    name: "Alerts",
    icon: Bell,
    path: "/alerts",
  },
  {
    name: "Human Review",
    icon: ClipboardCheck,
    path: "/review",
  },
  {
    name: "Model Performance",
    icon: BarChart2,
    path: "/model",
  },
];

export default function Sidebar() {
  return (
    <aside className="flex min-h-screen w-64 flex-col border-r border-white/10 bg-[#0c1914] p-5">
      {/* BRAND */}
      <div className="mb-10">
        <h1 className="text-2xl font-bold tracking-tight">
          Van<span className="text-emerald-400">Netra</span>
        </h1>
        <p className="mt-1 text-[11px] font-medium uppercase tracking-widest text-emerald-400/60">
          Wildlife Intelligence
        </p>
        <p className="mt-0.5 text-[10px] text-white/30">
          Pench Tiger Reserve · AI Platform
        </p>
      </div>

      {/* NAV */}
      <nav className="space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm transition ${
                  isActive
                    ? "bg-emerald-400/10 text-emerald-300 font-medium"
                    : "text-white/55 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <Icon size={17} />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* STATUS */}
      <div className="mt-auto pt-10">
        <div className="rounded-xl border border-emerald-400/10 bg-emerald-400/5 p-4">
          <p className="text-[10px] uppercase tracking-widest text-white/30">
            System Status
          </p>
          <div className="mt-3 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-white/60">Backend Connected</span>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            <span className="text-xs text-white/60">Model V2 Loaded</span>
          </div>
          <p className="mt-3 text-[10px] text-white/20 leading-relaxed">
            Van Netra V2 · mAP50 91.89%
          </p>
        </div>
      </div>
    </aside>
  );
}
