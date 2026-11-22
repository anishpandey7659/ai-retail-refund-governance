"use client";

import React, { useState, type ReactNode } from "react";
import { Sidebar } from "./layout/Sidebar";
import { Header } from "./layout/Header";
import { useAppData } from "@/context/app-context";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

interface AppShellProps {
  title: string;
  description: string;
  children: ReactNode;
}

export function AppShell({ title, description, children }: AppShellProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { toast, clearToast } = useAppData();

  return (
    <div className="min-h-screen bg-[#F8F7F4] text-[#252525]">
      <div className="mx-auto flex min-h-screen max-w-[2500px]">
        {/* Desktop Sidebar */}
        <div className="hidden lg:block lg:w-[260px] lg:shrink-0 lg:border-r lg:border-[#E8E6E1]">
          <div className="sticky top-0 h-screen overflow-y-auto">
            <Sidebar />
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 flex lg:hidden">
            <div
              className="fixed inset-0 bg-[#1D1B1A]/40 backdrop-blur-xs transition-opacity"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative flex w-full max-w-xs flex-1 flex-col bg-[#F1F0EC] shadow-2xl">
              <div className="absolute top-4 right-4 z-10">
                <button
                  type="button"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex h-9 w-9 items-center justify-center rounded-full border border-[#D9D5CF] bg-white text-[#555048]"
                >
                  <X size={16} />
                </button>
              </div>
              <Sidebar onCloseMobile={() => setMobileMenuOpen(false)} />
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 flex flex-col">
          <Header
            title={title}
            description={description}
            onOpenMobileMenu={() => setMobileMenuOpen(true)}
          />

          <div className="flex-1 p-4 sm:p-6 lg:p-8">{children}</div>
        </main>
      </div>

      {/* Floating Toast Notification */}
      {toast && (
        <div className="fixed bottom-5 right-5 z-50 flex max-w-md items-center justify-between gap-3 rounded-2xl border border-[#E2DDD5] bg-[#252525] px-4 py-3 text-sm text-[#F8F7F4] shadow-[0_18px_45px_rgba(34,29,25,0.18)] animate-in fade-in-0 slide-in-from-bottom-2 duration-200">
          <div className="flex items-center gap-2.5">
            {toast.type === "success" && (
              <CheckCircle2 size={16} className="text-[#A2BA99] shrink-0" />
            )}
            {toast.type === "error" && (
              <AlertCircle size={16} className="text-[#E7A69A] shrink-0" />
            )}
            {toast.type === "info" && (
              <Info size={16} className="text-[#C4B99F] shrink-0" />
            )}
            <span className="text-xs sm:text-sm font-medium">{toast.message}</span>
          </div>

          <button
            type="button"
            onClick={clearToast}
            className="ml-2 text-[#A8A49C] hover:text-white transition cursor-pointer"
            aria-label="Dismiss toast"
          >
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  );
}
