import { useMemo, useRef, useState } from 'react';
import { extractReportValues, predictCrop } from './api';

const fieldConfig = [
  { key: 'N', label: 'Nitrogen (N)', min: 0, max: 300, step: 'any' },
  { key: 'P', label: 'Phosphorus (P)', min: 0, max: 300, step: 'any' },
  { key: 'K', label: 'Potassium (K)', min: 0, max: 300, step: 'any' },
  { key: 'temperature', label: 'Temperature (C)', min: 0, max: 60, step: 'any' },
  { key: 'humidity', label: 'Humidity (%)', min: 0, max: 100, step: 'any' },
  { key: 'ph', label: 'Soil pH', min: 0, max: 14, step: 'any' },
  { key: 'rainfall', label: 'Rainfall (mm)', min: 0, max: 500, step: 'any' },
];

const initialValues = fieldConfig.reduce((acc, field) => {
  acc[field.key] = '';
  return acc;
}, {});

function validate(values) {
  const nextErrors = {};

  for (const field of fieldConfig) {
    const raw = values[field.key];

    if (raw === '') {
      nextErrors[field.key] = 'Required';
      continue;
    }

    const num = Number(raw);
    if (Number.isNaN(num)) {
      nextErrors[field.key] = 'Must be numeric';
      continue;
    }

    if (num < field.min || num > field.max) {
      nextErrors[field.key] = `Use ${field.min} to ${field.max}`;
    }
  }

  return nextErrors;
}

export default function App() {
  const fileInputRef = useRef(null);
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [apiError, setApiError] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [extractSummary, setExtractSummary] = useState(null);
  const [autofilledKeys, setAutofilledKeys] = useState([]);

  const allFilled = useMemo(
    () => Object.values(values).every((v) => String(v).trim() !== ''),
    [values]
  );

  function onChange(key, value) {
    setValues((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: undefined }));
    setApiError('');
    setAutofilledKeys((prev) => prev.filter((k) => k !== key));
  }

  function openFileDialog() {
    fileInputRef.current?.click();
  }

  async function onReportSelected(event) {
    const file = event.target.files?.[0];
    event.target.value = '';

    if (!file) {
      return;
    }

    setUploadLoading(true);
    setUploadError('');
    setApiError('');
    setExtractSummary(null);

    try {
      const data = await extractReportValues(file);
      const extracted = data.extracted_values || {};
      const nextValues = { ...values };
      const nextAutofilled = [];

      for (const field of fieldConfig) {
        const value = extracted[field.key];
        if (value !== null && value !== undefined && !Number.isNaN(Number(value))) {
          nextValues[field.key] = String(value);
          nextAutofilled.push(field.key);
        }
      }

      setValues(nextValues);
      setAutofilledKeys(nextAutofilled);
      setExtractSummary({
        missingFields: data.missing_fields || [],
        confidence: data.confidence,
        fileName: file.name,
      });
      setErrors({});
    } catch (err) {
      setUploadError(err.message || 'Failed to extract values from report image.');
    } finally {
      setUploadLoading(false);
    }
  }

  async function onSubmit(event) {
    event.preventDefault();

    const nextErrors = validate(values);
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setLoading(true);
    setApiError('');
    setResult('');

    try {
      const payload = Object.fromEntries(
        Object.entries(values).map(([k, v]) => [k, Number(v)])
      );
      const data = await predictCrop(payload);
      setResult(data.crop);
    } catch (err) {
      setApiError(err.message || 'Unable to fetch prediction.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <main className="card">
        <h1>AgroMind AI</h1>
        <p className="subtitle">Enter soil and climate values to get one recommended crop.</p>

        <section className="uploadPanel">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={onReportSelected}
            className="hiddenInput"
          />
          <button
            type="button"
            className="secondaryButton"
            onClick={openFileDialog}
            disabled={uploadLoading}
          >
            {uploadLoading ? 'Extracting From Photo...' : 'Upload Report Photo'}
          </button>

          {extractSummary ? (
            <div className="uploadStatus" aria-live="polite">
              <p>
                Extracted from {extractSummary.fileName} with {Math.round((extractSummary.confidence || 0) * 100)}% confidence.
              </p>
              {extractSummary.missingFields.length > 0 ? (
                <p>Missing fields: {extractSummary.missingFields.join(', ')}</p>
              ) : (
                <p>All fields found. Review values and submit prediction.</p>
              )}
            </div>
          ) : null}

          {uploadError ? (
            <div className="errorBox" aria-live="assertive">
              {uploadError}
            </div>
          ) : null}
        </section>

        <form onSubmit={onSubmit} className="form">
          {fieldConfig.map((field) => (
            <label
              className={`field ${autofilledKeys.includes(field.key) ? 'isAutofilled' : ''}`}
              key={field.key}
            >
              <span>{field.label}</span>
              <input
                type="number"
                value={values[field.key]}
                min={field.min}
                max={field.max}
                step={field.step}
                onChange={(e) => onChange(field.key, e.target.value)}
                placeholder={`${field.min} - ${field.max}`}
              />
              {autofilledKeys.includes(field.key) ? (
                <small className="autofilledTag">Autofilled from report photo</small>
              ) : null}
              {errors[field.key] ? <small className="error">{errors[field.key]}</small> : null}
            </label>
          ))}

          <button type="submit" disabled={loading || !allFilled}>
            {loading ? 'Predicting...' : 'Recommend Crop'}
          </button>
        </form>

        {result ? (
          <section className="result" aria-live="polite">
            <h2>Recommended Crop</h2>
            <p>{result}</p>
          </section>
        ) : null}

        {apiError ? (
          <section className="errorBox" aria-live="assertive">
            {apiError}
          </section>
        ) : null}
      </main>
    </div>
  );
}
