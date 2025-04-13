<<<<<<< HEAD
import React, {useState} from 'react';
import './App.css';  // Import your CSS file to style the app
import Spline from '@splinetool/react-spline'; // Import Spline for 3D animation
import Chatbot from './chatbot';  // Import the Chatbot component
=======
import { useState } from 'react'

>>>>>>> a429895fa7070ee5304d2db04477722843a09f1b

const App = () => {
  // Function to handle button click
  const [isChatbotVisible, setIsChatbotVisible] = useState(false);

  // Function to handle the button click and toggle visibility
  const handleButtonClick = () => {
    setIsChatbotVisible(!isChatbotVisible);
  };

  return (
<<<<<<< HEAD
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
=======
    <>
      <h1>Hello </h1>
      
    </>
  )
}
>>>>>>> a429895fa7070ee5304d2db04477722843a09f1b

export default App;
