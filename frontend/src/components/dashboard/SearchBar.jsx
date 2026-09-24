import { SearchBar as SharedSearchBar } from "../UI";
export default function SearchBar({search,setSearch}) { return <SharedSearchBar value={search} onChange={setSearch} />; }
