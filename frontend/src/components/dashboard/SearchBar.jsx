import { FaSearch } from "react-icons/fa";
import "./../../styles/Dashboard.css";


function SearchBar({ search, setSearch }) {

  return (

    <div className="search-container">

      <FaSearch className="search-icon" />

      <input

        type="text"

        placeholder="Search student..."

        value={search}

        onChange={(e) =>
          setSearch(e.target.value)
        }

      />

    </div>

  );

}


export default SearchBar;