import React from 'react';
import VoiceInterface from './components/VoiceInterface';
import './index.css';

function App() {
    return (
        <div className="app-container">
            <header>
                <h1>Voice AI Demo</h1>
                <p>Powered by Deepgram, Groq & Sarvam</p>
            </header>
            <main>
                <VoiceInterface />
            </main>
        </div>
    );
}

export default App;
