import { FaSearch } from "react-icons/fa";
import "./../../styles/Dashboard.css";

function SearchBar() {
  return (
    <div className="search-container">

      <FaSearch className="search-icon" />

      <input
        type="text"
        placeholder="Search student..."
      />

    </div>
  );
}

export default SearchBar;