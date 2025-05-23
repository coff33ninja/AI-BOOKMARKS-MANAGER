// frontend/src/components/AnalyticsDashboard.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/analytics/');
        setAnalytics(response.data);
        setError('');
      } catch (err) {
        console.error('Error fetching analytics:', err);
        setError('Failed to load analytics data.');
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) return <p className="text-center py-4">Loading analytics...</p>;
  if (error) return <p className="text-center py-4 text-red-500">{error}</p>;
  if (!analytics) return null;

  const categoryChartData = {
    labels: Object.keys(analytics.category_counts),
    datasets: [{
      label: 'Bookmarks per Category',
      data: Object.values(analytics.category_counts),
      backgroundColor: 'rgba(54, 162, 235, 0.6)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 1,
    }],
  };

  const tagChartData = {
    labels: Object.keys(analytics.tag_counts),
    datasets: [{
      label: 'Bookmarks per Tag',
      data: Object.values(analytics.tag_counts),
      backgroundColor: 'rgba(255, 159, 64, 0.6)',
      borderColor: 'rgba(255, 159, 64, 1)',
      borderWidth: 1,
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1
        }
      }
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Analytics Overview',
      },
    },
  };

  return (
    <div className="mt-8 p-6 bg-white shadow-lg rounded-lg">
      <h2 className="text-2xl font-semibold mb-6 text-center">Analytics Dashboard</h2>
      <div className="grid md:grid-cols-2 gap-8 mb-8">
        <div>
          <h3 className="text-xl font-medium mb-3 text-gray-700">Category Distribution</h3>
          <div style={{ height: '300px' }}>
            <Bar data={categoryChartData} options={{...chartOptions, plugins: {...chartOptions.plugins, title: {display: true, text: 'Bookmarks by Category'}}}} />
          </div>
        </div>
        <div>
          <h3 className="text-xl font-medium mb-3 text-gray-700">Tag Distribution</h3>
          <div style={{ height: '300px' }}>
            <Bar data={tagChartData} options={{...chartOptions, plugins: {...chartOptions.plugins, title: {display: true, text: 'Bookmarks by Tag'}}}} />
          </div>
        </div>
      </div>
      <div>
        <h3 className="text-xl font-medium mb-3 text-gray-700">Recent Actions (Last 10)</h3>
        {analytics.recent_actions.length > 0 ? (
          <ul className="list-disc pl-5 space-y-1 text-sm text-gray-600">
            {analytics.recent_actions.map((action, index) => (
              <li key={index}>
                <span className="font-semibold capitalize">{action.action}</span> on bookmark "{action.title}" (ID: {action.bookmark_id}) at {new Date(action.timestamp).toLocaleString()}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No recent actions to display.</p>
        )}
      </div>
    </div>
  );
}

export default AnalyticsDashboard;
