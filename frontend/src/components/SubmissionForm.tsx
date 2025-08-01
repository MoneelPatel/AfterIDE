/**
 * AfterIDE - Submission Form Component
 * 
 * Form component for creating new code submissions for review.
 */

import React, { useState, useEffect } from 'react';
import { useSubmissionStore } from '../store/submissionStore';
import { SubmissionCreate, UserSummary } from '../types/submissions';

interface SubmissionFormProps {
  filePath: string;
  fileName: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const SubmissionForm: React.FC<SubmissionFormProps> = ({
  filePath,
  fileName,
  onSuccess,
  onCancel
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [reviewerUsername, setReviewerUsername] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showReviewerDropdown, setShowReviewerDropdown] = useState(false);
  
  const { createSubmission, availableReviewers, fetchAvailableReviewers, error, clearError } = useSubmissionStore();

  useEffect(() => {
    fetchAvailableReviewers();
  }, [fetchAvailableReviewers]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) {
      return;
    }

    setIsSubmitting(true);
    clearError();

    try {
      const submissionData: SubmissionCreate = {
        title: title.trim(),
        description: description.trim() || undefined,
        file_path: filePath,
        reviewer_username: reviewerUsername.trim() || undefined
      };

      await createSubmission(submissionData);
      
      // Reset form
      setTitle('');
      setDescription('');
      setReviewerUsername('');
      
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      console.error('Failed to create submission:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReviewerSelect = (username: string) => {
    setReviewerUsername(username);
    setShowReviewerDropdown(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Submit for Review
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Submitting: <span className="font-mono text-gray-800 dark:text-gray-200">{fileName}</span>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Title *
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Brief description of your changes"
              required
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Detailed description of your changes (optional)"
            />
          </div>

          <div className="relative">
            <label htmlFor="reviewer" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Assign Reviewer (optional)
            </label>
            <div className="relative">
              <input
                type="text"
                id="reviewer"
                value={reviewerUsername}
                onChange={(e) => setReviewerUsername(e.target.value)}
                onFocus={() => setShowReviewerDropdown(true)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Type reviewer username or select from dropdown"
              />
              <button
                type="button"
                onClick={() => setShowReviewerDropdown(!showReviewerDropdown)}
                className="absolute right-2 top-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
            
            {showReviewerDropdown && availableReviewers.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
                {availableReviewers.map((reviewer) => (
                  <button
                    key={reviewer.id}
                    type="button"
                    onClick={() => handleReviewerSelect(reviewer.username)}
                    className="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-900 dark:text-white"
                  >
                    <div className="flex items-center justify-between">
                      <span>{reviewer.username}</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                        {reviewer.role}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {error && (
            <div className="text-red-600 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Submitting...' : 'Submit for Review'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SubmissionForm; 