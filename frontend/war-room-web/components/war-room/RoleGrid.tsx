"use client";

import { RoleKey, RoleState } from "@/lib/types/warRoom";
import { RoleCardPro } from "../pro/RoleCardPro";

interface RoleGridProps {
  roles: Record<RoleKey, RoleState>;
}

const ROLE_ORDER: RoleKey[] = [
  "intel_officer",
  "scout",
  "risk_officer",
  "quant_lead",
  "strategist",
  "execution_officer",
];

export function RoleGrid({ roles }: RoleGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {ROLE_ORDER.map((roleKey) => (
        <RoleCardPro key={roleKey} role={roles[roleKey]} />
      ))}
    </div>
  );
}

