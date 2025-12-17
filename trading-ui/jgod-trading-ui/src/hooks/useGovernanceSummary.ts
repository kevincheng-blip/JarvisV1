import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { GovernanceSummary } from "../types";

export const useGovernanceSummary = () =>
  useQuery<GovernanceSummary>({
    queryKey: ["governance-summary"],
    queryFn: async () => {
      const res = await api.getGovernanceSummary();
      return res;
    },
    staleTime: 30000,
    refetchOnWindowFocus: false,
  });


