import { useState, useEffect } from "react";

export function useLiveState() {
  const [state, setState] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onopen = () => {
      console.log("Live state connected");
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        setState(data);
      } catch (error) {
        console.error("Invalid live state:", error);
      }
    };

    ws.onerror = () => {
      // Connection errors are handled by onclose.
    };

    ws.onclose = () => {
      console.log("Live state connection closed");
    };

    return () => {
      // Only close a connection that has actually opened.
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  return state;
}