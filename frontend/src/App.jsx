import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./context/AuthContext";
import AdminDashboard from "./pages/AdminDashboard";
import AuthPage from "./pages/AuthPage";
import UserDashboard from "./pages/UserDashboard";


function ProtectedRoute({ adminOnly = false, children }) {
    const { loading, user } = useAuth();

    if (loading) {
        return <div className="app-loader"><span className="spinner" /></div>;
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (adminOnly && user.role !== "admin") {
        return <Navigate to="/dashboard" replace />;
    }

    if (!adminOnly && user.role === "admin") {
        return <Navigate to="/admin" replace />;
    }

    return children;
}


export default function App() {
    const { user } = useAuth();
    const home = user?.role === "admin" ? "/admin" : "/dashboard";

    return (
        <Routes>
            <Route
                path="/login"
                element={user ? <Navigate to={home} replace /> : <AuthPage />}
            />
            <Route
                path="/dashboard"
                element={
                    <ProtectedRoute>
                        <UserDashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin"
                element={
                    <ProtectedRoute adminOnly>
                        <AdminDashboard />
                    </ProtectedRoute>
                }
            />
            <Route path="*" element={<Navigate to={user ? home : "/login"} replace />} />
        </Routes>
    );
}
