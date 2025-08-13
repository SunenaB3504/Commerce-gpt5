// Resolve API base URL:
// - Prefer window.API_BASE_OVERRIDE when explicitly set.
// - Else use current page origin (works when served by FastAPI at /web).
// - Fallback to http://127.0.0.1:8000 for local dev when opened from file://
export const API_BASE = (() => {
	if (window.API_BASE_OVERRIDE) return window.API_BASE_OVERRIDE;
	const origin = window.location && window.location.origin;
	if (origin && origin !== 'null') return origin;
	return 'http://127.0.0.1:8000';
})();
