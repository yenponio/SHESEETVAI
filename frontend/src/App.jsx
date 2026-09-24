import { BrowserRouter, Routes, Route } from "react-router-dom";

import Settings from "./pages/Settings";
import EmailNotifications from "./pages/EmailNotifications";
import Students from "./pages/Students";
import StudentProfile from "./pages/StudentProfile";
import ScanHistory from "./pages/ScanHistory";
import StudentPage from "./pages/StudentPage";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Records from "./pages/Records";
import ConfirmationPage from "./pages/ConfirmationPage";
import ProtectedRoute from "./components/ProtectedRoute";
import SchoolRecords from "./pages/SchoolRecords";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        <Route path="/email-notifications" element={<ProtectedRoute><EmailNotifications /></ProtectedRoute>} />
        <Route path="/students" element={<ProtectedRoute><Students /></ProtectedRoute>} />
        <Route path="/students/:studentNumber" element={<ProtectedRoute><StudentProfile /></ProtectedRoute>} />

        {/* Student Scanner */}
        <Route
          path="/"
          element={<StudentPage />}
        />

        {/* OSA Login */}
        <Route
          path="/osa"
          element={<Login />}
        />

        {/* OSA Dashboard */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* School Records */}
        <Route
          path="/records/:school"
          element={
            <ProtectedRoute>
              <SchoolRecords />
            </ProtectedRoute>
          }
        />

        {/* Records */}
        <Route
          path="/records"
          element={
            <ProtectedRoute>
              <Records />
            </ProtectedRoute>
          }
        />

        {/* Scan History */}
        <Route
          path="/scan-history"
          element={
            <ProtectedRoute>
              <ScanHistory />
            </ProtectedRoute>
          }
        />

        {/* Confirmation Page */}
        <Route
          path="/chatbot"
          element={
            <ProtectedRoute>
              <ConfirmationPage />
            </ProtectedRoute>
          }
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;