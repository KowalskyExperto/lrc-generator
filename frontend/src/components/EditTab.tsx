import React from 'react';
import AutoGrowTextarea from './AutoGrowTextarea';

// Assuming these types are defined in a shared types file, 
// but defining here for simplicity for now.
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

interface EditTabProps {
  result: LyricLine[];
  metadata: Metadata;
  handleLyricEdit: (rowIndex: number, field: keyof LyricLine, value: string) => void;
  handleMetadataChange: (field: keyof Metadata, value: string) => void;
  handleSelectionChange: (rowIndex: number, lyricSource: 'English' | 'Improved English') => void;
  handleSetAllChoices: (lyricSource: 'English' | 'Improved English') => void;
  currentTime: number; // Add currentTime prop
}

const EditTab: React.FC<EditTabProps> = ({ 
  result, 
  metadata, 
  handleLyricEdit, 
  handleMetadataChange, 
  handleSelectionChange, 
  handleSetAllChoices,
  currentTime // Destructure currentTime
}) => {

  const getLyricTimeInSeconds = (line: LyricLine): number => {
    const minutes = parseInt(line.minutes || '0', 10);
    const seconds = parseInt(line.seconds || '0', 10);
    const milliseconds = parseInt(line.milliseconds || '0', 10);
    return minutes * 60 + seconds + milliseconds / 1000;
  };

  return (
    <>
      <div style={{ paddingBottom: '6rem' }}> {/* Wrapper for content with bottom padding */}
        <div className="metadata-editor card">
        <h2 className="metadata-editor__title">Song Metadata</h2>
        <div className="metadata-editor__group">
          <label>Title</label>
          <input className="metadata-editor__input" value={metadata.title} onChange={(e) => handleMetadataChange('title', e.target.value)} />
        </div>
        <div className="metadata-editor__group">
          <label>Artist</label>
          <input className="metadata-editor__input" value={metadata.artist} onChange={(e) => handleMetadataChange('artist', e.target.value)} />
        </div>
        <div className="metadata-editor__group">
          <label>Album</label>
          <input className="metadata-editor__input" value={metadata.album} onChange={(e) => handleMetadataChange('album', e.target.value)} />
        </div>
        </div>
        <div className="lyrics-editor">
          <h2 className="lyrics-editor__title">Editable Lyrics</h2>
          <table className="lyrics-editor__table">
            <thead>
              <tr>
                <th>M</th><th>S</th><th>MS</th><th>Japanese</th><th>Romaji</th>
                <th>
                  <div className="lyrics-editor__set-all-choice">
                    <button onClick={() => handleSetAllChoices('English')}>All Eng</button>
                    <button onClick={() => handleSetAllChoices('Improved English')}>All Imp</button>
                  </div>
                </th>
                <th>Final LRC Lyric</th>
              </tr>
            </thead>
            <tbody>
              {result.map((row, rowIndex) => {
                const lineStartTime = getLyricTimeInSeconds(row);
                const nextLine = result[rowIndex + 1];
                const lineEndTime = nextLine ? getLyricTimeInSeconds(nextLine) : Infinity;
                const isActive = currentTime >= lineStartTime && currentTime < lineEndTime;
                return (
                  <tr key={rowIndex} className={isActive ? 'lyrics-editor__row--active' : ''}>
                  <td><input className="lyrics-editor__input" value={row.minutes} onChange={(e) => handleLyricEdit(rowIndex, 'minutes', e.target.value)} /></td>
                  <td><input className="lyrics-editor__input" value={row.seconds} onChange={(e) => handleLyricEdit(rowIndex, 'seconds', e.target.value)} /></td>
                  <td><input className="lyrics-editor__input" value={row.milliseconds} onChange={(e) => handleLyricEdit(rowIndex, 'milliseconds', e.target.value)} /></td>
                  <td><div className="lyrics-editor__input">{row.Japanese}</div></td>
                  <td><AutoGrowTextarea className="lyrics-editor__input lyrics-editor__input--wrapping" value={row.Romaji} onChange={(e) => handleLyricEdit(rowIndex, 'Romaji', e.target.value)} rows={1} /></td>
                  <td>
                    {row.Japanese.trim() !== '' && (
                      <div className="lyrics-editor__choice">
                        <label><input type="radio" name={`choice-${rowIndex}`} value="English" checked={row.selectedLyric === row.English} onChange={() => handleSelectionChange(rowIndex, 'English')} /> Eng</label>
                        <label><input type="radio" name={`choice-${rowIndex}`} value="Improved English" checked={row.selectedLyric === row['Improved English']} onChange={() => handleSelectionChange(rowIndex, 'Improved English')} /> Imp</label>
                      </div>
                    )}
                  </td>
                  <td><AutoGrowTextarea className="lyrics-editor__input lyrics-editor__input--wrapping" value={row.selectedLyric} onChange={(e) => handleLyricEdit(rowIndex, 'selectedLyric', e.target.value)} rows={1} /></td>
                </tr>
              )})}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
};

export default EditTab;
