import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";

import { apiRequest } from "../lib/api";


const AuthContext = createContext(null);


export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const logout = useCallback(() => {
        localStorage.removeItem("researchmind_token");
        setUser(null);
    }, []);

    useEffect(() => {
        if (!localStorage.getItem("researchmind_token")) {
            setLoading(false);
            return;
        }

        apiRequest("/auth/me")
            .then(setUser)
            .catch(logout)
            .finally(() => setLoading(false));
    }, [logout]);

    const login = useCallback(async (email, password) => {
        const data = await apiRequest("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });
        localStorage.setItem("researchmind_token", data.access_token);
        setUser(data.user);
        return data.user;
    }, []);

    const register = useCallback(async (name, email, password) => {
        await apiRequest("/auth/register", {
            method: "POST",
            body: JSON.stringify({ name, email, password }),
        });
        return login(email, password);
    }, [login]);

    const value = useMemo(() => ({
        loading,
        login,
        logout,
        register,
        user,
    }), [loading, login, logout, register, user]);

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}


export function useAuth() {
    return useContext(AuthContext);
}
