"use client";

import React from "react";
import { ChevronRight, LogOut, Menu } from "lucide-react";
import { useAppData } from "@/context/app-context";

interface HeaderProps {
  title: string;
  description: string;
  onOpenMobileMenu?: () => void;
}

export function Header({ title, description, onOpenMobileMenu }: HeaderProps) {
  const { user, signOut } = useAppData();
  const initials = user?.name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="border-b border-[#E8E6E1] bg-[#F8F7F4]/90 px-4 py-4 backdrop-blur-xs sm:px-6 lg:px-8">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {onOpenMobileMenu && (
            <button
              type="button"
              onClick={onOpenMobileMenu}
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#E8E6E1] bg-white text-[#5E5A54] hover:bg-[#F1F0EC] lg:hidden"
              aria-label="Open navigation menu"
            >
              <Menu size={18} />
            </button>
          )}
          <div>
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-[#77746E]">
              <span>Marlow Commerce</span>
              <ChevronRight size={11} className="text-[#A2A09C]" />
              <span className="text-[#252525]">{title}</span>
            </div>
            <h1 className="mt-1.5 text-2xl font-semibold tracking-[-0.03em] text-[#252525] sm:text-3xl">
              {title}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2.5 rounded-full border border-[#E5E1DA] bg-white px-2.5 py-1.5 shadow-xs">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#E7E0D4] text-[11px] font-semibold text-[#4B443E]">
            {initials}
          </div>
          <div className="hidden text-left sm:block">
            <div className="max-w-40 truncate text-xs font-semibold leading-tight text-[#252525]">
              {user?.name}
            </div>
            <div className="max-w-40 truncate text-[10px] leading-tight text-[#77746E]">
              {user?.email}
            </div>
          </div>
          <button
            type="button"
            onClick={() => void signOut()}
            aria-label="Sign out"
            title="Sign out"
            className="ml-1 flex h-8 w-8 items-center justify-center rounded-full text-[#77746E] transition hover:bg-[#F1F0EC] hover:text-[#252525]"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>

      <p className="mt-2 max-w-3xl text-xs text-[#77746E] sm:text-sm">
        {description}
      </p>
    </header>
  );
}
