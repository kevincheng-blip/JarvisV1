/**
 * useDoctrinePatches Hook
 * 
 * React Query hooks for Doctrine Patch & Rollout system.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type {
  DoctrinePatch,
  DoctrinePatchSummary,
  CreateDoctrinePatchRequest,
  ApprovePatchRequest,
  RejectPatchRequest,
  DeployPatchRequest,
  RevertPatchRequest,
} from "../types/doctrinePatch";

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
      return await api.getDoctrinePatchQueue(status);
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
      return await api.getDoctrinePatch(patchId);
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
      return await api.createDoctrinePatch(request);
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
      const result = await api.runDoctrinePatchSim(patchId);
      return result.patch || result;
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
      const result = await api.approveDoctrinePatch(patchId, request);
      return result.patch || result;
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
      return await api.rejectDoctrinePatch(patchId, request);
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
      const result = await api.deployDoctrinePatch(patchId, request);
      return result.patch || result;
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
      const result = await api.revertDoctrinePatch(patchId, request);
      return result.patch || result;
    },
    onSuccess: (_, { patchId }) => {
      queryClient.invalidateQueries({ queryKey: ["patchQueue"] });
      queryClient.invalidateQueries({ queryKey: ["patch", patchId] });
    },
  });
}
