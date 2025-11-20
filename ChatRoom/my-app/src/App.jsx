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

const API_BASE_URL = "http://127.0.0.1:8000/api/chat/messages/";

function App() {
  const [nameInput, setNameInput] = useState("");
  const [messageInput, setMessageInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [quickMeetLink, setQuickMeetLink] = useState("");
  const scrollAnchorRef = useRef(null);

  // Load messages from backend on first render
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const response = await fetch(API_BASE_URL);
        const data = await response.json();

        const normalized = data.map((m) => ({
          id: m.id,
          author: m.author,
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

    const payload = {
      author: nameInput.trim(),
      text: messageInput.trim(),
    };

    try {
      const response = await fetch(API_BASE_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const saved = await response.json();

      const newMessage = {
        id: saved.id,
        author: saved.author,
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
    } finally {
      setIsSending(false);
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
              <label className="field">
                <span className="field-label">Name</span>
                <input
                  type="text"
                  placeholder="Enter your display name"
                  value={nameInput}
                  onChange={(event) => setNameInput(event.target.value)}
                />
              </label>
              <label className="field">
                <span className="field-label">Message</span>
                <textarea
                  rows="3"
                  placeholder="Write something nice for the team..."
                  value={messageInput}
                  onChange={(event) => setMessageInput(event.target.value)}
                />
              </label>
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
                      <span className="message-author">{message.author}</span>
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