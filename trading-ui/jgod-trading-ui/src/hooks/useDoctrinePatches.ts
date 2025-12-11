/**
 * useDoctrinePatches Hook
 * 
 * React Query hooks for Doctrine Patch & Rollout system.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import type {
  DoctrinePatch,
  DoctrinePatchSummary,
  CreateDoctrinePatchRequest,
  ApprovePatchRequest,
  RejectPatchRequest,
  DeployPatchRequest,
  RevertPatchRequest,
} from "../types/doctrinePatch";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch patch queue (default: PENDING_REVIEW + APPROVED)
 * If no status provided, returns all active patches (PENDING_SIMULATION, PENDING_REVIEW, APPROVED)
 */
export function usePatchQueue(
  status?: string | null,
  limit: number = 50,
  enabled: boolean = true
) {
  return useQuery<DoctrinePatchSummary[]>({
    queryKey: ["patchQueue", { status, limit }],
    queryFn: async () => {
      const response = await apiClient.get<DoctrinePatchSummary[]>(
        `/api/v1/doctrine/patches/queue`,
        {
          params: {
            status: status || undefined,
            limit,
          },
        }
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Auto-refetch every 60 seconds
    refetchOnWindowFocus: false,
    enabled,
  });
}

/**
 * Fetch a specific patch by ID
 */
export function usePatch(patchId: string | null, enabled: boolean = true) {
  return useQuery<DoctrinePatch>({
    queryKey: ["patch", patchId],
    queryFn: async () => {
      if (!patchId) throw new Error("Patch ID is required");
      const response = await apiClient.get<DoctrinePatch>(
        `/api/v1/doctrine/patches/${patchId}`
      );
      return response.data;
    },
    staleTime: 30000,
    refetchOnWindowFocus: false,
    enabled: enabled && !!patchId,
  });
}

/**
 * Create a new patch
 */
export function useCreatePatch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: CreateDoctrinePatchRequest) => {
      const response = await apiClient.post<DoctrinePatch>(
        `/api/v1/doctrine/patches`,
        request
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patchQueue"] });
    },
  });
}

/**
 * Run Rule Sim for a patch
 */
export function useRunRuleSim() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (patchId: string) => {
      const response = await apiClient.post<DoctrinePatch>(
        `/api/v1/doctrine/patches/${patchId}/run-sim`
      );
      return response.data;
    },
    onSuccess: (_, patchId) => {
      queryClient.invalidateQueries({ queryKey: ["patchQueue"] });
      queryClient.invalidateQueries({ queryKey: ["patch", patchId] });
    },
  });
}

/**
 * Approve a patch
 */
export function useApprovePatch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ patchId, request }: { patchId: string; request: ApprovePatchRequest }) => {
      const response = await apiClient.post<DoctrinePatch>(
        `/api/v1/doctrine/patches/${patchId}/approve`,
        request
      );
      return response.data;
    },
    onSuccess: (_, { patchId }) => {
      queryClient.invalidateQueries({ queryKey: ["patchQueue"] });
      queryClient.invalidateQueries({ queryKey: ["patch", patchId] });
    },
  });
}

/**
 * Reject a patch
 */
export function useRejectPatch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ patchId, request }: { patchId: string; request: RejectPatchRequest }) => {
      const response = await apiClient.post<DoctrinePatch>(
        `/api/v1/doctrine/patches/${patchId}/reject`,
        request
      );
      return response.data;
    },
    onSuccess: (_, { patchId }) => {
      queryClient.invalidateQueries({ queryKey: ["patchQueue"] });
      queryClient.invalidateQueries({ queryKey: ["patch", patchId] });
    },
  });
}

/**
 * Deploy a patch
 */
export function useDeployPatch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ patchId, request }: { patchId: string; request: DeployPatchRequest }) => {
      const response = await apiClient.post<DoctrinePatch>(
        `/api/v1/doctrine/patches/${patchId}/deploy`,
        request
      );
      return response.data;
    },
    onSuccess: (_, { patchId }) => {
      queryClient.invalidateQueries({ queryKey: ["patchQueue"] });
      queryClient.invalidateQueries({ queryKey: ["patch", patchId] });
    },
  });
}

/**
 * Revert a patch
 */
export function useRevertPatch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ patchId, request }: { patchId: string; request: RevertPatchRequest }) => {
      const response = await apiClient.post<DoctrinePatch>(
        `/api/v1/doctrine/patches/${patchId}/revert`,
        request
      );
      return response.data;
    },
    onSuccess: (_, { patchId }) => {
      queryClient.invalidateQueries({ queryKey: ["patchQueue"] });
      queryClient.invalidateQueries({ queryKey: ["patch", patchId] });
    },
  });
}
