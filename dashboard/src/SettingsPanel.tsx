import { FormEvent, useState } from "react";
import { setPassword } from "./api";

export default function SettingsPanel() {
  const [password, setPasswordValue] = useState("");
  const [confirm, setConfirm] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setMessage("");
    setError("");
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    try {
      await setPassword(password);
      setMessage("Password updated.");
      setPasswordValue("");
      setConfirm("");
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div className="card" style={{ maxWidth: 420 }}>
      <h2>Settings</h2>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.75rem", marginTop: "1rem" }}>
        <input
          type="password"
          placeholder="New password"
          value={password}
          onChange={(e) => setPasswordValue(e.target.value)}
        />
        <input
          type="password"
          placeholder="Confirm password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
        />
        <button type="submit">Update password</button>
      </form>
      {message && <p style={{ color: "#0f766e" }}>{message}</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </div>
  );
}
