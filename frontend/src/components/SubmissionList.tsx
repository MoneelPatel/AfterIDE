/**
 * AfterIDE - Submission List Component
 * 
 * Component for displaying and managing code submissions.
 */

import React, { useEffect, useState } from 'react';
import { useSubmissionStore } from '../store/submissionStore';
import { Submission, SubmissionStatus } from '../types/submissions';
import { formatDistanceToNow } from 'date-fns';

interface SubmissionListProps {
  showPendingOnly?: boolean;
  onSubmissionClick?: (submission: Submission) => void;
}

const SubmissionList: React.FC<SubmissionListProps> = ({
  showPendingOnly = false,
  onSubmissionClick
}) => {
  const {
    submissions,
    loading,
    error,
    pagination,
    filters,
    fetchSubmissions,
    fetchPendingSubmissions,
    setFilters,
    clearError
  } = useSubmissionStore();

  const [statusFilter, setStatusFilter] = useState<SubmissionStatus | ''>('');

  useEffect(() => {
    clearError();
    if (showPendingOnly) {
      fetchPendingSubmissions();
    } else {
      fetchSubmissions({ ...filters, status_filter: statusFilter || undefined });
    }
  }, [showPendingOnly, statusFilter]);

  const handleStatusFilterChange = (status: SubmissionStatus | '') => {
    setStatusFilter(status);
    if (!showPendingOnly) {
      setFilters({ status_filter: status || undefined, page: 1 });
    }
  };

  const handlePageChange = (page: number) => {
    if (!showPendingOnly) {
      setFilters({ page });
    }
  };

  const getStatusBadge = (status: SubmissionStatus) => {
    const statusConfig = {
      [SubmissionStatus.PENDING]: {
        label: 'Pending',
        className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
      },
      [SubmissionStatus.UNDER_REVIEW]: {
        label: 'Under Review',
        className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
      },
      [SubmissionStatus.APPROVED]: {
        label: 'Approved',
        className: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
      },
      [SubmissionStatus.REJECTED]: {
        label: 'Rejected',
        className: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
      }
    };

    const config = statusConfig[status];
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
        {config.label}
      </span>
    );
  };

  const handleSubmissionClick = (submission: Submission) => {
    onSubmissionClick?.(submission);
  };

  if (loading && submissions.length === 0) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button
          onClick={() => clearError()}
          className="mt-2 text-sm text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
        >
          Try again
        </button>
      </div>
    );
  }

  if (submissions.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 dark:text-gray-500">
          <svg className="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {showPendingOnly ? 'No pending submissions' : 'No submissions found'}
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            {showPendingOnly 
              ? 'All submissions have been reviewed or are currently under review.'
              : 'Get started by submitting your first code review request.'
            }
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      {!showPendingOnly && (
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Filter by status:
          </label>
          <select
            value={statusFilter}
            onChange={(e) => handleStatusFilterChange(e.target.value as SubmissionStatus | '')}
            className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">All</option>
            <option value={SubmissionStatus.PENDING}>Pending</option>
            <option value={SubmissionStatus.UNDER_REVIEW}>Under Review</option>
            <option value={SubmissionStatus.APPROVED}>Approved</option>
            <option value={SubmissionStatus.REJECTED}>Rejected</option>
          </select>
        </div>
      )}

      {/* Submissions List */}
      <div className="space-y-3">
        {submissions.map((submission) => (
          <div
            key={submission.id}
            onClick={() => handleSubmissionClick(submission)}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
                    {submission.title}
                  </h3>
                  {getStatusBadge(submission.status)}
                </div>
                
                {submission.description && (
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-2 line-clamp-2">
                    {submission.description}
                  </p>
                )}
                
                <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                  <span>File: {submission.file.filename}</span>
                  <span>By: {submission.user.username}</span>
                  <span>
                    {formatDistanceToNow(new Date(submission.created_at), { addSuffix: true })}
                  </span>
                  {submission.reviewer && (
                    <span>Assigned to: {submission.reviewer.username}</span>
                  )}
                  {submission.reviewer && submission.reviewed_at && (
                    <span>Reviewed by: {submission.reviewer.username}</span>
                  )}
                </div>
              </div>
              
              <div className="flex items-center space-x-2 ml-4">
                <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {!showPendingOnly && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            Showing {((pagination.page - 1) * pagination.per_page) + 1} to{' '}
            {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
            {pagination.total} results
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Page {pagination.page} of {pagination.total_pages}
            </span>
            
            <button
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= pagination.total_pages}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubmissionList; 