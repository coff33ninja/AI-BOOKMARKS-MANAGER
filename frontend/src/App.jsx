// frontend/src/App.jsx
import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import BookmarkList from './components/BookmarkList';
import BookmarkForm from './components/BookmarkForm';
import SearchBar from './components/SearchBar';
import CategoryFilter from './components/CategoryFilter';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import axios from 'axios';
import './styles/App.css'; // Ensure this sets up Tailwind CSS

function App() {
  const [bookmarks, setBookmarks] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('');
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    // Fetch initial categories
    axios.get('/api/categories/').then(response => setCategories(response.data));

    // Initialize WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws/bookmarks');

    ws.onmessage = (event) => {
      const { action, bookmark, bookmark_id } = JSON.parse(event.data);
      if (action === 'create') {
        setBookmarks(prev => [...prev, bookmark].sort((a, b) => (a.position || 0) - (b.position || 0)));
      } else if (action === 'update') {
        setBookmarks(prev => prev.map(b => b.id === bookmark.id ? bookmark : b).sort((a, b) => (a.position || 0) - (b.position || 0)));
      } else if (action === 'delete') {
        setBookmarks(prev => prev.filter(b => b.id !== bookmark_id));
      }
    };

    ws.onclose = () => console.log('WebSocket disconnected');

    // Cleanup WebSocket connection on component unmount
    return () => ws.close();
  }, []); // Empty dependency array: fetch categories and setup WebSocket once

  return (
    <Router>
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-4 text-center">AI Bookmark Manager</h1>
        <div className="md:flex md:space-x-4 mb-6 items-end">
          <div className="flex-grow mb-4 md:mb-0">
            <SearchBar setSearchQuery={setSearchQuery} />
          </div>
          <div>
            <CategoryFilter categories={categories} setCategory={setCategory} />
          </div>
        </div>
        <BookmarkForm setBookmarks={setBookmarks} /> {/* Manages its own state, updates global via setBookmarks on add */}
        <AnalyticsDashboard />
        <Routes>
          <Route
            path="/"
            element={<BookmarkList bookmarks={bookmarks} setBookmarks={setBookmarks} searchQuery={searchQuery} category={category} />}
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
