import { Link } from "react-router-dom";
import ViolationTable from "../components/ViolationTable";
import useLiveData from "../hooks/useLiveData";
import { PageHeading, Icon } from "../components/UI";
export default function Records() {
  const { data,error } = useLiveData("http://127.0.0.1:8000/api/students/records/");
  return <><PageHeading title="Official violation records" description="Confirmed-entry offenses, their original evidence, and current student totals." />
    <div className="school-links mb-4" aria-label="Browse school records">{data?.schools.map(school => <Link key={school} className="btn btn-outline-primary btn-sm" to={`/records/${encodeURIComponent(school.toLowerCase())}`}><Icon name="building" />{school}</Link>)}</div>
    <section className="card"><div className="card-body"><h2>All schools</h2><ViolationTable records={data?.records || []} loading={!data && !error} error={error} /></div></section></>;
}
