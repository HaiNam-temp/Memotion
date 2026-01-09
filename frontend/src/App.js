import React, { useState, useEffect } from 'react';
import Login from './Login';
import AddData from './AddData';
import ViewData from './ViewData';
import './App.css';

function App() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [view, setView] = useState('add'); // 'add' or 'view'

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setLoggedIn(true);
    }
  }, []);

  if (!loggedIn) {
    return <Login onLogin={() => setLoggedIn(true)} />;
  }

  return (
    <div className="App">
      {view === 'add' ? (
        <AddData />
      ) : (
        <ViewData />
      )}
      <div>
        <button onClick={() => setView('add')}>Add Data</button>
        <button onClick={() => setView('view')}>View Data</button>
      </div>
    </div>
  );
}

export default App;
