"use client";

import { RoleKey, RoleState, ROLE_NAME_MAP } from "@/lib/types/warRoom";
import { RoleCardPro } from "../pro/RoleCardPro";

interface RoleGridProps {
  roles: Record<RoleKey, RoleState>;
}

// 固定的角色順序（使用 RoleKey）
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
      {ROLE_ORDER.map((roleKey) => {
        const role = roles[roleKey];
        if (!role) {
          console.warn(`[RoleGrid] Role ${roleKey} not found in state`);
          return null;
        }
        return <RoleCardPro key={roleKey} role={role} />;
      })}
    </div>
  );
}

