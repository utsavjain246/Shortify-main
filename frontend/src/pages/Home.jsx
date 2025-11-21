import { useState } from 'react';
import { urlAPI } from '../api/urls';
import { FiLink, FiCopy, FiCheck, FiDownload, FiAlertCircle } from 'react-icons/fi';

const Home = () => {
  const [originalUrl, setOriginalUrl] = useState('');
  const [customAlias, setCustomAlias] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setResult(null);

    try {
      const data = await urlAPI.shortenURL({
        original_url: originalUrl,
        custom_alias: customAlias || null
      });
      setResult(data);
      setOriginalUrl('');
      setCustomAlias('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to shorten URL. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result.full_short_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadQRCode = () => {
    const link = document.createElement('a');
    link.href = result.qr_code;
    link.download = `qr-${result.short_code}.png`;
    link.click();
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="max-w-2xl w-full">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
            Shorten Your Links
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Create short, memorable links with powerful analytics
          </p>
        </div>

        {/* Main Card */}
        <div className="card mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="url" className="block text-sm font-medium mb-2">
                Enter your long URL
              </label>
              <div className="relative">
                <FiLink className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  id="url"
                  type="url"
                  value={originalUrl}
                  onChange={(e) => setOriginalUrl(e.target.value)}
                  className="input-field pl-10"
                  placeholder="https://example.com/very-long-url"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="alias" className="block text-sm font-medium mb-2">
                Custom alias (optional)
              </label>
              <input
                id="alias"
                type="text"
                value={customAlias}
                onChange={(e) => setCustomAlias(e.target.value)}
                className="input-field"
                placeholder="my-custom-link"
                pattern="[a-zA-Z0-9_-]+"
                title="Only letters, numbers, hyphens, and underscores allowed"
              />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Leave blank for a random short code
              </p>
            </div>

            {error && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-red-600 dark:text-red-400 animate-slide-down">
                <FiAlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full text-lg py-4"
            >
              {loading ? 'Shortening...' : 'Shorten URL'}
            </button>
          </form>
        </div>

        {/* Result Card */}
        {result && (
          <div className="card animate-slide-down">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Your shortened URL</h3>
              <FiCheck className="w-6 h-6 text-green-500" />
            </div>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between gap-4">
                <a
                  href={result.full_short_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 dark:text-primary-400 font-medium text-lg hover:underline flex-1 truncate"
                >
                  {result.full_short_url}
                </a>
                <button
                  onClick={copyToClipboard}
                  className="btn-secondary flex items-center gap-2"
                >
                  {copied ? (
                    <>
                      <FiCheck className="w-5 h-5" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <FiCopy className="w-5 h-5" />
                      Copy
                    </>
                  )}
                </button>
              </div>
            </div>

            {result.qr_code && (
              <div className="text-center">
                <p className="text-sm font-medium mb-3">QR Code</p>
                <img
                  src={result.qr_code}
                  alt="QR Code"
                  className="mx-auto w-48 h-48 rounded-lg border-2 border-gray-200 dark:border-gray-600"
                />
                <button
                  onClick={downloadQRCode}
                  className="btn-secondary mt-4 flex items-center gap-2 mx-auto"
                >
                  <FiDownload className="w-5 h-5" />
                  Download QR Code
                </button>
              </div>
            )}

            <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              <p className="truncate">
                Original: <span className="font-medium">{result.original_url}</span>
              </p>
            </div>
          </div>
        )}

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center mx-auto mb-3">
              <FiLink className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="font-semibold mb-2">Custom Aliases</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Create branded, memorable short links
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center mx-auto mb-3">
              <FiDownload className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="font-semibold mb-2">QR Codes</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Generate QR codes instantly
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center mx-auto mb-3">
              <FiCheck className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="font-semibold mb-2">Analytics</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Track clicks and engagement
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
