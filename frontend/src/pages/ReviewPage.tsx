import React from 'react'
import WebSocketTest from '../components/WebSocketTest'

const ReviewPage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          WebSocket Infrastructure Test
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Test the real-time WebSocket communication for terminal and file synchronization.
        </p>
      </div>
      
      <WebSocketTest />
      
      <div className="mt-8 bg-white dark:bg-gray-800 shadow rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
            Code Review Dashboard
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500 dark:text-gray-400">
            <p>Review submitted code and provide feedback.</p>
          </div>
          <div className="mt-5">
            <div className="rounded-md bg-gray-50 dark:bg-gray-700 p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    No submissions to review
                  </h3>
                  <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                    <p>When users submit code for review, it will appear here.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ReviewPage 