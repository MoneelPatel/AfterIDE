/**
 * AfterIDE - Submission Types
 * 
 * TypeScript type definitions for submission-related data structures.
 */

export enum SubmissionStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  UNDER_REVIEW = 'under_review'
}

export enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
  REVIEWER = 'reviewer'
}

export interface UserSummary {
  id: string;
  username: string;
  role: UserRole;
}

export interface FileSummary {
  id: string;
  filename: string;
  filepath: string;
  language?: string;
  content?: string;  // Add file content for reviewers
}

export interface Submission {
  id: string;
  title: string;
  description?: string;
  file_id: string;
  user_id: string;
  reviewer_id?: string;
  status: SubmissionStatus;
  review_comments?: string;
  review_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  submitted_at: string;
  reviewed_at?: string;
  user: UserSummary;
  reviewer?: UserSummary;
  file: FileSummary;
}

export interface SubmissionCreate {
  title: string;
  description?: string;
  file_id?: string;
  file_path?: string;
  reviewer_username?: string;
}

export interface SubmissionUpdate {
  title?: string;
  description?: string;
}

export interface SubmissionReview {
  status: SubmissionStatus;
  review_comments?: string;
  review_metadata?: Record<string, any>;
}

export interface SubmissionListResponse {
  submissions: Submission[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface SubmissionStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  under_review: number;
}

export interface SubmissionFilters {
  page?: number;
  per_page?: number;
  status_filter?: SubmissionStatus;
} 