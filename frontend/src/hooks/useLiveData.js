import { useEffect, useState } from "react";

// Poll after each request completes so slow responses cannot overlap.
export default function useLiveData(url) {
  const [state, setState] = useState({ url, data: null, error: "", updatedAt: null });

  useEffect(() => {
    let disposed = false;
    let timer;
    let active = false;
    let controller;

    async function refresh() {
      if (disposed || active) return;
      clearTimeout(timer);
      active = true;
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      try {
        const response = await fetch(url, { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Request failed");
        const data = await response.json();
        if (!disposed) setState({ url, data, error: "", updatedAt: new Date() });
      } catch {
        if (!disposed) setState(previous => ({
          url,
          data: previous.url === url ? previous.data : null,
          updatedAt: previous.url === url ? previous.updatedAt : null,
          error: "Unable to refresh data. Displayed data may be outdated. Retrying automatically.",
        }));
      } finally {
        clearTimeout(timeout);
        active = false;
        if (!disposed) timer = setTimeout(refresh, 5000);
      }
    }

    function onVisible() {
      if (document.visibilityState === "visible") refresh();
    }
    refresh();
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      disposed = true;
      clearTimeout(timer);
      controller?.abort();
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [url]);

  return state.url === url ? state : { data: null, error: "", updatedAt: null };
}
