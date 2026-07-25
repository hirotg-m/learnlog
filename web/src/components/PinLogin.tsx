import { FormEvent, useEffect, useState } from "react";

import { apiClient } from "../lib/apiClient";
import "./PinLogin.css";

type PinLoginProps = {
  onSuccess: () => void;
};

export function PinLogin(props: PinLoginProps): JSX.Element {
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lockedUntil, setLockedUntil] = useState<number | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState(0);

  useEffect(() => {
    if (lockedUntil === null) {
      return;
    }
    const tick = (): void => {
      const remaining = Math.max(0, Math.ceil((lockedUntil - Date.now()) / 1000));
      setRemainingSeconds(remaining);
      if (remaining === 0) {
        setLockedUntil(null);
      }
    };
    tick();
    const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [lockedUntil]);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);

    if (!/^\d{8}$/.test(pin)) {
      setError("PIN は 8 桁の数字で入力してください");
      return;
    }

    setIsLoading(true);
    try {
      await apiClient.login(pin);
      props.onSuccess();
    } catch (errorValue) {
      const retryAfter = apiClient.retryAfterSeconds(errorValue);
      if (retryAfter !== undefined) {
        setLockedUntil(Date.now() + retryAfter * 1000);
      }
      setError(apiClient.errorMessage(errorValue));
    } finally {
      setIsLoading(false);
    }
  }

  const isLocked = lockedUntil !== null && remainingSeconds > 0;

  return (
    <main className="pinLogin">
      <section className="pinCard">
        <p className="pinCaption">LEARNLOG</p>
        <h1>8桁PINでログイン</h1>
        <p className="pinSubtext">毎日の学習を、秒で記録する。</p>
        <form onSubmit={onSubmit} className="pinForm">
          <input
            value={pin}
            onChange={(event) => setPin(event.target.value)}
            inputMode="numeric"
            pattern="[0-9]{8}"
            maxLength={8}
            placeholder="12345678"
            aria-label="PIN"
            disabled={isLocked}
          />
          <button type="submit" disabled={isLoading || isLocked}>
            {isLoading ? "認証中..." : "ログイン"}
          </button>
        </form>
        {error && <p className="pinError">{error}</p>}
        {isLocked && (
          <p className="pinError">あと {remainingSeconds} 秒後に再度お試しください</p>
        )}
      </section>
    </main>
  );
}