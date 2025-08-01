/**
 * AfterIDE - Submission Store
 * 
 * Zustand store for managing submission state and operations.
 */

import { create } from 'zustand';
import { apiService } from '../services/api';
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
      const currentFilters = filters || get().filters;
      const response = await apiService.getSubmissions(currentFilters);
      
      if (response.error) {
        setError(response.error);
        return;
      }

      const data = response.data as SubmissionListResponse;
      set({
        submissions: data.submissions,
        pagination: {
          page: data.page,
          per_page: data.per_page,
          total: data.total,
          total_pages: data.total_pages,
        },
        filters: currentFilters,
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch submissions');
    } finally {
      setLoading(false);
    }
  },

  fetchPendingSubmissions: async () => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.getPendingSubmissions();
      
      if (response.error) {
        setError(response.error);
        return;
      }

      set({ submissions: response.data as Submission[] });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch pending submissions');
    } finally {
      setLoading(false);
    }
  },

  fetchSubmission: async (id: string) => {
    const { setLoading, setError, setCurrentSubmission } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.getSubmission(id);
      
      if (response.error) {
        setError(response.error);
        return;
      }

      setCurrentSubmission(response.data as Submission);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch submission');
    } finally {
      setLoading(false);
    }
  },

  createSubmission: async (data: SubmissionCreate) => {
    const { setLoading, setError, fetchSubmissions } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.createSubmission(data);
      
      if (response.error) {
        setError(response.error);
        return null;
      }

      const submission = response.data as Submission;
      
      // Refresh the submissions list
      await fetchSubmissions();
      
      return submission;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create submission');
      return null;
    } finally {
      setLoading(false);
    }
  },

  reviewSubmission: async (id: string, review: SubmissionReview) => {
    const { setLoading, setError, fetchSubmissions, setCurrentSubmission } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.reviewSubmission(id, review);
      
      if (response.error) {
        setError(response.error);
        return null;
      }

      const submission = response.data as Submission;
      
      // Update current submission if it's the one being reviewed
      const { currentSubmission } = get();
      if (currentSubmission?.id === id) {
        setCurrentSubmission(submission);
      }
      
      // Refresh the submissions list
      await fetchSubmissions();
      
      return submission;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to review submission');
      return null;
    } finally {
      setLoading(false);
    }
  },

  updateSubmission: async (id: string, data: Partial<SubmissionCreate>) => {
    const { setLoading, setError, fetchSubmissions, setCurrentSubmission } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.updateSubmission(id, data);
      
      if (response.error) {
        setError(response.error);
        return null;
      }

      const submission = response.data as Submission;
      
      // Update current submission if it's the one being updated
      const { currentSubmission } = get();
      if (currentSubmission?.id === id) {
        setCurrentSubmission(submission);
      }
      
      // Refresh the submissions list
      await fetchSubmissions();
      
      return submission;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update submission');
      return null;
    } finally {
      setLoading(false);
    }
  },

  deleteSubmission: async (id: string) => {
    const { setLoading, setError, fetchSubmissions, setCurrentSubmission } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.deleteSubmission(id);
      
      if (response.error) {
        setError(response.error);
        return false;
      }

      // Clear current submission if it's the one being deleted
      const { currentSubmission } = get();
      if (currentSubmission?.id === id) {
        setCurrentSubmission(null);
      }
      
      // Refresh the submissions list
      await fetchSubmissions();
      
      return true;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to delete submission');
      return false;
    } finally {
      setLoading(false);
    }
  },

  fetchStats: async () => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.getSubmissionStats();
      
      if (response.error) {
        setError(response.error);
        return;
      }

      set({ stats: response.data as SubmissionStats });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch stats');
    } finally {
      setLoading(false);
    }
  },

  fetchAvailableReviewers: async () => {
    const { setLoading, setError } = get();
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.getAvailableReviewers();
      
      if (response.error) {
        setError(response.error);
        return;
      }

      set({ availableReviewers: response.data as UserSummary[] });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch available reviewers');
    } finally {
      setLoading(false);
    }
  },

  clearError: () => set({ error: null }),
  reset: () => set(initialState),
})); 