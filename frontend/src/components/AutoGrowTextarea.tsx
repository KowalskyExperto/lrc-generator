import React, { useRef, useEffect } from 'react';

// Inherit all props from a standard textarea element
interface AutoGrowTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const AutoGrowTextarea: React.FC<AutoGrowTextareaProps> = (props) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      // Reset the height to its default to get the correct scrollHeight
      textareaRef.current.style.height = 'auto';
      // Set the height to the scrollHeight to fit the content
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [props.value]); // Rerun this effect whenever the textarea's value changes

  return (
    <textarea
      {...props} // Pass all props (like value, onChange, className) to the textarea
      ref={textareaRef}
    />
  );
};

export default AutoGrowTextarea;
