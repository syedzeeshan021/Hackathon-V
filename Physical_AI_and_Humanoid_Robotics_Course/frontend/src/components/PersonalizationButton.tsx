import React from 'react';
import { useUser } from '../../contexts/UserContext';
import { getPersonalizedContent } from '../../services/api';

interface PersonalizationButtonProps {
  chapterId: string; // The ID of the current chapter
}

const PersonalizationButton: React.FC<PersonalizationButtonProps> = ({ chapterId }) => {
  const { user, isLoading: userLoading } = useUser();
  const [isPersonalizing, setIsPersonalizing] = React.useState(false);
  const [personalizedContent, setPersonalizedContent] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handlePersonalize = async () => {
    if (!user || !user.token) { // Assuming user context provides a token
      setError("You must be logged in to personalize content.");
      return;
    }
    setIsPersonalizing(true);
    setError(null);
    try {
      const response = await getPersonalizedContent(chapterId, user.token);
      setPersonalizedContent(response.personalized_content);
      // In a real scenario, you'd likely update the DOM with this content
      console.log("Personalized content received:", response.personalized_content);
      alert("Content personalized! Check console for details (actual DOM update not implemented yet).");
    } catch (err: any) {
      setError(err.message || "Failed to personalize content.");
    } finally {
      setIsPersonalizing(false);
    }
  };

  if (userLoading) {
    return null; // Or a loading spinner
  }

  if (!user) {
    return null; // Only show button for logged-in users
  }

  return (
    <div style={{ margin: '20px 0', textAlign: 'center' }}>
      <button
        onClick={handlePersonalize}
        disabled={isPersonalizing}
        style={{
          padding: '10px 20px',
          fontSize: '1em',
          backgroundColor: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          opacity: isPersonalizing ? 0.7 : 1,
        }}
      >
        {isPersonalizing ? 'Personalizing...' : 'Personalize Content'}
      </button>
      {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
      {personalizedContent && <p style={{ marginTop: '10px', fontStyle: 'italic' }}>Personalization data ready.</p>}
    </div>
  );
};

export default PersonalizationButton;