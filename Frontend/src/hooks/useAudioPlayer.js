import { useCallback, useEffect, useRef, useState } from "react";

export function useAudioPlayer() {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentUrl, setCurrentUrl] = useState(null);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentUrl(null);
  }, []);

  const play = useCallback(
    (url, { onEnded, onError } = {}) => {
      stop();
      const audio = new Audio(url);
      audioRef.current = audio;
      setCurrentUrl(url);

      audio.onplay = () => {
        setIsPlaying(true);
        setIsPaused(false);
      };
      audio.onpause = () => {
        if (audio.currentTime > 0 && audio.currentTime < audio.duration) {
          setIsPaused(true);
          setIsPlaying(false);
        }
      };
      audio.onended = () => {
        setIsPlaying(false);
        setIsPaused(false);
        setCurrentUrl(null);
        audioRef.current = null;
        onEnded?.();
      };
      audio.onerror = () => {
        setIsPlaying(false);
        setIsPaused(false);
        onError?.(new Error("Audio playback failed"));
      };

      return audio.play().catch((err) => {
        onError?.(err);
        throw err;
      });
    },
    [stop]
  );

  const pause = useCallback(() => {
    audioRef.current?.pause();
    setIsPlaying(false);
    setIsPaused(true);
  }, []);

  const resume = useCallback(() => {
    if (audioRef.current) {
      return audioRef.current.play().then(() => {
        setIsPlaying(true);
        setIsPaused(false);
      });
    }
    return Promise.resolve();
  }, []);

  const interrupt = useCallback(() => {
    stop();
  }, [stop]);

  return {
    play,
    pause,
    resume,
    stop,
    interrupt,
    isPlaying,
    isPaused,
    currentUrl,
    audioElement: audioRef.current,
  };
}
