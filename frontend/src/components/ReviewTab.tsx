import React from 'react';

interface ReviewTabProps {
  lrcPreview: string;
  handleFinalize: () => void;
  isFinalizing: boolean;
}

const ReviewTab: React.FC<ReviewTabProps> = ({ lrcPreview, handleFinalize, isFinalizing }) => {
  return (
    <div className="lrc-preview">
      <h2 className="lrc-preview__title">LRC Preview</h2>
      <pre className="lrc-preview__content">{lrcPreview}</pre>
      <button onClick={handleFinalize} className="lrc-preview__download" disabled={isFinalizing}>
        {isFinalizing ? 'Finalizing...' : 'Finalize & Download'}
      </button>
    </div>
  );
};

export default ReviewTab;