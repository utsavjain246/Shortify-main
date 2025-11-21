import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { urlAPI } from '../api/urls';
import { FiLink, FiTrash2, FiExternalLink, FiBarChart2, FiTrendingUp, FiEye, FiClock } from 'react-icons/fi';

const Dashboard = () => {
  const { user } = useAuth();
  const [urls, setUrls] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedUrl, setSelectedUrl] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const [urlsData, summaryData] = await Promise.all([
        urlAPI.getUserURLs(user.id),
        urlAPI.getUserAnalyticsSummary(user.id)
      ]);
      setUrls(urlsData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (shortCode) => {
    if (!window.confirm('Are you sure you want to delete this URL?')) return;

    try {
      await urlAPI.deleteURL(shortCode);
      setUrls(urls.filter(url => url.short_code !== shortCode));
      fetchData(); // Refresh summary
    } catch (error) {
      console.error('Failed to delete URL:', error);
    }
  };

  const viewAnalytics = async (shortCode) => {
    try {
      const data = await urlAPI.getAnalytics(shortCode);
      setAnalytics({ shortCode, ...data });
      setSelectedUrl(shortCode);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Welcome back, {user?.username}! Here's your URL overview.
        </p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="stat-card">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Total URLs
              </span>
              <FiLink className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div className="text-3xl font-bold">{summary.total_urls}</div>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Active URLs
              </span>
              <FiTrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div className="text-3xl font-bold">{summary.active_urls}</div>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Total Clicks
              </span>
              <FiEye className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="text-3xl font-bold">{summary.total_clicks}</div>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Last 7 Days
              </span>
              <FiClock className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="text-3xl font-bold">{summary.recent_clicks_7_days}</div>
          </div>
        </div>
      )}

      {/* URLs Table */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Your URLs</h2>

        {urls.length === 0 ? (
          <div className="text-center py-12">
            <FiLink className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              You haven't created any short URLs yet
            </p>
            <a href="/" className="btn-primary">
              Create Your First URL
            </a>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200 dark:border-gray-700">
                <tr className="text-left">
                  <th className="pb-3 font-medium text-gray-600 dark:text-gray-400">Short URL</th>
                  <th className="pb-3 font-medium text-gray-600 dark:text-gray-400">Original URL</th>
                  <th className="pb-3 font-medium text-gray-600 dark:text-gray-400">Clicks</th>
                  <th className="pb-3 font-medium text-gray-600 dark:text-gray-400">Created</th>
                  <th className="pb-3 font-medium text-gray-600 dark:text-gray-400">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {urls.map((url) => (
                  <tr key={url.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="py-4">
                      <a
                        href={url.full_short_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 dark:text-primary-400 font-medium hover:underline flex items-center gap-2"
                      >
                        {url.short_code}
                        <FiExternalLink className="w-4 h-4" />
                      </a>
                    </td>
                    <td className="py-4">
                      <div className="max-w-xs truncate text-gray-600 dark:text-gray-400">
                        {url.original_url}
                      </div>
                    </td>
                    <td className="py-4">
                      <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full text-sm font-medium">
                        <FiEye className="w-4 h-4" />
                        {url.total_clicks}
                      </span>
                    </td>
                    <td className="py-4 text-gray-600 dark:text-gray-400">
                      {new Date(url.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => viewAnalytics(url.short_code)}
                          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors"
                          title="View Analytics"
                        >
                          <FiBarChart2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </button>
                        <button
                          onClick={() => handleDelete(url.short_code)}
                          className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                          title="Delete URL"
                        >
                          <FiTrash2 className="w-5 h-5 text-red-600 dark:text-red-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Analytics Modal */}
      {analytics && selectedUrl && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setAnalytics(null)}>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold">Analytics for /{selectedUrl}</h3>
              <button
                onClick={() => setAnalytics(null)}
                className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
              <div className="stat-card">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Clicks</div>
                <div className="text-2xl font-bold">{analytics.total_clicks}</div>
              </div>
              <div className="stat-card">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Unique Visitors</div>
                <div className="text-2xl font-bold">{analytics.unique_ips}</div>
              </div>
              <div className="stat-card">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Today</div>
                <div className="text-2xl font-bold">{analytics.clicks_today}</div>
              </div>
              <div className="stat-card">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">This Week</div>
                <div className="text-2xl font-bold">{analytics.clicks_this_week}</div>
              </div>
              <div className="stat-card">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">This Month</div>
                <div className="text-2xl font-bold">{analytics.clicks_this_month}</div>
              </div>
            </div>

            {analytics.top_referrers && analytics.top_referrers.length > 0 && (
              <div className="mb-6">
                <h4 className="font-semibold mb-3">Top Referrers</h4>
                <div className="space-y-2">
                  {analytics.top_referrers.map((ref, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <span className="text-sm truncate flex-1">{ref.referrer || 'Direct'}</span>
                      <span className="text-sm font-medium ml-2">{ref.count} clicks</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {analytics.clicks_by_date && analytics.clicks_by_date.length > 0 && (
              <div>
                <h4 className="font-semibold mb-3">Recent Activity</h4>
                <div className="space-y-2">
                  {analytics.clicks_by_date.slice(0, 7).map((day, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <span className="text-sm">{new Date(day.date).toLocaleDateString()}</span>
                      <span className="text-sm font-medium">{day.clicks} clicks</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
