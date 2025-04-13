import React, {useState} from 'react';
import './App.css';  // Import your CSS file to style the app
import Spline from '@splinetool/react-spline'; // Import Spline for 3D animation
import Chatbot from './chatbot';  // Import the Chatbot component


const App = () => {
  // Function to handle button click
  const [isChatbotVisible, setIsChatbotVisible] = useState(false);

  // Function to handle the button click and toggle visibility
  const handleButtonClick = () => {
    setIsChatbotVisible(!isChatbotVisible);
  };

  return (

    <div className="app-container">
      {/* Spline 3D scene */}
      <div className="spline-container">
        <Spline scene="https://prod.spline.design/1K5yR1IhZMrEZbyV/scene.splinecode" />
      </div>
      <button className="start-button" onClick={handleButtonClick}>
        Let's Start
      </button>
        {/* Conditionally render the Chatbot */}
        {isChatbotVisible && <Chatbot />}
    </div>
  );
};

export default App;
