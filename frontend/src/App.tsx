import React, { useState, useMemo } from 'react';
import './App.css';

// --- Type Definitions ---
interface LyricLine {
  linea: string;
  minutes: string;
  seconds: string;
  milliseconds: string;
  Japanese: string;
  Romaji: string;
  English: string;
  'Improved English': string;
  selectedLyric: string;
}

interface Metadata {
  title: string;
  artist: string;
  album: string;
  length: string;
}

type ActiveTab = 'upload' | 'edit' | 'review';

// --- Main App Component ---
function App() {
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [lyricsText, setLyricsText] = useState<string>('');
  const [result, setResult] = useState<LyricLine[] | null>(null);
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('upload');

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
    setMetadata(null);

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
      
      const processedData = data.lyrics.map((row: any) => ({
        ...row,
        selectedLyric: row['Improved English'] || row['English']
      }));

      setResult(processedData);
      setMetadata(data.metadata);
      setActiveTab('edit');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch from the API.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLyricEdit = (rowIndex: number, field: keyof LyricLine, value: string) => {
    if (!result) return;
    const newData = [...result];
    newData[rowIndex] = { ...newData[rowIndex], [field]: value };
    setResult(newData);
  };

  const handleMetadataChange = (field: keyof Metadata, value: string) => {
    if (!metadata) return;
    setMetadata({ ...metadata, [field]: value });
  };

  const handleSelectionChange = (rowIndex: number, lyricSource: 'English' | 'Improved English') => {
    if (!result) return;
    const newData = [...result];
    const newRow = { ...newData[rowIndex] };
    newRow.selectedLyric = newRow[lyricSource];
    newData[rowIndex] = newRow;
    setResult(newData);
  };

  const lrcPreview = useMemo(() => {
    if (!result || !metadata) return "";
    
    const headers = [
      `[ar: ${metadata.artist}]`,
      `[al: ${metadata.album}]`,
      `[ti: ${metadata.title}]`,
      `[length: ${metadata.length}]`,
      `[tool: KowalskyExperto]`
    ].join('\n');

    const lyrics = result.map(row => {
      const centiseconds = row.milliseconds.substring(0, 2);
      const japanese = row.Japanese;
      const romaji = row.Romaji;
      const selected = row.selectedLyric;
      return `[${row.minutes}:${row.seconds}.${centiseconds}]${japanese} ${romaji} ${selected}`;
    }).join('\n');

    return `${headers}\n${lyrics}`;
  }, [result, metadata]);

  return (
    <div className="App">
      <header className="App-header"><h1>Lyric Processor</h1></header>
      
      <div className="tabs">
        <button className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}>1. Upload</button>
        <button className={`tab-button ${activeTab === 'edit' ? 'active' : ''}`} onClick={() => setActiveTab('edit')} disabled={!result}>2. Edit</button>
        <button className={`tab-button ${activeTab === 'review' ? 'active' : ''}`} onClick={() => setActiveTab('review')} disabled={!result}>3. Review LRC</button>
      </div>

      <main>
        {activeTab === 'upload' && (
          <div className="form-container">
            <form onSubmit={handleSubmit}>
              <div className="form-group"><label htmlFor="audio-file">Audio File</label><input id="audio-file" type="file" accept="audio/*" onChange={handleFileChange} /></div>
              <div className="form-group"><label htmlFor="lyrics-text">Lyrics</label><textarea id="lyrics-text" value={lyricsText} onChange={(e) => setLyricsText(e.target.value)} placeholder="Paste your lyrics here..." /></div>
              <button type="submit" className="submit-btn" disabled={isLoading}>{isLoading ? 'Processing...' : 'Generate'}</button>
            </form>
            {error && <p className="status-message error-message">Error: {error}</p>}
          </div>
        )}

        {activeTab === 'edit' && result && metadata && (
          <>
            <div className="metadata-container">
              <h2>Song Metadata</h2>
              <div className="form-group"><label>Title</label><input className="table-input" value={metadata.title} onChange={(e) => handleMetadataChange('title', e.target.value)} /></div>
              <div className="form-group"><label>Artist</label><input className="table-input" value={metadata.artist} onChange={(e) => handleMetadataChange('artist', e.target.value)} /></div>
              <div className="form-group"><label>Album</label><input className="table-input" value={metadata.album} onChange={(e) => handleMetadataChange('album', e.target.value)} /></div>
            </div>
            <div className="table-container">
              <h2>Editable Lyrics</h2>
              <table>
                <thead>
                  <tr>
                    <th>M</th><th>S</th><th>MS</th><th>Japanese</th><th>Romaji</th><th>Choice</th><th>Final LRC Lyric</th>
                  </tr>
                </thead>
                <tbody>
                  {result.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      <td className="col-time"><input className="table-input" value={row.minutes} onChange={(e) => handleLyricEdit(rowIndex, 'minutes', e.target.value)} /></td>
                      <td className="col-time"><input className="table-input" value={row.seconds} onChange={(e) => handleLyricEdit(rowIndex, 'seconds', e.target.value)} /></td>
                      <td className="col-time"><input className="table-input" value={row.milliseconds} onChange={(e) => handleLyricEdit(rowIndex, 'milliseconds', e.target.value)} /></td>
                      <td>{row.Japanese}</td>
                      <td><input className="table-input" value={row.Romaji} onChange={(e) => handleLyricEdit(rowIndex, 'Romaji', e.target.value)} /></td>
                      <td>
                        <div className="choice-container">
                          <label><input type="radio" name={`choice-${rowIndex}`} value="English" checked={row.selectedLyric === row.English} onChange={() => handleSelectionChange(rowIndex, 'English')} /> Eng</label>
                          <label><input type="radio" name={`choice-${rowIndex}`} value="Improved English" checked={row.selectedLyric === row['Improved English']} onChange={() => handleSelectionChange(rowIndex, 'Improved English')} /> Imp</label>
                        </div>
                      </td>
                      <td><input className="table-input" value={row.selectedLyric} onChange={(e) => handleLyricEdit(rowIndex, 'selectedLyric', e.target.value)} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {activeTab === 'review' && result && (
          <div className="lrc-preview-container">
            <h2>LRC Preview</h2>
            <pre>{lrcPreview}</pre>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;