"use client";

import { RoleKey, RoleState } from "@/lib/types/warRoom";
import { RoleCard } from "./RoleCard";

interface RoleGridProps {
  roles: Record<RoleKey, RoleState>;
}

const ROLE_ORDER: RoleKey[] = [
  "Intel Officer",
  "Scout",
  "Risk Officer",
  "Quant Lead",
  "Strategist",
  "Execution Officer",
];

export function RoleGrid({ roles }: RoleGridProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {ROLE_ORDER.map((roleKey) => (
        <RoleCard key={roleKey} role={roles[roleKey]} />
      ))}
    </div>
  );
}

