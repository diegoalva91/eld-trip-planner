const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export async function planTrip(payload) {
  let response
  try {
    response = await fetch(`${API_BASE}/trips/plan/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch (error) {
    throw new Error(
      `Cannot connect to Django at ${API_BASE}. Start the backend with: python manage.py runserver 8000`,
    )
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || `Trip planner request failed (${response.status})`)
  }
  return data
}
