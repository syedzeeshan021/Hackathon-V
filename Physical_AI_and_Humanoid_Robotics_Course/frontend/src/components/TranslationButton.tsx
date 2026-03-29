import React from 'react';
import { useUser } from '../../contexts/UserContext';
import { getTranslatedContent } from '../../services/api';

interface TranslationButtonProps {
  chapterContent: string; // The content of the current chapter to translate
}

const TranslationButton: React.FC<TranslationButtonProps> = ({ chapterContent }) => {
  const { user, isLoading: userLoading } = useUser();
  const [isTranslating, setIsTranslating] = React.useState(false);
  const [translatedContent, setTranslatedContent] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleTranslate = async () => {
    if (!user || !user.token) { // Assuming user context provides a token
      setError("You must be logged in to translate content.");
      return;
    }
    setIsTranslating(true);
    setError(null);
    try {
      const response = await getTranslatedContent(chapterContent, "ur", user.token); // "ur" for Urdu
      setTranslatedContent(response.translated_content);
      // In a real scenario, you'd likely update the DOM with this content
      console.log("Translated content received:", response.translated_content);
      alert("Content translated! Check console for details (actual DOM update not implemented yet).");
    } catch (err: any) {
      setError(err.message || "Failed to translate content.");
    } finally {
      setIsTranslating(false);
    }
  };

  if (userLoading) {
    return null; // Or a loading spinner
  }

  // Optionally, only show button for logged-in users
  // if (!user) {
  //   return null;
  // }

  return (
    <div style={{ margin: '20px 0', textAlign: 'center' }}>
      <button
        onClick={handleTranslate}
        disabled={isTranslating}
        style={{
          padding: '10px 20px',
          fontSize: '1em',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          opacity: isTranslating ? 0.7 : 1,
        }}
      >
        {isTranslating ? 'Translating...' : 'Translate to Urdu'}
      </button>
      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
      {translatedContent && <p style={{ marginTop: '10px', fontStyle: 'italic' }}>Translation data ready.</p>}
    </div>
  );
};

export default TranslationButton;