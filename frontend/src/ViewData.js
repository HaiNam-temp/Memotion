import React, { useState } from 'react';

const API_BASE = 'http://localhost:8000/api';

function ViewData() {
  const [data, setData] = useState([]);
  const [type, setType] = useState('');
  const [error, setError] = useState('');

  const fetchData = async (endpoint) => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${API_BASE}/${endpoint}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const result = await response.json();
      if (result.code === '200') {
        setData(result.data);
        setType(endpoint);
        setError('');
      } else {
        setError('Error: ' + (result.message || 'Unknown error'));
      }
    } catch (err) {
      setError('Network error');
    }
  };

  const renderItem = (item) => {
    if (type === 'medication-library') {
      return (
        <div key={item.medication_id} className="item">
          <strong>{item.name}</strong><br />
          Description: {item.description || 'N/A'}<br />
          Dosage: {item.dosage || 'N/A'}<br />
          Frequency: {item.frequency_per_day || 'N/A'}<br />
          Notes: {item.notes || 'N/A'}<br />
          Image: {item.image_path ? <img src={item.image_path} alt="Image" style={{ maxWidth: '100px' }} /> : 'N/A'}
        </div>
      );
    } else if (type === 'nutrition-library') {
      return (
        <div key={item.nutrition_id} className="item">
          <strong>{item.name}</strong><br />
          Calories: {item.calories || 'N/A'}<br />
          Description: {item.description || 'N/A'}<br />
          Meal Type: {item.meal_type || 'N/A'}<br />
          Image: {item.image_path ? <img src={item.image_path} alt="Image" style={{ maxWidth: '100px' }} /> : 'N/A'}
        </div>
      );
    } else if (type === 'exercise-library') {
      return (
        <div key={item.exercise_id} className="item">
          <strong>{item.name}</strong><br />
          Target Region: {item.target_body_region || 'N/A'}<br />
          Description: {item.description || 'N/A'}<br />
          Duration: {item.duration_minutes || 'N/A'} min<br />
          Difficulty: {item.difficulty_level || 'N/A'}<br />
          Video: {item.video_path ? <video src={item.video_path} controls style={{ maxWidth: '100px' }} /> : 'N/A'}
        </div>
      );
    }
    return null;
  };

  return (
    <div>
      <h1>View Data</h1>
      <a href="#add">Add Data</a>
      <button onClick={() => { localStorage.removeItem('token'); window.location.reload(); }}>Logout</button>
      <div>
        <button onClick={() => fetchData('medication-library')}>View Medications</button>
        <button onClick={() => fetchData('nutrition-library')}>View Nutrition</button>
        <button onClick={() => fetchData('exercise-library')}>View Exercises</button>
      </div>
      {error && <p>{error}</p>}
      <div className="grid">
        {data.map(renderItem)}
      </div>
    </div>
  );
}

export default ViewData;