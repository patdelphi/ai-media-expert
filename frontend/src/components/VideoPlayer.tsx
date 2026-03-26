/**
 * 简洁视频播放器弹窗组件
 * 
 * 功能特性：
 * - 简洁美观的弹窗播放
 * - 默认静音
 * - 基本播放控制
 * - 进度条和音量控制
 * - 播放速度调节
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';

interface VideoPlayerProps {
  isOpen: boolean;
  onClose: () => void;
  videoUrl: string;
  videoTitle: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ isOpen, onClose, videoUrl, videoTitle }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(true); // 默认静音
  const [volume, setVolume] = useState(0.5);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  // const [showControls, setShowControls] = useState(true);
  const [isLooping, setIsLooping] = useState(false); // 循环播放状态

  // 播放速度选项
  const playbackRates = [0.5, 0.75, 1, 1.25, 1.5, 2];

  // 播放/暂停
  const togglePlay = useCallback(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  }, [isPlaying]);

  useEffect(() => {
    if (isOpen && videoRef.current) {
      videoRef.current.muted = isMuted;
      videoRef.current.volume = volume;
      videoRef.current.loop = isLooping;
      
      // 自动开始播放
      videoRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch((error) => {
        console.log('自动播放失败:', error);
      });
    }
  }, [isOpen, isMuted, volume, isLooping]);
  
  // 单独处理播放速度设置
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = playbackRate;
      console.log('useEffect设置播放速度为:', playbackRate, '实际速度:', videoRef.current.playbackRate);
    }
  }, [playbackRate]);
  
  // 监听视频加载事件，确保播放速度在视频重新加载后保持
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    
    const handleLoadStart = () => {
      console.log('视频开始加载，当前播放速度状态:', playbackRate);
    };
    
    const handleCanPlay = () => {
      video.playbackRate = playbackRate;
      console.log('视频可以播放，重新设置播放速度为:', playbackRate, '实际速度:', video.playbackRate);
    };
    
    video.addEventListener('loadstart', handleLoadStart);
    video.addEventListener('canplay', handleCanPlay);
    
    return () => {
      video.removeEventListener('loadstart', handleLoadStart);
      video.removeEventListener('canplay', handleCanPlay);
    };
  }, [playbackRate]);

  // 键盘事件监听
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (isOpen) {
        if (event.code === 'Space') {
          event.preventDefault();
          togglePlay();
        } else if (event.code === 'Escape') {
          event.preventDefault();
          onClose();
        }
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyPress);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [isOpen, togglePlay, onClose]);

  // 静音切换
  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  // 音量调节
  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      if (newVolume > 0 && isMuted) {
        setIsMuted(false);
        videoRef.current.muted = false;
      }
    }
  };

  // 进度条调节
  const handleProgressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value);
    setCurrentTime(newTime);
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
    }
  };

  // 播放速度调节
  const handlePlaybackRateChange = (rate: number) => {
    console.log('设置播放速度为:', rate);
    setPlaybackRate(rate);
    // 注意：实际的播放速度设置由useEffect处理
  };
  


  // 时间格式化
  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // 视频事件处理
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
      // 确保播放速度正确设置
      videoRef.current.playbackRate = playbackRate;
      console.log('视频加载完成，播放速度设置为:', playbackRate, '实际速度:', videoRef.current.playbackRate);
    }
  };

  const handlePlay = () => setIsPlaying(true);
  const handlePause = () => setIsPlaying(false);
  const handleEnded = () => {
    setIsPlaying(false);
    if (isLooping && videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play();
      setIsPlaying(true);
    }
  };
  
  // 循环播放切换
  const toggleLoop = () => {
    setIsLooping(!isLooping);
    if (videoRef.current) {
      videoRef.current.loop = !isLooping;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50" onClick={onClose}>
      <div className="relative bg-black rounded-lg shadow-2xl max-w-7xl w-full mx-4 max-h-[95vh]" onClick={(e) => e.stopPropagation()}>
        {/* 关闭按钮 */}
        <button
          onClick={onClose}
          className="absolute top-2 right-2 z-10 text-white hover:text-gray-200 text-2xl bg-black bg-opacity-50 rounded-full w-8 h-8 flex items-center justify-center"
        >
          <i className="fas fa-times"></i>
        </button>

        {/* 视频播放区域 */}
        <div className="relative">
          <video
            ref={videoRef}
            src={videoUrl}
            className="w-full h-auto max-h-[80vh] rounded-t-lg"
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onPlay={handlePlay}
            onPause={handlePause}
            onEnded={handleEnded}
            onClick={togglePlay}
            controls={false}
          />
          
          {/* 播放按钮覆盖层 */}
          {!isPlaying && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 rounded-t-lg">
              <button
                onClick={togglePlay}
                className="text-white text-6xl hover:text-gray-200 transition-colors"
              >
                <i className="fas fa-play"></i>
              </button>
            </div>
          )}
        </div>

        {/* 简洁控制栏 */}
        <div className="bg-gray-50 text-gray-900 p-3 rounded-b-lg">
          {/* 进度条 */}
          <div className="mb-3">
            <input
              type="range"
              min="0"
              max={duration || 0}
              value={currentTime}
              onChange={handleProgressChange}
              className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-700 mt-1">
              <span>{formatTime(currentTime)}</span>
              <span className="text-center flex-1 truncate px-2">{videoTitle}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* 控制按钮 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {/* 播放/暂停 */}
              <button
                onClick={togglePlay}
                className="text-xl text-gray-900 hover:text-gray-700"
              >
                <i className={`fas ${isPlaying ? 'fa-pause' : 'fa-play'}`}></i>
              </button>

              {/* 音量控制 */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleMute}
                  className="text-gray-900 hover:text-gray-700"
                >
                  <i className={`fas ${isMuted ? 'fa-volume-mute' : 'fa-volume-up'}`}></i>
                </button>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={isMuted ? 0 : volume}
                  onChange={handleVolumeChange}
                  className="w-16 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              
              {/* 循环播放切换 */}
              <button
                onClick={toggleLoop}
                className={`text-gray-900 hover:text-gray-700 ${isLooping ? 'text-blue-600' : ''}`}
                title={isLooping ? '关闭循环播放' : '开启循环播放'}
              >
                <i className="fas fa-redo"></i>
              </button>
            </div>

            {/* 播放速度 */}
            <div className="flex items-center space-x-1">
              {playbackRates.map((rate) => (
                <button
                  key={rate}
                  onClick={() => handlePlaybackRateChange(rate)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    playbackRate === rate
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                  }`}
                >
                  {rate}x
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;
