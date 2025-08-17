#!/usr/bin/env python3
"""Signal-based message receiver using HDLC framing and timing analysis."""

import os
import signal
import time
from abc import ABC, abstractmethod
from utils import HDLCFrame


class SignalReceiver(ABC):
    """Receives messages from signal timing patterns."""
    
    def __init__(self, sleep_time: float = 0.05, sender_pid: int = None):
        self.sleep_time = sleep_time
        self.sender_pid = sender_pid
        self.last_seq_num = None
        self.frame_buffer = bytearray()
        self.in_frame = False
        self.pid_extracted = False
        
        # Signal timing state
        self.signal_times = []
        self.current_timer = None
        
        # Set up signal handler
        signal.signal(signal.SIGUSR1, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """Handle incoming signal."""
        current_time = time.time()
        self.signal_times.append(current_time)
        
        # Process when we detect stop signal timing (9+ intervals from start)
        if len(self.signal_times) >= 2:
            elapsed = current_time - self.signal_times[0]
            intervals_since_start = elapsed / self.sleep_time
            
            # If we've reached the stop position (≥8.5 intervals), process the byte
            if intervals_since_start >= 8.5:
                self._process_signal_burst()
                self.signal_times = []
    
    def _process_signal_burst(self):
        """Decode a burst of signals as a byte using timing analysis."""
        if len(self.signal_times) < 2:  # Need at least start + stop
            return
        
        # Decode byte using timing intervals from start signal
        start_time = self.signal_times[0]
        byte_val = 0
        
        # Check each signal timing to determine which bit position it represents
        for i, signal_time in enumerate(self.signal_times[1:], 1):  # Skip start signal
            elapsed = signal_time - start_time
            intervals = elapsed / self.sleep_time
            
            # Use threshold to distinguish data bits from stop
            if 1 <= intervals < 8.5:
                bit_pos = round(intervals) - 1  # Convert to 0-7 range
                if 0 <= bit_pos <= 7:
                    byte_val |= (1 << (7 - bit_pos))  # MSB first
        
        # Reset signal times for next byte
        self.signal_times = []
        
        self._process_byte(byte_val)
    
    def _process_byte(self, byte: int):
        """Process a received byte."""        
        if byte == HDLCFrame.FLAG:
            if self.in_frame and len(self.frame_buffer) > 0:
                self._process_frame()
            self.frame_buffer.clear()
            self.in_frame = True
        elif self.in_frame:
            self.frame_buffer.append(byte)
    
    def _process_frame(self):
        """Process a complete frame."""
        frame = bytes([HDLCFrame.FLAG]) + self.frame_buffer + bytes([HDLCFrame.FLAG])
        
        result = HDLCFrame.parse_frame(frame)
        
        if result:
            payload, seq_num = result
            
            # Extract sender PID from first message (seq_num 0)
            if seq_num == 0 and not self.pid_extracted and len(payload) >= 4:
                sender_pid = int.from_bytes(payload[:4], 'big')
                actual_message = payload[4:]
                self.sender_pid = sender_pid
                self.pid_extracted = True
                payload = actual_message
            
            if self.last_seq_num is None or seq_num != self.last_seq_num:
                self.last_seq_num = seq_num
                self.handle_message(payload, seq_num)
            self._send_ack()
    
    def _send_ack(self):
        """Send ACK signal back to sender."""
        if self.sender_pid:
            try:
                os.kill(self.sender_pid, signal.SIGUSR2)
            except ProcessLookupError:
                pass
    
    @abstractmethod
    def handle_message(self, message: bytes, seq_num: int):
        """Handle received message - override in subclasses."""
        pass


class EchoReceiver(SignalReceiver):
    """Receiver that prints messages."""
    
    def handle_message(self, message: bytes, seq_num: int):
        """Print received message."""
        try:
            text = message.decode('utf-8')
            print(f"RECEIVED: {text}")
        except UnicodeDecodeError:
            print(f"RECEIVED: {message.hex()}")
    
    def run(self):
        """Main receiver loop."""
        print(f"Receiver PID: {os.getpid()}")
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopped.")


def main():
    receiver = EchoReceiver()
    receiver.run()


if __name__ == '__main__':
    main()