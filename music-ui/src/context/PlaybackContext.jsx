import {
  createContext,
  useContext,
  useRef,
  useState,
  useEffect,
  useCallback,
} from "react";

const PlaybackContext = createContext(null);

export function PlaybackProvider({ children }) {
  const audioRef = useRef(null);

  /* ===================== STATE ===================== */

  const [queue, setQueue] = useState([]);       // array of track IDs
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [playing, setPlaying] = useState(false);

  // preview = true means "do not affect queue navigation"
  const [previewTrackId, setPreviewTrackId] = useState(null);

  const currentTrackId =
    previewTrackId ??
    (currentIndex >= 0 ? queue[currentIndex] : null);

  /* ===================== AUDIO LIFECYCLE ===================== */

  useEffect(() => {
    if (!audioRef.current) return;

    if (!currentTrackId) {
      audioRef.current.pause();
      audioRef.current.src = "";
      return;
    }

    audioRef.current.src =
      `http://127.0.0.1:8000/audio/${currentTrackId}`;

    if (playing) {
      audioRef.current.play().catch(() => {});
    }
  }, [currentTrackId, playing]);

  /* ===================== COMMANDS ===================== */

  const play = useCallback(() => {
    setPlaying(true);
  }, []);

  const pause = useCallback(() => {
    setPlaying(false);
  }, []);

  const playTrack = useCallback(
    (id, { preview = false } = {}) => {
      if (preview) {
        setPreviewTrackId(id);
        setPlaying(true);
        return;
      }

      const index = queue.indexOf(id);
      if (index !== -1) {
        setPreviewTrackId(null);
        setCurrentIndex(index);
        setPlaying(true);
      }
    },
    [queue]
  );

  const stopPreview = useCallback(() => {
    setPreviewTrackId(null);
  }, []);

  const next = useCallback(() => {
    if (previewTrackId) return;

    setCurrentIndex(i =>
      i + 1 < queue.length ? i + 1 : i
    );
  }, [queue.length, previewTrackId]);

  const prev = useCallback(() => {
    if (previewTrackId) return;

    setCurrentIndex(i =>
      i > 0 ? i - 1 : i
    );
  }, [previewTrackId]);

  const seekBy = useCallback(seconds => {
    if (!audioRef.current) return;

    audioRef.current.currentTime =
      Math.max(0, audioRef.current.currentTime + seconds);
  }, []);

  /* ===================== QUEUE CONTROL ===================== */

  const setPlaybackQueue = useCallback((ids, startId = null) => {
    setQueue(ids);

    if (startId != null) {
      const idx = ids.indexOf(startId);
      if (idx !== -1) setCurrentIndex(idx);
    }
  }, []);

  /* ===================== END OF TRACK ===================== */

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onEnded = () => {
      if (previewTrackId) {
        setPreviewTrackId(null);
        setPlaying(false);
      } else {
        next();
      }
    };

    audio.addEventListener("ended", onEnded);
    return () => audio.removeEventListener("ended", onEnded);
  }, [next, previewTrackId]);

  /* ===================== CONTEXT VALUE ===================== */

  const value = {
    // state
    queue,
    currentIndex,
    currentTrackId,
    playing,
    isPreviewing: !!previewTrackId,

    // commands
    play,
    pause,
    playTrack,
    stopPreview,
    next,
    prev,
    seekBy,
    setPlaybackQueue,
  };

  return (
    <PlaybackContext.Provider value={value}>
      {children}
      <audio ref={audioRef} preload="metadata" />
    </PlaybackContext.Provider>
  );
}

/* ===================== HOOK ===================== */

export function usePlayback() {
  const ctx = useContext(PlaybackContext);
  if (!ctx) {
    throw new Error("usePlayback must be used inside PlaybackProvider");
  }
  return ctx;
}
