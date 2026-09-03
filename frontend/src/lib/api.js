const API_BASE_URL = (
    import.meta.env.VITE_API_BASE_URL
    || "http://127.0.0.1:5000/api"
).replace(/\/$/, "");


export class ApiRequestError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}


export async function apiRequest(path, options = {}) {
    const token = localStorage.getItem("researchmind_token");
    const headers = new Headers(options.headers || {});

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    if (options.body && !(options.body instanceof FormData)) {
        headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new ApiRequestError(
            data.message || "Something went wrong",
            response.status,
        );
    }

    return data;
}


export { API_BASE_URL };
