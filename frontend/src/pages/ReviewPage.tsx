/**
 * AfterIDE - Review Page
 * 
 * Page for managing code submissions and reviews.
 */

import React, { useState, useEffect } from 'react';
import { useSubmissionStore } from '../store/submissionStore';
import { useAuthStore } from '../store/authStore';
import { Submission, SubmissionStatus } from '../types/submissions';
import SubmissionList from '../components/SubmissionList';
import SubmissionDetail from '../components/SubmissionDetail';
import SubmissionStats from '../components/SubmissionStats';

const ReviewPage: React.FC = () => {
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'pending'>('all');
  
  const { user } = useAuthStore();
  const { fetchSubmissions, fetchPendingSubmissions, fetchStats, stats } = useSubmissionStore();

  // Any user can see pending submissions if they have any assigned to them
  const canSeePending = true;

  useEffect(() => {
    // Load initial data
    fetchSubmissions();
    fetchStats();
  }, []);

  const handleSubmissionClick = (submission: Submission) => {
    setSelectedSubmission(submission);
  };

  const handleSubmissionUpdate = (updatedSubmission: Submission) => {
    setSelectedSubmission(updatedSubmission);
    // Refresh the list to show updated status
    if (activeTab === 'pending') {
      fetchPendingSubmissions();
    } else {
      fetchSubmissions();
    }
    fetchStats();
  };

  const handleCloseDetail = () => {
    setSelectedSubmission(null);
  };

  const handleTabChange = (tab: 'all' | 'pending') => {
    setActiveTab(tab);
    if (tab === 'pending') {
      fetchPendingSubmissions();
    } else {
      fetchSubmissions();
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Code Review Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {user?.role === 'reviewer' || user?.role === 'admin' 
            ? 'Review submitted code and provide feedback to developers.'
            : 'Track your code submissions and review status.'
          }
        </p>
      </div>

      {/* Stats Overview */}
      <div className="mb-8">
        <SubmissionStats stats={stats} />
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => handleTabChange('all')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'all'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              All Submissions
            </button>
            {canSeePending && (
              <button
                onClick={() => handleTabChange('pending')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'pending'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Pending Review
              </button>
            )}
          </nav>
        </div>
      </div>

      {/* Submissions List */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            {activeTab === 'pending' ? 'Pending Reviews' : 'All Submissions'}
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {activeTab === 'pending' 
              ? 'Submissions waiting for review feedback.'
              : 'All code submissions in the system.'
            }
          </p>
        </div>
        <div className="p-6">
          <SubmissionList
            showPendingOnly={activeTab === 'pending'}
            onSubmissionClick={handleSubmissionClick}
          />
        </div>
      </div>

      {/* Submission Detail Modal */}
      {selectedSubmission && (
        <SubmissionDetail
          submission={selectedSubmission}
          onClose={handleCloseDetail}
          onUpdate={handleSubmissionUpdate}
        />
      )}
    </div>
  );
};

export default ReviewPage; 