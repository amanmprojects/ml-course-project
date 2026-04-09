const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function predictCrop(payload) {
  const response = await fetch(`${API_BASE}/predict?model=xgboost`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail || 'Prediction request failed.';
    throw new Error(detail);
  }

  return response.json();
}

export async function extractReportValues(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/extract-report-values`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail || 'Report extraction failed.';
    throw new Error(detail);
  }

  return response.json();
}
