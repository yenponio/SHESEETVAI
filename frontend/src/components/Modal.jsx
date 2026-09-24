import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";

export default function Modal({ title, children, onClose, footer, busy = false, large = false, id, drawer = false }) {
  const heading = useId();
  const dialog = useRef(null);
  useEffect(() => {
    const element = dialog.current;
    const opener = document.activeElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    element.showModal();
    return () => {
      element.close();
      document.body.style.overflow = overflow;
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus();
    };
  }, []);
  function containFocus(event) {
    if (event.key !== "Tab") return;
    const controls = [...dialog.current.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])')].filter(element => element.getClientRects().length);
    const first = controls[0], last = controls.at(-1);
    if (!first) { event.preventDefault(); dialog.current.focus(); }
    else if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
  return createPortal(<dialog ref={dialog} id={id} className={`sh-modal ${large ? "sh-modal-lg" : ""} ${drawer ? "sh-drawer" : ""}`} tabIndex={-1} onKeyDown={containFocus}
    aria-labelledby={heading} onCancel={event => { event.preventDefault(); if (!busy) onClose(); }}>
    <div className={`modal-dialog modal-dialog-centered modal-dialog-scrollable ${large ? "modal-lg" : ""}`}>
      <div className="modal-content">
        <div className="modal-header"><h2 className="modal-title fs-5" id={heading}>{title}</h2>
          <button type="button" className="btn-close" aria-label="Close dialog" disabled={busy} onClick={onClose} /></div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  </dialog>, document.body);
}
