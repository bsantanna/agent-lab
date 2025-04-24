import {AfterViewInit, Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'console-audio-recorder',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './audio-recorder.component.html'
})
export class AudioRecorderComponent implements OnDestroy, AfterViewInit{
  isRecording = false;
  isPaused = false;
  isMicrophoneAvailable = false;
  permissionState: 'prompt' | 'granted' | 'denied' = 'prompt';
  recordedAudio: string | null = null;
  recordingTime = 0;
  maxRecordingTime = 300; // 5 minutes in seconds
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private timerInterval: any;

  ngAfterViewInit(): void {
    this.checkMicrophoneAccess();
  }

  ngOnDestroy() {
    this.clearTimer();
    this.stopMediaTracks();
  }

  async checkMicrophoneAccess() {
    if (!navigator.permissions || !navigator.permissions.query) {
      // Fallback for browsers that don't support permissions API
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.isMicrophoneAvailable = true;
        this.permissionState = 'granted';
        stream.getTracks().forEach(track => track.stop());
      } catch {
        this.isMicrophoneAvailable = false;
        this.permissionState = 'denied';
      }
      return;
    }

    try {
      const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
      this.permissionState = permission.state;
      this.isMicrophoneAvailable = permission.state === 'granted';

      // Listen for permission changes
      permission.onchange = () => {
        this.permissionState = permission.state;
        this.isMicrophoneAvailable = permission.state === 'granted';
      };
    } catch (error) {
      console.error('Error checking microphone permission:', error);
      this.isMicrophoneAvailable = false;
      this.permissionState = 'denied';
    }
  }

  async requestMicrophonePermission() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.isMicrophoneAvailable = true;
      this.permissionState = 'granted';
      stream.getTracks().forEach(track => track.stop());
    } catch (error) {
      console.error('Microphone permission denied:', error);
      this.isMicrophoneAvailable = false;
      this.permissionState = 'denied';
    }
  }

  async toggleRecording() {
    if (this.isRecording) {
      this.stopRecording();
    } else {
      if (this.permissionState !== 'granted') {
        await this.requestMicrophonePermission();
        if (this.permissionState === 'prompt' || this.permissionState === 'denied') {
          return; // Don't proceed if permission is not granted
        }
      }
      await this.startRecording();
    }
  }

  async startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream);
      this.audioChunks = [];
      this.recordingTime = 0;

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        this.recordedAudio = URL.createObjectURL(audioBlob);
        this.stopMediaTracks();
        this.clearTimer();
      };

      this.mediaRecorder.start();
      this.isRecording = true;
      this.startTimer();
    } catch (error) {
      console.error('Error starting recording:', error);
      this.isMicrophoneAvailable = false;
      this.permissionState = 'denied';
    }
  }

  stopRecording() {
    if (this.mediaRecorder) {
      this.mediaRecorder.stop();
      this.isRecording = false;
      this.isPaused = false;
    }
  }

  // downloadRecording() {
  //   if (this.recordedAudio) {
  //     const link = document.createElement('a');
  //     link.href = this.recordedAudio;
  //     link.download = `recording-${new Date().toISOString()}.webm`;
  //     link.click();
  //   }
  // }

  private startTimer() {
    this.clearTimer();
    this.timerInterval = setInterval(() => {
      this.recordingTime++;
      if (this.recordingTime >= this.maxRecordingTime) {
        this.stopRecording();
      }
    }, 1000);
  }

  private clearTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  private stopMediaTracks() {
    if (this.mediaRecorder?.stream) {
      this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
  }

  formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
}
