import React, { useRef, useState } from 'react'
import { X, Play, Pause, Volume2, VolumeX } from 'lucide-react'

interface WatchDemoModalProps {
  isOpen: boolean
  onClose: () => void
}

export const WatchDemoModal: React.FC<WatchDemoModalProps> = ({ isOpen, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)

  if (!isOpen) return null

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleMuteToggle = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const handleVideoPlay = () => setIsPlaying(true)
  const handleVideoPause = () => setIsPlaying(false)

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="w-full max-w-4xl bg-black rounded-xl overflow-hidden">
        {/* Video Container */}
        <div className="relative bg-black aspect-video">
          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            onPlay={handleVideoPlay}
            onPause={handleVideoPause}
          >
            {/* PLACEHOLDER: Video URL will be added here */}
            <source src="" type="video/mp4" />
            Your browser does not support the video tag.
          </video>

          {/* Placeholder Text (shown when no video source) */}
          <div className="absolute inset-0 flex items-center justify-center bg-black/50">
            <div className="text-center">
              <Play size={64} className="text-white mx-auto mb-4 opacity-50" />
              <p className="text-white text-lg font-medium">
                CLINOVA Demo Video
              </p>
              <p className="text-gray-300 text-sm mt-2">
                45–60 second overview (video to be added)
              </p>
            </div>
          </div>

          {/* Controls Overlay */}
          <div className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity flex flex-col justify-end bg-gradient-to-t from-black/80 to-transparent">
            {/* Progress Bar */}
            <input
              type="range"
              min="0"
              max="100"
              defaultValue="0"
              className="w-full h-1 bg-gray-700 cursor-pointer"
              onChange={(e) => {
                if (videoRef.current) {
                  videoRef.current.currentTime =
                    (parseFloat(e.target.value) / 100) * videoRef.current.duration
                }
              }}
            />

            {/* Control Buttons */}
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-2">
                {/* Play/Pause Button */}
                <button
                  onClick={handlePlayPause}
                  className="p-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
                  title={isPlaying ? 'Pause' : 'Play'}
                >
                  {isPlaying ? (
                    <Pause size={20} />
                  ) : (
                    <Play size={20} />
                  )}
                </button>

                {/* Mute Button */}
                <button
                  onClick={handleMuteToggle}
                  className="p-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
                  title={isMuted ? 'Unmute' : 'Mute'}
                >
                  {isMuted ? (
                    <VolumeX size={20} />
                  ) : (
                    <Volume2 size={20} />
                  )}
                </button>
              </div>

              {/* Fullscreen and Close */}
              <div className="flex items-center gap-2">
                <span className="text-white text-sm">
                  {videoRef.current
                    ? `${Math.floor(videoRef.current.currentTime)}s / ${Math.floor(
                        videoRef.current.duration
                      )}s`
                    : '0s / 0s'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Top Close Button */}
        <div className="absolute top-4 right-4 z-50">
          <button
            onClick={onClose}
            className="p-2 bg-white/20 hover:bg-white/40 text-white rounded-lg transition-colors"
            title="Close"
          >
            <X size={24} />
          </button>
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-4 text-center text-white text-sm">
        <p>
          To add your demo video: Replace the empty <code className="bg-gray-800 px-2 py-1 rounded">src=""</code> in WatchDemoModal.tsx with your video URL
        </p>
      </div>
    </div>
  )
}

export default WatchDemoModal
