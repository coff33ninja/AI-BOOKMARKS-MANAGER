// frontend/src/components/BookmarkList.jsx
import { useEffect } from 'react';
import axios from 'axios';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

function BookmarkList({ bookmarks, setBookmarks, searchQuery, category }) {

  const fetchBookmarks = async () => {
    try {
      let url = '/api/bookmarks/';
      const params = new URLSearchParams();
      if (searchQuery) {
        url = `/api/bookmarks/search/`;
        params.append('query', searchQuery);
      }
      if (category) {
        // If searching and categorizing, backend needs to support both
        // For now, category filter overrides search if both are active, or vice-versa
        // Assuming category filter applies to the base list or search results if backend supports it
        // For simplicity, if category is set, we fetch by category.
        // A more robust solution might involve backend handling combined filters.
        if (!searchQuery) { // Only apply category if not searching, or adjust backend
            params.append('category', category);
        }
      }

      const response = await axios.get(url, { params });
      setBookmarks(response.data); // Backend should return sorted by position
    } catch (error) {
      console.error('Error fetching bookmarks:', error);
    }
  };

  useEffect(() => {
    fetchBookmarks();
  }, [searchQuery, category]); // Removed setBookmarks from deps to avoid potential loops
                               // Relies on parent to manage `bookmarks` state via WebSocket primarily

  const deleteBookmark = async (id) => {
    try {
      await axios.delete(`/api/bookmarks/${id}`);
      // Optimistic update handled by WebSocket via App.jsx
      // setBookmarks(bookmarks.filter(bookmark => bookmark.id !== id));
    } catch (error) {
      console.error('Error deleting bookmark:', error);
    }
  };

  const handleDragEnd = async (result) => {
    if (!result.destination) return;

    const reorderedBookmarks = Array.from(bookmarks);
    const [movedBookmark] = reorderedBookmarks.splice(result.source.index, 1);
    reorderedBookmarks.splice(result.destination.index, 0, movedBookmark);

    // Update positions for the entire list (or affected segment)
    const updatedBookmarksWithNewPositions = reorderedBookmarks.map((bookmark, index) => ({
      ...bookmark,
      position: index + 1.0 // Ensure positions are sequential floats
    }));

    // Optimistically update UI
    setBookmarks(updatedBookmarksWithNewPositions);

    // Send reorder update to backend for the moved bookmark
    // The backend /api/bookmarks/reorder/ expects new_position and category
    const bookmarkToUpdate = updatedBookmarksWithNewPositions[result.destination.index];
    try {
      await axios.post('/api/bookmarks/reorder/', {
        bookmark_id: bookmarkToUpdate.id,
        new_position: bookmarkToUpdate.position,
        category: bookmarkToUpdate.category // Category might change if dragging between categorized lists (future enhancement)
      });
      // Backend broadcast via WebSocket should confirm this change.
      // If not, uncomment fetchBookmarks() or ensure WebSocket handles position updates.
      // fetchBookmarks();
    } catch (error) {
      console.error('Error reordering bookmarks:', error);
      // Revert on error by fetching the original list
      fetchBookmarks();
    }
  };

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-semibold mb-4">Your Bookmarks</h2>
      {bookmarks.length > 0 ? (
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="bookmarksDroppable">
            {(provided) => (
              <div {...provided.droppableProps} ref={provided.innerRef} className="overflow-x-auto">
                <table className="min-w-full bg-white shadow-md rounded-lg">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">URL</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tags</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {bookmarks.map((bookmark, index) => (
                      <Draggable key={bookmark.id.toString()} draggableId={bookmark.id.toString()} index={index}>
                        {(provided) => (
                          <tr
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            className="hover:bg-gray-50"
                          >
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{bookmark.title}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 hover:text-blue-800">
                              <a href={bookmark.url} target="_blank" rel="noopener noreferrer">{bookmark.url}</a>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{bookmark.category || 'N/A'}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {bookmark.tags.map(tag => tag.name).join(', ')}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <button
                                onClick={() => deleteBookmark(bookmark.id)}
                                className="text-red-600 hover:text-red-800 transition-colors duration-150"
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </tbody>
                </table>
              </div>
            )}
          </Droppable>
        </DragDropContext>
      ) : (
        <p className="text-gray-500 text-center py-4">No bookmarks yet. Add some to get started!</p>
      )}
    </div>
  );
}

export default BookmarkList;
