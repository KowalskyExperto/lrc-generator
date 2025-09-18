import React, { useState, useMemo, useEffect } from 'react';
import './App.css';
import UploadTab from './components/UploadTab';
import EditTab from './components/EditTab';
import ReviewTab from './components/ReviewTab';
import AudioPlayer from './components/AudioPlayer'; // Import AudioPlayer

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

declare global {
  interface Window {
    config?: {
      API_BASE_URL?: string;
    };
  }
}

const API_BASE_URL = window.config?.API_BASE_URL || 'http://localhost:8000';

// --- Main App Component ---
function App() {
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [lyricsText, setLyricsText] = useState<string>('');
  const [result, setResult] = useState<LyricLine[] | null>(null);
  const [originalResult, setOriginalResult] = useState<LyricLine[] | null>(null);
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isFinalizing, setIsFinalizing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('upload');
  const [currentTime, setCurrentTime] = useState<number>(0); // New state for current audio time
  const [selectedLineIndex, setSelectedLineIndex] = useState<number | null>(null);

  const handleAudioFileChange = (file: File | null) => {
    setAudioFile(file);
  };

  const audioSrc = useMemo(() => {
    if (audioFile) {
      return URL.createObjectURL(audioFile);
    }
    return null;
  }, [audioFile]);

  // Clean up the object URL when the component unmounts or audioFile changes
  useEffect(() => {
    return () => {
      if (audioSrc) {
        URL.revokeObjectURL(audioSrc);
      }
    };
  }, [audioSrc]);

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  const handleLineSelect = (index: number) => {
    setSelectedLineIndex(index);
  };

  const handleSetTimestamp = (time: number) => {
    if (selectedLineIndex === null || !result) return;

    const minutes = Math.floor(time / 60).toString().padStart(2, '0');
    const seconds = Math.floor(time % 60).toString().padStart(2, '0');
    const milliseconds = Math.round((time % 1) * 1000).toString().padStart(3, '0');

    const newData = [...result];
    const updatedLine = { ...newData[selectedLineIndex] };

    updatedLine.minutes = minutes;
    updatedLine.seconds = seconds;
    updatedLine.milliseconds = milliseconds;

    newData[selectedLineIndex] = updatedLine;
    setResult(newData);
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
      const response = await fetch(`${API_BASE_URL}/process-lyrics`, {
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
      setOriginalResult(processedData);
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

    // Validate and update timestamp fields
    if (field === 'minutes' || field === 'seconds') {
      if (!/^\d*$/.test(value) || value.length > 2) {
        return; // Only allow numbers, max 2 digits
      }
    } else if (field === 'milliseconds') {
      if (!/^\d*$/.test(value) || value.length > 3) {
        return; // Only allow numbers, max 3 digits
      }
    }

    // Create a new array and update the specific field for the specific line
    const newData = [...result];
    newData[rowIndex] = {
      ...newData[rowIndex],
      [field]: value,
    };

    setResult(newData);
  };

  const handleTimestampBlur = (rowIndex: number, field: 'minutes' | 'seconds' | 'milliseconds') => {
    if (!result) return;

    const line = result[rowIndex];
    const value = line[field];
    let padLength: number | null = null;

    if (field === 'minutes' || field === 'seconds') {
      padLength = 2;
    } else if (field === 'milliseconds') {
      padLength = 3;
    }

    if (padLength) {
      const formattedValue = value.padStart(padLength, '0');
      if (formattedValue !== value) {
        const newData = [...result];
        newData[rowIndex] = { ...newData[rowIndex], [field]: formattedValue };
        setResult(newData);
      }
    }
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

  const handleSetAllChoices = (lyricSource: 'English' | 'Improved English') => {
    if (!result) return;
    const newData = result.map(row => ({
      ...row,
      selectedLyric: row[lyricSource]
    }));
    setResult(newData);
  };

  const handleFinalize = async () => {
    if (!result || !metadata || !audioFile) {
      setError('Missing data to finalize.');
      return;
    }

    setIsFinalizing(true);
    setError(null);

    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('lyrics_data', JSON.stringify(result));
    formData.append('metadata', JSON.stringify(metadata));

    try {
      const response = await fetch(`${API_BASE_URL}/generate-and-embed`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate final file.');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${metadata.artist} - ${metadata.title}.flac` || 'song.flac';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();

    } catch (err: any) {
      setError(err.message || 'Failed to finalize.');
    } finally {
      setIsFinalizing(false);
    }
  };

  const handleResetAll = () => {
    if (!originalResult) return;
    setResult([...originalResult]);
  };

  const handleResetTimestamps = () => {
    if (!result || !originalResult) return;
    const newData = result.map((line, index) => ({
      ...line,
      minutes: originalResult[index].minutes,
      seconds: originalResult[index].seconds,
      milliseconds: originalResult[index].milliseconds,
    }));
    setResult(newData);
  };

  const handleResetRomaji = () => {
    if (!result || !originalResult) return;
    const newData = result.map((line, index) => ({
      ...line,
      Romaji: originalResult[index].Romaji,
    }));
    setResult(newData);
  };

  const handleResetLine = (rowIndex: number) => {
    if (!result || !originalResult) return;
    const newData = [...result];
    newData[rowIndex] = { ...originalResult[rowIndex] };
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
      <header className="app__header"><h1>Lyric Processor</h1></header>
      
      <div className="tabs">
        <button className={`tabs__button ${activeTab === 'upload' ? 'tabs__button--active' : ''}`} onClick={() => setActiveTab('upload')}>1. Upload</button>
        <button className={`tabs__button ${activeTab === 'edit' ? 'tabs__button--active' : ''}`} onClick={() => setActiveTab('edit')} disabled={!result}>2. Edit</button>
        <button className={`tabs__button ${activeTab === 'review' ? 'tabs__button--active' : ''}`} onClick={() => setActiveTab('review')} disabled={!result}>3. Review LRC</button>
      </div>

      <main className="app__main-content">
        {activeTab === 'upload' && (
          <UploadTab 
            handleSubmit={handleSubmit}
            onAudioFileChange={handleAudioFileChange}
            setLyricsText={setLyricsText}
            lyricsText={lyricsText}
            isLoading={isLoading}
            error={error}
          />
        )}

        {activeTab === 'edit' && result && metadata && (
          <EditTab 
            result={result}
            metadata={metadata}
            handleLyricEdit={handleLyricEdit}
            handleMetadataChange={handleMetadataChange}
            handleSelectionChange={handleSelectionChange}
            handleSetAllChoices={handleSetAllChoices}
            currentTime={currentTime}
            selectedLineIndex={selectedLineIndex}
            handleLineSelect={handleLineSelect}
            handleResetAll={handleResetAll}
            handleResetTimestamps={handleResetTimestamps}
            handleResetRomaji={handleResetRomaji}
            handleResetLine={handleResetLine}
            handleTimestampBlur={handleTimestampBlur}
          />
        )}

        {activeTab === 'review' && result && (
          <ReviewTab 
            lrcPreview={lrcPreview}
            handleFinalize={handleFinalize}
            isFinalizing={isFinalizing}
          />
        )}
      </main>

      {/* Render AudioPlayer globally */}
      <AudioPlayer 
        audioSrc={audioSrc} 
        onTimeUpdate={handleTimeUpdate} 
        onSetTimestamp={handleSetTimestamp}
        isLineSelected={selectedLineIndex !== null}
      />
    </div>
  );
}

export default App;
