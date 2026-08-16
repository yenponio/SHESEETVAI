import { BrowserRouter, Routes, Route } from "react-router-dom";

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