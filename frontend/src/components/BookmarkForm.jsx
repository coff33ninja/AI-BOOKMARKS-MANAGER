import { useState } from 'react';
import axios from 'axios';

function BookmarkForm({ setBookmarks }) {
  const [formData, setFormData] = useState({ url: '', title: '', description: '', tags: [] });
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/api/bookmarks/', {
        ...formData,
        tags: formData.tags.length ? formData.tags.split(',').map(tag => tag.trim()) : []
      });
      setBookmarks(prev => [response.data, ...prev]);
      setFormData({ url: '', title: '', description: '', tags: [] });
      setMessage('Bookmark added successfully!');
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Error adding bookmark');
    }
  };

  const suggestTitle = async () => {
    try {
      const response = await axios.post('/api/ai/suggest-title', { url: formData.url });
      if (response.data.suggested_title) {
        setFormData({ ...formData, title: response.data.suggested_title });
        setMessage('Title suggested successfully!');
      } else {
        setMessage(response.data.error || 'Could not suggest title');
      }
    } catch (error) {
      setMessage('Error fetching title suggestion');
    }
  };

  const suggestTags = async () => {
    try {
      const response = await axios.post('/api/ai/suggest-tags', { url: formData.url });
      if (response.data.suggested_tags.length) {
        setFormData({ ...formData, tags: response.data.suggested_tags.join(', ') });
        setMessage('Tags suggested successfully!');
      } else {
        setMessage(response.data.error || 'Could not suggest tags');
      }
    } catch (error) {
      setMessage('Error fetching tag suggestions');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mb-6">
      <div className="mb-4">
        <label className="block text-sm font-medium">URL</label>
        <input
          type="url"
          value={formData.url}
          onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          className="mt-1 p-2 w-full border rounded"
          required
        />
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium">Title</label>
        <input
          type="text"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          className="mt-1 p-2 w-full border rounded"
        />
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium">Description</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          className="mt-1 p-2 w-full border rounded"
        />
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium">Tags (comma-separated)</label>
        <input
          type="text"
          value={formData.tags}
          onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
          className="mt-1 p-2 w-full border rounded"
        />
      </div>
      <div className="flex space-x-2">
        <button type="button" onClick={suggestTitle} className="p-2 bg-blue-500 text-white rounded">
          Suggest Title
        </button>
        <button type="button" onClick={suggestTags} className="p-2 bg-blue-500 text-white rounded">
          Suggest Tags
        </button>
        <button type="submit" className="p-2 bg-green-500 text-white rounded">
          Add Bookmark
        </button>
      </div>
      {message && (
        <div className={`mt-2 p-2 ${message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'} rounded`}>
          {message}
        </div>
      )}
    </form>
  );
}

export default BookmarkForm;
