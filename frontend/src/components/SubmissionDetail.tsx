/**
 * AfterIDE - Submission Detail Component
 * 
 * Component for viewing and reviewing individual submissions.
 */

import React, { useState, useEffect } from 'react';
import { useSubmissionStore } from '../store/submissionStore';
import { Submission, SubmissionStatus, SubmissionReview } from '../types/submissions';
import { formatDistanceToNow } from 'date-fns';
import { useAuthStore } from '../store/authStore';
import CodeViewer from './CodeViewer';

interface SubmissionDetailProps {
  submission: Submission;
  onClose: () => void;
  onUpdate?: (submission: Submission) => void;
}

const SubmissionDetail: React.FC<SubmissionDetailProps> = ({
  submission,
  onClose,
  onUpdate
}) => {
  const [reviewComments, setReviewComments] = useState('');
  const [isReviewing, setIsReviewing] = useState(false);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [showCodeViewer, setShowCodeViewer] = useState(false);
  
  const { reviewSubmission, error, clearError } = useSubmissionStore();
  const { user } = useAuthStore();

  // Check if current user can review this submission
  const canReview = submission.status === SubmissionStatus.PENDING && 
                   (user?.role === 'admin' || user?.id === submission.reviewer_id);
  const isAuthor = user?.id === submission.user_id;

  useEffect(() => {
    if (submission.review_comments) {
      setReviewComments(submission.review_comments);
    }
  }, [submission]);

  const handleReview = async (status: SubmissionStatus) => {
    if (!reviewComments.trim()) {
      return;
    }

    setIsReviewing(true);
    clearError();

    const reviewData: SubmissionReview = {
      status,
      review_comments: reviewComments.trim(),
    };

    const result = await reviewSubmission(submission.id, reviewData);
    
    if (result) {
      setShowReviewForm(false);
      onUpdate?.(result);
    }
    
    setIsReviewing(false);
  };

  const getStatusBadge = (status: SubmissionStatus) => {
    const statusConfig = {
      [SubmissionStatus.PENDING]: {
        label: 'Pending Review',
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
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.className}`}>
        {config.label}
      </span>
    );
  };

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {submission.title}
              </h2>
              <div className="flex items-center space-x-4 mt-1">
                {getStatusBadge(submission.status)}
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Submitted {formatDistanceToNow(new Date(submission.created_at), { addSuffix: true })}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="overflow-y-auto max-h-[calc(90vh-120px)]">
            <div className="px-6 py-4 space-y-6">
              {/* Error Display */}
              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
                  <p className="text-red-600 dark:text-red-400">{error}</p>
                </div>
              )}

              {/* Submission Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                    Submission Details
                  </h3>
                  <dl className="space-y-2">
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Author</dt>
                      <dd className="text-sm text-gray-900 dark:text-white">{submission.user.username}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">File</dt>
                      <dd className="text-sm text-gray-900 dark:text-white">{submission.file.filename}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Language</dt>
                      <dd className="text-sm text-gray-900 dark:text-white">{submission.file.language || 'Unknown'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Assigned Reviewer</dt>
                      <dd className="text-sm text-gray-900 dark:text-white">
                        {submission.reviewer ? submission.reviewer.username : 'No reviewer assigned'}
                      </dd>
                    </div>
                    {submission.reviewer && submission.reviewed_at && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Reviewed by</dt>
                        <dd className="text-sm text-gray-900 dark:text-white">{submission.reviewer.username}</dd>
                      </div>
                    )}
                    {submission.reviewed_at && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Reviewed</dt>
                        <dd className="text-sm text-gray-900 dark:text-white">
                          {formatDistanceToNow(new Date(submission.reviewed_at), { addSuffix: true })}
                        </dd>
                      </div>
                    )}
                  </dl>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                    Description
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-md p-3">
                    {submission.description ? (
                      <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                        {submission.description}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                        No description provided
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* File Content Preview */}
              {submission.file.content && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Code Preview
                    </h3>
                    <button
                      onClick={() => setShowCodeViewer(true)}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      View Full File
                    </button>
                  </div>
                  <div className="bg-gray-900 rounded-lg overflow-hidden">
                    <div className="px-4 py-2 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
                      <span className="text-sm text-gray-300">{submission.file.filename}</span>
                      <span className="text-xs text-gray-500">
                        {submission.file.content.split('\n').length} lines
                      </span>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      <div className="overflow-x-auto">
                        <pre className="text-sm text-gray-100 font-mono">
                          <code className="block">
                            {submission.file.content.split('\n').map((line, index) => (
                              <div key={index} className="flex hover:bg-gray-800">
                                <span className="text-gray-500 text-xs px-4 py-0.5 select-none border-r border-gray-700 min-w-[3rem] text-right">
                                  {index + 1}
                                </span>
                                <span className="px-4 py-0.5 whitespace-pre">
                                  {line}
                                </span>
                              </div>
                            ))}
                          </code>
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Review Comments */}
              {submission.review_comments && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                    Review Comments
                  </h3>
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-4">
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {submission.review_comments}
                    </p>
                  </div>
                </div>
              )}

              {/* Review Form */}
              {canReview && showReviewForm && (
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
                    Review Submission
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Review Comments *
                      </label>
                      <textarea
                        value={reviewComments}
                        onChange={(e) => setReviewComments(e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                        placeholder="Provide detailed feedback on the submission..."
                        required
                      />
                    </div>
                    <div className="flex space-x-3">
                      <button
                        onClick={() => handleReview(SubmissionStatus.APPROVED)}
                        disabled={isReviewing || !reviewComments.trim()}
                        className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isReviewing ? 'Processing...' : 'Approve'}
                      </button>
                      <button
                        onClick={() => handleReview(SubmissionStatus.REJECTED)}
                        disabled={isReviewing || !reviewComments.trim()}
                        className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isReviewing ? 'Processing...' : 'Reject'}
                      </button>
                      <button
                        onClick={() => setShowReviewForm(false)}
                        disabled={isReviewing}
                        className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                {canReview && submission.status === SubmissionStatus.PENDING && !showReviewForm && (
                  <button
                    onClick={() => setShowReviewForm(true)}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    Review Submission
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Code Viewer Modal */}
      {showCodeViewer && submission.file.content && (
        <CodeViewer
          code={submission.file.content}
          language={submission.file.language || 'text'}
          filename={submission.file.filename}
          onClose={() => setShowCodeViewer(false)}
        />
      )}
    </>
  );
};

export default SubmissionDetail; 