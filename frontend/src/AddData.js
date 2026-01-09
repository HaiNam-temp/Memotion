import React, { useState } from 'react';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api';

function AddData() {
  const [message, setMessage] = useState('');

  const handleSubmit = async (e, type) => {
    e.preventDefault();
    const form = e.target;
    const token = localStorage.getItem('token');
    let data = {};
    let filePath = null;

    const fileInput = form.querySelector(`input[type="file"]`);
    if (fileInput.files[0]) {
      filePath = await uploadFile(fileInput.files[0], token, type);
    }

    if (type === 'medication') {
      data = {
        name: form.name.value,
        description: form.description.value,
        dosage: form.dosage.value,
        frequency_per_day: parseInt(form.frequency.value) || null,
        notes: form.notes.value,
        image_path: filePath,
      };
    } else if (type === 'nutrition') {
      data = {
        name: form.name.value,
        calories: parseInt(form.calories.value) || null,
        description: form.description.value,
        meal_type: form.mealType.value,
        image_path: filePath,
      };
    } else if (type === 'exercise') {
      data = {
        name: form.name.value,
        target_body_region: form.region.value,
        description: form.description.value,
        duration_minutes: parseInt(form.duration.value) || null,
        difficulty_level: parseInt(form.difficulty.value) || null,
        video_path: filePath,
      };
    }

    try {
      const response = await fetch(`${API_BASE}/${type}-library`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });
      const result = await response.json();
      if (result.code === '200') {
        setMessage('Added successfully');
        form.reset();
      } else {
        setMessage('Error: ' + (result.message || 'Unknown error'));
      }
    } catch (err) {
      setMessage('Network error');
    }
  };

  const uploadFile = async (file, token, type) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,
    });
    const result = await response.json();
    if (result.code === '200') {
      return result.data;
    } else {
      throw new Error(result.message || 'Upload failed');
    }
  };

  return (
    <div>
      <h1>Add Data</h1>
      <a href="#view">View Data</a>
      <button onClick={() => { localStorage.removeItem('token'); window.location.reload(); }}>Logout</button>
      {message && <p>{message}</p>}
      <div style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap' }}>
        <div style={{ width: '300px', padding: '20px', border: '1px solid #ccc', margin: '10px' }}>
          <h2>Add Medication</h2>
          <form onSubmit={(e) => handleSubmit(e, 'medication')}>
            <label>Name: <input name="name" required /></label><br />
            <label>Description: <textarea name="description" /></label><br />
            <label>Dosage: <input name="dosage" /></label><br />
            <label>Frequency: <input name="frequency" type="number" /></label><br />
            <label>Notes: <textarea name="notes" /></label><br />
            <label>Image: <input type="file" accept="image/*" /></label><br />
            <button type="submit">Add</button>
          </form>
        </div>
        <div style={{ width: '300px', padding: '20px', border: '1px solid #ccc', margin: '10px' }}>
          <h2>Add Nutrition</h2>
          <form onSubmit={(e) => handleSubmit(e, 'nutrition')}>
            <label>Name: <input name="name" required /></label><br />
            <label>Calories: <input name="calories" type="number" /></label><br />
            <label>Description: <textarea name="description" /></label><br />
            <label>Meal Type: <input name="mealType" /></label><br />
            <label>Image: <input type="file" accept="image/*" /></label><br />
            <button type="submit">Add</button>
          </form>
        </div>
        <div style={{ width: '300px', padding: '20px', border: '1px solid #ccc', margin: '10px' }}>
          <h2>Add Exercise</h2>
          <form onSubmit={(e) => handleSubmit(e, 'exercise')}>
            <label>Name: <input name="name" required /></label><br />
            <label>Region: <input name="region" /></label><br />
            <label>Description: <textarea name="description" /></label><br />
            <label>Duration: <input name="duration" type="number" /></label><br />
            <label>Difficulty: <input name="difficulty" type="number" /></label><br />
            <label>Video: <input type="file" accept="video/*" /></label><br />
            <button type="submit">Add</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AddData;