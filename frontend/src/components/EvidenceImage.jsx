import { useState } from "react";
import { EmptyState } from "./UI";
export default function EvidenceImage({ src, alt, id }) {
  const [failedUrl, setFailedUrl] = useState(null);
  return <div className="media-frame">{src && failedUrl !== src ? <img id={id} src={src} alt={alt} onError={() => setFailedUrl(src)} /> : <EmptyState icon="image" title="No evidence image available." />}</div>;
}
