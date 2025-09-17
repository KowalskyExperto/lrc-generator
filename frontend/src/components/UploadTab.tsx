import React from 'react';

interface UploadTabProps {
  handleSubmit: (event: React.FormEvent) => void;
  onAudioFileChange: (file: File | null) => void;
  setLyricsText: (text: string) => void;
  lyricsText: string;
  isLoading: boolean;
  error: string | null;
}

const UploadTab: React.FC<UploadTabProps> = ({ 
  handleSubmit, 
  onAudioFileChange, 
  setLyricsText, 
  lyricsText, 
  isLoading, 
  error 
}) => {
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onAudioFileChange(event.target.files ? event.target.files[0] : null);
  };

  return (
    <form className="upload-form card" onSubmit={handleSubmit}>
      <div className="upload-form__group">
        <label htmlFor="audio-file">Audio File</label>
        <input id="audio-file" type="file" accept="audio/*" onChange={handleFileChange} />
      </div>
      <div className="upload-form__group">
        <label htmlFor="lyrics-text">Lyrics</label>
        <textarea 
          id="lyrics-text" 
          value={lyricsText} 
          onChange={(e) => setLyricsText(e.target.value)} 
          placeholder="Paste your lyrics here..." 
        />
      </div>
      <button type="submit" className="upload-form__submit" disabled={isLoading}>
        {isLoading ? 'Processing...' : 'Generate'}
      </button>
      {error && <p className="app__status-message app__status-message--error">Error: {error}</p>}
    </form>
  );
};

export default UploadTab;