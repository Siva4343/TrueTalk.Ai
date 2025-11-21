import React, { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";

const accentColors = [
  "#f97316",
  "#22c55e",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#3b82f6",
];

const API_HOST =
  import.meta.env.VITE_API_HOST ||
  `${window.location.hostname}:${import.meta.env.VITE_API_PORT || "8000"}`;

const API_PROTOCOL = window.location.protocol === "https:" ? "https" : "http";
const API_BASE_URL = `${API_PROTOCOL}://${API_HOST}/api/chat/messages/`;

const WS_PROTOCOL = window.location.protocol === "https:" ? "wss" : "ws";
const WS_URL =
  import.meta.env.VITE_WS_URL || `${WS_PROTOCOL}://${API_HOST}/ws/chat/`;

function App() {
  const [nameInput, setNameInput] = useState("");
  const [receiverInput, setReceiverInput] = useState("");
  const [messageInput, setMessageInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [quickMeetLink, setQuickMeetLink] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const scrollAnchorRef = useRef(null);
  const wsRef = useRef(null);

  // Load messages from backend on first render
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const response = await fetch(API_BASE_URL);
        const data = await response.json();

        const normalized = data.map((m) => ({
          id: m.id,
          author: m.sender_username || m.sender?.username || "Unknown",
          receiver: m.receiver_username || m.receiver?.username || null,
          text: m.text,
          time: new Date(m.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        }));

        setMessages(normalized);
      } catch (error) {
        console.error("Failed to load messages", error);
      }
    };

    fetchMessages();
  }, []);

  // WebSocket connection for real-time messaging
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("WebSocket Connected");
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === "chat_message" && data.message) {
            const msg = data.message;
            const newMessage = {
              id: msg.id,
              author: msg.sender_username,
              receiver: msg.receiver_username,
              text: msg.text,
              time: new Date(msg.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              }),
            };

            setMessages((prev) => [...prev, newMessage]);
          }
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          setIsConnected(false);
        };

        ws.onclose = () => {
          console.log("WebSocket Disconnected");
          setIsConnected(false);
          // Attempt to reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };
      } catch (error) {
        console.error("Failed to connect WebSocket:", error);
        setIsConnected(false);
      }
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const colorByAuthor = useMemo(() => {
    const map = new Map();
    let index = 0;

    messages.forEach((msg) => {
      if (!map.has(msg.author)) {
        map.set(msg.author, accentColors[index % accentColors.length]);
        index += 1;
      }
    });

    return map;
  }, [messages]);

  const resetInputs = () => {
    setMessageInput("");
  };

  const handleSend = async (event) => {
    event.preventDefault();
    if (!nameInput.trim() || !messageInput.trim() || isSending) return;

    setIsSending(true);

    // Send via WebSocket for real-time delivery
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(
          JSON.stringify({
            type: "chat_message",
            sender_username: nameInput.trim(),
            receiver_username: receiverInput.trim() || null,
            message: messageInput.trim(),
          })
        );
        resetInputs();
      } catch (error) {
        console.error("Failed to send via WebSocket:", error);
        // Fallback to REST API
        await sendViaAPI();
      }
    } else {
      // Fallback to REST API if WebSocket not connected
      await sendViaAPI();
    }

    setIsSending(false);
  };

  const sendViaAPI = async () => {
    try {
      const payload = {
        sender_username: nameInput.trim(),
        receiver_username: receiverInput.trim() || null,
        text: messageInput.trim(),
      };

      const response = await fetch(API_BASE_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const saved = await response.json();

      const newMessage = {
        id: saved.id,
        author: saved.sender_username || saved.sender?.username,
        receiver: saved.receiver_username || saved.receiver?.username || null,
        text: saved.text,
        time: new Date(saved.created_at).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      setMessages((prev) => [...prev, newMessage]);
      resetInputs();
    } catch (error) {
      console.error("Failed to send message", error);
      alert("Failed to send message. Check backend is running.");
    }
  };

  const generateMeetSlug = () =>
    `${Math.random().toString(36).substring(2, 6)}-${Date.now()
      .toString(36)
      .slice(-4)}`;

  const handleCall = (type) => {
    if (!nameInput.trim()) {
      alert("Enter your name before starting a call.");
      return;
    }
    alert(`${type} call started by ${nameInput.trim()} (demo action).`);
  };

  const handleQuickMeet = async () => {
    const hostName = nameInput.trim() || "Guest";
    const link = `https://truetalk.chat/${generateMeetSlug()}`;
    setQuickMeetLink(link);

    if (navigator?.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(link);
        alert(`Quick Meet started by ${hostName}.\nLink copied to clipboard!`);
        return;
      } catch (error) {
        // fall through
      }
    }
    alert(`Quick Meet started by ${hostName}.\nShare this link: ${link}`);
  };

  const copyQuickMeetLink = async () => {
    if (!quickMeetLink) return;
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(quickMeetLink);
      alert("Quick Meet link copied!");
    } else {
      window.prompt("Copy this Quick Meet link:", quickMeetLink);
    }
  };

  const handleResetChat = () => {
    setMessages([]);
    setQuickMeetLink("");
  };

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="app">
      <div className="chat-shell">
        <header className="chat-header">
          <div>
            <p className="chat-title">TrueTalk ChatRoom</p>
            <p className="chat-subtitle">
              Greet the team, drop updates, or kick off a call instantly.
            </p>
          </div>
          <div className="header-actions">
            <button
              className="action-btn voice-call"
              onClick={() => handleCall("Voice")}
            >
              📞 Voice Call
            </button>
            <button
              className="action-btn video-call"
              onClick={() => handleCall("Video")}
            >
              🎥 Video Call
            </button>
            <button
              className="action-btn quick-meet"
              type="button"
              onClick={handleQuickMeet}
            >
              ⚡ Quick Meet
            </button>
          </div>
        </header>

        <main className="chat-body">
          <section className="composer-card">
            <form className="composer-form" onSubmit={handleSend}>
              <div style={{ display: "flex", gap: "12px" }}>
                <label className="field" style={{ flex: 1 }}>
                  <span className="field-label">Your Name</span>
                  <input
                    type="text"
                    placeholder="Enter your display name"
                    value={nameInput}
                    onChange={(event) => setNameInput(event.target.value)}
                  />
                </label>
                <label className="field" style={{ flex: 1 }}>
                  <span className="field-label">Send To (optional - leave empty for group chat)</span>
                  <input
                    type="text"
                    placeholder="Enter receiver username"
                    value={receiverInput}
                    onChange={(event) => setReceiverInput(event.target.value)}
                  />
                </label>
              </div>
              <label className="field">
                <span className="field-label">Message</span>
                <textarea
                  rows="3"
                  placeholder="Write something nice for the team..."
                  value={messageInput}
                  onChange={(event) => setMessageInput(event.target.value)}
                />
              </label>
              {isConnected ? (
                <div style={{ 
                  padding: "8px 12px", 
                  background: "#d1fae5", 
                  borderRadius: "8px", 
                  fontSize: "0.85rem",
                  color: "#065f46",
                  fontWeight: 600
                }}>
                  ✓ Connected - Real-time messaging active
                </div>
              ) : (
                <div style={{ 
                  padding: "8px 12px", 
                  background: "#fee2e2", 
                  borderRadius: "8px", 
                  fontSize: "0.85rem",
                  color: "#991b1b",
                  fontWeight: 600
                }}>
                  ⚠ Disconnected - Using REST API fallback
                </div>
              )}
              <div className="composer-footer">
                <div className="typing-preview">
                  {messageInput
                    ? `${nameInput || "You"} is typing: ${messageInput}`
                    : "Start typing to preview your message..."}
                </div>
                {quickMeetLink && (
                  <div className="meet-banner">
                    <div>
                      <p className="meet-label">Quick Meet link ready</p>
                      <p className="meet-link">{quickMeetLink}</p>
                    </div>
                    <button
                      type="button"
                      className="copy-link-btn"
                      onClick={copyQuickMeetLink}
                    >
                      Copy Link
                    </button>
                  </div>
                )}
                <button
                  type="submit"
                  className="send-btn"
                  disabled={!nameInput.trim() || !messageInput.trim()}
                >
                  {isSending ? "Sending..." : "Send Message"}
                </button>
              </div>
            </form>
          </section>

          <section className="messages-card">
            <div className="messages-header">
              <div>
                <p className="messages-title">Live Conversation</p>
                <p className="messages-subtitle">
                  {messages.length} message
                  {messages.length === 1 ? "" : "s"} so far
                </p>
              </div>
              <button className="clear-btn" onClick={handleResetChat}>
                Reset Chat (local only)
              </button>
            </div>
            <div className="messages-scroll">
              {messages.map((message) => (
                <div className="message-row" key={message.id}>
                  <div
                    className="message-avatar"
                    style={{ background: colorByAuthor.get(message.author) }}
                  >
                    {message.author.charAt(0).toUpperCase()}
                  </div>
                  <div className="message-content">
                    <div className="message-meta">
                      <span className="message-author">
                        {message.author}
                        {message.receiver && (
                          <span style={{ 
                            marginLeft: "8px", 
                            fontSize: "0.75rem", 
                            color: "#6b7280",
                            fontWeight: "normal"
                          }}>
                            → {message.receiver}
                          </span>
                        )}
                      </span>
                      <span className="message-time">{message.time}</span>
                    </div>
                    <p className="message-text">{message.text}</p>
                  </div>
                </div>
              ))}
              <div ref={scrollAnchorRef} />
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;