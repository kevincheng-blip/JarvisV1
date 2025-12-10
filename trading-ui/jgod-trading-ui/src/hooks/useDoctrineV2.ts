/**
 * useDoctrineV2 Hook
 * 
 * Fetches Doctrine V2 sections and manages review workflow.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import type {
  DoctrineSection,
  SectionsResponse,
  VersionContentResponse,
  DiffResponse,
} from "../types/doctrineV2";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch Doctrine sections with filtering and pagination
 */
export function useDoctrineSections(
  status?: string | null,
  page: number = 1,
  pageSize: number = 50,
  enabled: boolean = true
) {
  return useQuery<SectionsResponse>({
    queryKey: ["doctrineSections", { status, page, pageSize }],
    queryFn: async () => {
      const response = await apiClient.get<SectionsResponse>(
        `/api/v2/doctrine/sections`,
        {
          params: {
            status: status || undefined,
            page,
            page_size: pageSize,
          },
        }
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
    enabled,
  });
}

/**
 * Fetch a specific Doctrine section
 */
export function useDoctrineSection(sectionId: string | null, enabled: boolean = true) {
  return useQuery<DoctrineSection>({
    queryKey: ["doctrineSection", sectionId],
    queryFn: async () => {
      if (!sectionId) throw new Error("Section ID is required");
      const response = await apiClient.get<DoctrineSection>(
        `/api/v2/doctrine/sections/${sectionId}`
      );
      return response.data;
    },
    enabled: enabled && !!sectionId,
    staleTime: 30000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Fetch version content
 */
export function useVersionContent(
  sectionId: string | null,
  versionId: string | null,
  enabled: boolean = true
) {
  return useQuery<VersionContentResponse>({
    queryKey: ["versionContent", sectionId, versionId],
    queryFn: async () => {
      if (!sectionId || !versionId) throw new Error("Section ID and Version ID are required");
      const response = await apiClient.get<VersionContentResponse>(
        `/api/v2/doctrine/sections/${sectionId}/versions/${versionId}/content`
      );
      return response.data;
    },
    enabled: enabled && !!sectionId && !!versionId,
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: false,
  });
}

/**
 * Fetch diff between two versions
 */
export function useVersionDiff(
  sectionId: string | null,
  fromVersion: string | null,
  toVersion: string | null,
  enabled: boolean = true
) {
  return useQuery<DiffResponse>({
    queryKey: ["versionDiff", sectionId, fromVersion, toVersion],
    queryFn: async () => {
      if (!sectionId || !fromVersion || !toVersion) {
        throw new Error("All parameters are required");
      }
      const response = await apiClient.get<DiffResponse>(
        `/api/v2/doctrine/sections/${sectionId}/diff`,
        {
          params: {
            from_version: fromVersion,
            to_version: toVersion,
          },
        }
      );
      return response.data;
    },
    enabled: enabled && !!sectionId && !!fromVersion && !!toVersion,
    staleTime: 60000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Mutation: Create draft
 */
export function useCreateDraft() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ sectionId, content }: { sectionId: string; content: string }) => {
      const response = await apiClient.post(`/api/v2/doctrine/sections/${sectionId}/draft`, {
        content,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctrineSections"] });
      queryClient.invalidateQueries({ queryKey: ["doctrineSection"] });
    },
  });
}

/**
 * Mutation: Submit for review
 */
export function useSubmitForReview() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (sectionId: string) => {
      const response = await apiClient.post(`/api/v2/doctrine/sections/${sectionId}/submit`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctrineSections"] });
      queryClient.invalidateQueries({ queryKey: ["doctrineSection"] });
    },
  });
}

/**
 * Mutation: Approve version
 */
export function useApproveVersion() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ sectionId, versionId }: { sectionId: string; versionId: string }) => {
      const response = await apiClient.post(
        `/api/v2/doctrine/sections/${sectionId}/approve`,
        null,
        {
          params: { version_id: versionId },
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctrineSections"] });
      queryClient.invalidateQueries({ queryKey: ["doctrineSection"] });
    },
  });
}

/**
 * Mutation: Reject version
 */
export function useRejectVersion() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ sectionId, versionId }: { sectionId: string; versionId: string }) => {
      const response = await apiClient.post(
        `/api/v2/doctrine/sections/${sectionId}/reject`,
        null,
        {
          params: { version_id: versionId },
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctrineSections"] });
      queryClient.invalidateQueries({ queryKey: ["doctrineSection"] });
    },
  });
}

/**
 * Mutation: Rollback version
 */
export function useRollbackVersion() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ sectionId, targetVersionId }: { sectionId: string; targetVersionId: string }) => {
      const response = await apiClient.post(
        `/api/v2/doctrine/sections/${sectionId}/rollback`,
        null,
        {
          params: { target_version_id: targetVersionId },
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctrineSections"] });
      queryClient.invalidateQueries({ queryKey: ["doctrineSection"] });
    },
  });
}

