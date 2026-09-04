import { useEffect, useRef, useState } from "react";
import AgoraRTC from "agora-rtc-sdk-ng";
import VoiceOrb from "../components/VoiceOrb";
import { startCallingBuddy, stopCallingBuddy } from "../services/api";

const SPEECH_THRESHOLD = 5;
const SPEECH_END_DELAY_MS = 1200;

export default function CallingBuddy({ navigate }) {
  const [state, setState] = useState("idle");
  const [notice, setNotice] = useState("Ready to talk?");
  const [processingSeconds, setProcessingSeconds] = useState(0);

  const client = useRef();
  const track = useRef();
  const session = useRef();

  const localSpeech = useRef(false);
  const remoteSpeaking = useRef(false);
  const silenceTimer = useRef();

  const processingTimer = useRef();
  const processingStartedAt = useRef();

  const clearSpeechTimer = () => {
    if (silenceTimer.current) {
      clearTimeout(silenceTimer.current);
      silenceTimer.current = undefined;
    }
  };

  const clearProcessingTimer = () => {
    if (processingTimer.current) {
      clearInterval(processingTimer.current);
      processingTimer.current = undefined;
    }

    processingStartedAt.current = undefined;
    setProcessingSeconds(0);
  };

  const startProcessingTimer = () => {
    clearProcessingTimer();

    processingStartedAt.current = Date.now();
    setProcessingSeconds(0);

    processingTimer.current = setInterval(() => {
      if (!processingStartedAt.current) return;

      const elapsed = Math.floor(
        (Date.now() - processingStartedAt.current) / 1000,
      );

      setProcessingSeconds(elapsed);
    }, 250);
  };

  const cleanup = async () => {
    clearSpeechTimer();
    clearProcessingTimer();

    localSpeech.current = false;
    remoteSpeaking.current = false;

    track.current?.close();
    track.current = null;

    if (client.current) {
      await client.current.leave();
      client.current = null;
    }
  };

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  const start = async () => {
    try {
      setState("connecting");
      setNotice("Requesting microphone access…");

      track.current = await AgoraRTC.createMicrophoneAudioTrack();

      session.current = await startCallingBuddy();

      client.current = AgoraRTC.createClient({
        mode: "rtc",
        codec: "vp8",
      });

     client.current.on("user-published", async (user, type) => {
  await client.current.subscribe(user, type);

  if (type === "audio") {
    clearSpeechTimer();

    localSpeech.current = false;

    user.audioTrack.play();

    // Do NOT mark the agent as speaking here.
    // user-published only means the audio track was published.
  }
});

      client.current.on("user-unpublished", () => {
        remoteSpeaking.current = false;

        setState("listening");
        setNotice(
          "Listening… Speak naturally in English, Hindi, or Hinglish.",
        );
      });

     client.current.on("volume-indicator", (volumes) => {
  const local = volumes.find(
    (volume) =>
      String(volume.uid) === String(session.current?.user_uid),
  );

  const remote = volumes.find(
    (volume) =>
      String(volume.uid) !== String(session.current?.user_uid),
  );

  // Detect actual agent speech from its audio level.
  if (remote && remote.level > SPEECH_THRESHOLD) {
    remoteSpeaking.current = true;

    clearSpeechTimer();
    clearProcessingTimer();

    setState("speaking");
    setNotice("Calling Buddy is speaking…");

    return;
  }

  // Agent audio is currently quiet.
  if (remoteSpeaking.current) {
    remoteSpeaking.current = false;

    if (localSpeech.current) {
      setState("working");
      setNotice("Processing your request…");
      startProcessingTimer();
    } else {
      setState("listening");
      setNotice(
        "Listening… Speak naturally in English, Hindi, or Hinglish.",
      );
    }
  }

  // Detect the user's speech.
  if (local && local.level > SPEECH_THRESHOLD) {
    localSpeech.current = true;

    clearSpeechTimer();
    clearProcessingTimer();

    setState("listening");
    setNotice("Listening…");

    return;
  }

  // User stopped speaking.
  if (localSpeech.current && !silenceTimer.current) {
    silenceTimer.current = setTimeout(() => {
      silenceTimer.current = undefined;

      if (!remoteSpeaking.current) {
        setState("working");
        setNotice("Processing your request…");
        startProcessingTimer();
      }
    }, SPEECH_END_DELAY_MS);
  }
});

      await client.current.join(
        session.current.app_id,
        session.current.channel,
        session.current.rtc_token,
        session.current.user_uid,
      );

      await client.current.enableAudioVolumeIndicator();

      await client.current.publish([track.current]);

      setState("listening");
      setNotice(
        "Listening… Speak naturally in English, Hindi, or Hinglish.",
      );
    } catch (error) {
      console.error(error);

      await cleanup();

      setState("error");

      setNotice(
        error?.name === "NotAllowedError"
          ? "Microphone access was denied. Please allow it and try again."
          : "Unable to connect to Calling Buddy. Please try again.",
      );
    }
  };

  const stop = async () => {
    try {
      if (session.current?.session_id) {
        await stopCallingBuddy(session.current.session_id);
      }
    } catch (error) {
      console.error(error);
    } finally {
      await cleanup();

      session.current = null;

      setState("ended");
      setNotice("Conversation ended.");
    }
  };

  const workingNotice =
    processingSeconds >= 8
      ? `Still working… ${processingSeconds}s`
      : `Processing your request… ${processingSeconds}s`;

  return (
    <main className="page buddy-page">
      <button
        className="back-button"
        onClick={() => {
          stop();
          navigate("/");
        }}
      >
        ← Back to agents
      </button>

      <div className="buddy-header">
        <div>
          <p className="eyebrow">CALLING BUDDY</p>

          <h1>
            Your multilingual <em>voice companion.</em>
          </h1>
        </div>

        <span className={`state-badge ${state}`}>
          {state}
        </span>
      </div>

      <section className="voice-session">
        <VoiceOrb state={state} />

        {state === "working" ? (
          <div className="processing-status">
            <p className="session-notice">
              {workingNotice}
            </p>

            <div className="processing-timer">
              {processingSeconds}s
            </div>

            <p className="processing-help">
              Please wait while Calling Buddy completes the request.
            </p>
          </div>
        ) : (
          <p className="session-notice">
            {notice}
          </p>
        )}

        <div className="language-row">
          <span>Selected language</span>

          <strong>
            English / Hindi / Hinglish
          </strong>
        </div>

        <div className="session-actions">
          {["idle", "ended", "error"].includes(state) ? (
            <button
              className="primary-button"
              onClick={start}
            >
              Start conversation
            </button>
          ) : (
            <button
              className="secondary-button"
              onClick={stop}
            >
              Stop conversation
            </button>
          )}
        </div>
      </section>

      <section className="transcript">
        <div className="section-title">
          <h2>Live conversation</h2>
          <span>Voice session</span>
        </div>

        <div className="transcript-row">
          <span>E</span>

          <p>
            Hello! Welcome to Calling Buddy. Which language
            would you like to speak?
          </p>
        </div>

        <p className="transcript-hint">
          Transcript events will appear here when enabled
          in the Agora session.
        </p>
      </section>
    </main>
  );
}