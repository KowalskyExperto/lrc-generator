import React, { useState } from 'react';
import './App.css';

function App() {
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [lyricsText, setLyricsText] = useState<string>('');
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setAudioFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!audioFile || !lyricsText) {
      setError('Please provide both an audio file and lyrics.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('lyrics_text', lyricsText);

    try {
      const response = await fetch('http://localhost:8000/process-lyrics', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'An unknown error occurred.');
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch from the API.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Lyric Processor</h1>
      </header>
      <main>
        <div className="form-container">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="audio-file">Audio File</label>
              <input 
                id="audio-file"
                type="file" 
                accept="audio/*" 
                onChange={handleFileChange} 
              />
            </div>
            <div className="form-group">
              <label htmlFor="lyrics-text">Lyrics</label>
              <textarea 
                id="lyrics-text"
                value={lyricsText} 
                onChange={(e) => setLyricsText(e.target.value)} 
                placeholder="Paste your lyrics here..."
              />
            </div>
            <button type="submit" className="submit-btn" disabled={isLoading}>
              {isLoading ? 'Processing...' : 'Generate'}
            </button>
          </form>
          {error && <p className="status-message error-message">Error: {error}</p>}
        </div>

        {result && (
          <div className="result-container">
            <h2>Result:</h2>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;