function SearchBar({ setSearchQuery }) {
  return (
    <div className="mb-4">
      <input
        type="text"
        placeholder="Search by title, URL, or tags..."
        onChange={(e) => setSearchQuery(e.target.value)}
        className="p-2 w-full border rounded"
      />
    </div>
  );
}

export default SearchBar;
