import { useState, useRef, useEffect, useCallback } from 'react';

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const mediaRecorder = useRef(null);
  const socket = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    socket.current = new WebSocket('ws://localhost:8000/ws/audio');

    socket.current.onopen = () => {
      console.log('WebSocket Connected');
      setIsConnected(true);
    };

    socket.current.onclose = () => {
      console.log('WebSocket Disconnected');
      setIsConnected(false);
    };

    socket.current.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'audio') {
        // Play audio
        const audio = new Audio(`data:audio/wav;base64,${data.data}`);
        audio.play();
        setTranscript(prev => [...prev, { role: 'ai', text: data.text }]);
      }
    };

    return () => {
      if (socket.current) {
        socket.current.close();
      }
    };
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);

      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0 && socket.current && socket.current.readyState === WebSocket.OPEN) {
          socket.current.send(event.data);
        }
      };

      mediaRecorder.current.start(250); // Send chunks every 250ms
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      // Stop all tracks
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
    }
  }, [isRecording]);

  return {
    isRecording,
    isConnected,
    startRecording,
    stopRecording,
    transcript
  };
}
