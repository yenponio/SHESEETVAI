import { Link,useParams } from "react-router-dom";
import ViolationTable from "../components/ViolationTable";
import useLiveData from "../hooks/useLiveData";
import { PageHeading,Icon } from "../components/UI";
export default function SchoolRecords() {
  const {school} = useParams();
  const {data,error} = useLiveData(`http://127.0.0.1:8000/api/students/records/${encodeURIComponent(school)}/`);
  return <><PageHeading title={`${data?.school || school.toUpperCase()} records`} description="Official confirmed-entry offenses for this school."><Link to="/records" className="btn btn-outline-primary"><Icon name="arrow-left" />All schools</Link></PageHeading><section className="card"><div className="card-body"><ViolationTable records={data?.records || []} loading={!data && !error} error={error} /></div></section></>;
}
