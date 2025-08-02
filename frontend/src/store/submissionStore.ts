/**
 * AfterIDE - Submission Store
 * 
 * Zustand store for managing submission state and operations.
 */

import { create } from 'zustand';
import { apiService } from '../services/api';
import { getUserSessionId } from '../utils/session';
import {
  Submission,
  SubmissionCreate,
  SubmissionReview,
  SubmissionListResponse,
  SubmissionStats,
  SubmissionStatus,
  SubmissionFilters,
  UserSummary
} from '../types/submissions';

interface SubmissionState {
  // State
  submissions: Submission[];
  currentSubmission: Submission | null;
  stats: SubmissionStats | null;
  availableReviewers: UserSummary[];
  loading: boolean;
  error: string | null;
  filters: SubmissionFilters;
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };

  // Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setCurrentSubmission: (submission: Submission | null) => void;
  setFilters: (filters: Partial<SubmissionFilters>) => void;
  
  // API Actions
  fetchSubmissions: (filters?: SubmissionFilters) => Promise<void>;
  fetchPendingSubmissions: () => Promise<void>;
  fetchSubmission: (id: string) => Promise<void>;
  createSubmission: (data: SubmissionCreate) => Promise<Submission | null>;
  reviewSubmission: (id: string, review: SubmissionReview) => Promise<Submission | null>;
  updateSubmission: (id: string, data: Partial<SubmissionCreate>) => Promise<Submission | null>;
  deleteSubmission: (id: string) => Promise<boolean>;
  fetchStats: () => Promise<void>;
  fetchAvailableReviewers: () => Promise<void>;
  
  // Utility Actions
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  submissions: [],
  currentSubmission: null,
  stats: null,
  availableReviewers: [],
  loading: false,
  error: null,
  filters: {
    page: 1,
    per_page: 10,
  },
  pagination: {
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0,
  },
};

// Helper function to get auth token
const getAuthToken = (): string | null => {
  return localStorage.getItem('authToken');
};

export const useSubmissionStore = create<SubmissionState>((set, get) => ({
  ...initialState,

  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setCurrentSubmission: (submission) => set({ currentSubmission: submission }),
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters }
  })),

  fetchSubmissions: async (filters?: SubmissionFilters) => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const currentFilters = filters || get().filters;
      const response = await apiService.getSubmissions(token, currentFilters) as SubmissionListResponse;
      
      set({
        submissions: response.submissions || [],
        pagination: {
          page: response.page,
          per_page: response.per_page,
          total: response.total,
          total_pages: response.total_pages,
        },
        loading: false,
        error: null
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch submissions');
      set({ loading: false });
    }
  },

  fetchPendingSubmissions: async () => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await apiService.getPendingSubmissions(token) as { submissions: Submission[] };
      
      set({
        submissions: response.submissions || [],
        loading: false,
        error: null
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch pending submissions');
      set({ loading: false });
    }
  },

  fetchSubmission: async (id: string) => {
    const { setLoading, setError, setCurrentSubmission } = get();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await apiService.getSubmission(token, id) as Submission;
      
      setCurrentSubmission(response);
      set({ loading: false, error: null });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch submission');
      set({ loading: false });
    }
  },

  createSubmission: async (data: SubmissionCreate) => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return null;
      }

      // If data has file_path instead of file_id, convert it
      let submissionData = data;
      if ('file_path' in data && !data.file_id) {
        // Get file information by path
        const fileInfo = await apiService.getFileByPath(token, data.file_path as string) as {
          file_id: string;
          filename: string;
          filepath: string;
          language: string;
        };
        
        // Create new submission data with file_id
        submissionData = {
          ...data,
          file_id: fileInfo.file_id
        };
      }

      const response = await apiService.createSubmission(token, submissionData) as Submission;
      
      set({ loading: false, error: null });
      return response;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create submission');
      set({ loading: false });
      return null;
    }
  },

  reviewSubmission: async (id: string, review: SubmissionReview) => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return null;
      }

      const response = await apiService.reviewSubmission(token, id, review) as Submission;
      
      set({ loading: false, error: null });
      return response;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to review submission');
      set({ loading: false });
      return null;
    }
  },

  updateSubmission: async (id: string, data: Partial<SubmissionCreate>) => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return null;
      }

      const response = await apiService.updateSubmission(token, id, data) as Submission;
      
      set({ loading: false, error: null });
      return response;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update submission');
      set({ loading: false });
      return null;
    }
  },

  deleteSubmission: async (id: string) => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return false;
      }

      await apiService.deleteSubmission(token, id);
      
      set({ loading: false, error: null });
      return true;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to delete submission');
      set({ loading: false });
      return false;
    }
  },

  fetchStats: async () => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await apiService.getSubmissionStats(token) as SubmissionStats;
      
      set({
        stats: response,
        loading: false,
        error: null
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch stats');
      set({ loading: false });
    }
  },

  fetchAvailableReviewers: async () => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await apiService.getAvailableReviewers(token) as { reviewers: UserSummary[] };
      
      set({
        availableReviewers: response.reviewers || [],
        loading: false,
        error: null
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch reviewers');
      set({ loading: false });
    }
  },

  clearError: () => set({ error: null }),
  reset: () => set(initialState),
})); 