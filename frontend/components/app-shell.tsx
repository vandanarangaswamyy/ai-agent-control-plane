"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import {
  ArrowRightLeft,
  BarChart3,
  GitBranch,
  History,
  LayoutDashboard,
  NotebookText,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const navigation = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "Agents", icon: Users },
  { href: "/runs", label: "Runs", icon: History },
  { href: "/approvals", label: "Approvals", icon: ShieldCheck },
  { href: "/evaluations", label: "Evaluations", icon: BarChart3 },
  { href: "/evaluations/compare", label: "Compare", icon: ArrowRightLeft },
  { href: "/deployments", label: "Deployments", icon: GitBranch },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-[1600px] gap-0 lg:px-4 lg:py-4">
        <aside className="hidden w-72 shrink-0 lg:flex lg:flex-col">
          <div className="sticky top-4 flex h-[calc(100vh-2rem)] flex-col rounded-2xl border bg-card px-4 py-5 shadow-soft">
            <div className="mb-6 flex items-center gap-3 px-2">
              <div className="rounded-xl bg-primary p-2 text-primary-foreground">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold leading-none">AI Agent Control Plane</p>
                <p className="text-xs text-muted-foreground">Dashboard</p>
              </div>
            </div>

            <nav className="flex flex-col gap-1">
              {navigation.map((item) => {
                const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
                const Icon = item.icon;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-primary text-primary-foreground shadow-soft"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="mt-auto rounded-xl border bg-muted/40 p-4">
              <Badge variant="secondary" className="mb-2">
                Runtime + safety + evals
              </Badge>
              <p className="text-xs leading-5 text-muted-foreground">
                Operational views for agent versions, runs, approvals, evaluations, and deployment history.
              </p>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 border-b bg-background/90 backdrop-blur lg:top-4 lg:rounded-t-2xl lg:border-x lg:border-t">
            <div className="flex items-center justify-between px-4 py-3 lg:px-6">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-primary p-2 text-primary-foreground lg:hidden">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold">AI Agent Control Plane</p>
                  <p className="text-xs text-muted-foreground">Operational dashboard</p>
                </div>
              </div>
              <div className="hidden items-center gap-2 lg:flex">
                <Badge variant="outline">Frontend MVP</Badge>
                <Badge variant="secondary">Next.js 15</Badge>
              </div>
            </div>
            <nav className="flex gap-2 overflow-x-auto border-t px-3 py-2 lg:hidden">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium",
                      active
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </header>

          <main className="flex-1 px-4 py-6 lg:border-x lg:border-b lg:px-6">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
