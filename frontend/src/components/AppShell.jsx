import { useState } from "react";
import { useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import { navigation } from "../navigation";
import Topbar from "./Topbar";
import Modal from "./Modal";
export default function AppShell({ children }) {
  const [compact, setCompact] = useState(false);
  const [mobile, setMobile] = useState(false);
  const { pathname } = useLocation();
  const title = navigation.find(([path]) => pathname.startsWith(path))?.[2] || "OSA workspace";
  return <div className={`app-shell ${compact ? "is-compact" : ""}`}>
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside id="desktop-navigation" className="desktop-sidebar"><Sidebar compact={compact} /></aside>
    <div className="workspace"><Topbar title={title} compact={compact} toggleDesktop={() => setCompact(!compact)} openMobile={() => setMobile(true)} />
      <main id="main-content" className="container-fluid app-content" tabIndex={-1}>{children}</main></div>
    {mobile && <Modal drawer title="Navigation" id="mobile-navigation" onClose={() => setMobile(false)}><Sidebar onNavigate={() => setMobile(false)} /></Modal>}
  </div>;
}
