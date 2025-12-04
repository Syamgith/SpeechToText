import React, { useEffect, useRef } from 'react';
import { Mic, MicOff, Activity } from 'lucide-react';
import { useAudioRecorder } from '../hooks/useAudioRecorder';

export default function VoiceInterface() {
    const { isRecording, isConnected, startRecording, stopRecording, transcript } = useAudioRecorder();
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [transcript]);

    return (
        <div className="voice-interface">
            <div className="status-bar">
                <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
                    {isConnected ? 'Connected' : 'Connecting...'}
                </div>
            </div>

            <div className="visualizer-container">
                <div className={`visualizer ${isRecording ? 'active' : ''}`}>
                    <div className="wave"></div>
                    <div className="wave"></div>
                    <div className="wave"></div>
                </div>
            </div>

            <div className="transcript-container" ref={scrollRef}>
                {transcript.map((msg, index) => (
                    <div key={index} className={`message ${msg.role}`}>
                        <span className="role-label">{msg.role === 'user' ? 'You' : 'AI'}</span>
                        <p>{msg.text}</p>
                    </div>
                ))}
                {transcript.length === 0 && (
                    <div className="empty-state">Start speaking to see the conversation here...</div>
                )}
            </div>

            <div className="controls">
                <button
                    className={`record-button ${isRecording ? 'recording' : ''}`}
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={!isConnected}
                >
                    {isRecording ? <MicOff size={32} /> : <Mic size={32} />}
                </button>
                <p className="instruction">
                    {isRecording ? 'Listening...' : 'Tap to Speak'}
                </p>
            </div>
        </div>
    );
}
