// One shared backend address for the whole frontend - override via a
// VITE_API_BASE entry in frontend/.env for anything other than local dev,
// instead of editing a hardcoded URL in each file that calls the API.
export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
