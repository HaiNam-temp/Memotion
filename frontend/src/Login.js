import React, { useState } from 'react';

const API_BASE = 'http://localhost:8000/api';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (data.code === '200' && data.data.access_token) {
        localStorage.setItem('token', data.data.access_token);
        onLogin();
      } else {
        setError('Login failed');
      }
    } catch (err) {
      setError('Network error');
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <label>Username: <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required /></label><br />
        <label>Password: <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label><br />
        <button type="submit">Login</button>
      </form>
      {error && <p>{error}</p>}
    </div>
  );
}

export default Login;