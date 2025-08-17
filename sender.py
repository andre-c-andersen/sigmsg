#!/usr/bin/env python3
"""Signal-based message sender using HDLC framing and stop-and-wait ARQ."""

import os
import signal
import time
import argparse
from utils import HDLCFrame


class SignalSender:
    """Sends messages using POSIX signals with timing-based bit encoding."""
    
    def __init__(self, target_pid: int, sleep_time: float = 0.05, 
                 timeout: float = 1.0, max_retries: int = 5):
        self.target_pid = target_pid
        self.sleep_time = sleep_time
        self.timeout = timeout
        self.max_retries = max_retries
        self.seq_num = 0
        self.ack_received = False
        
        # Set up signal handler for ACK
        signal.signal(signal.SIGUSR2, self._handle_ack)
    
    def _handle_ack(self, signum, frame):
        """Handle ACK signal."""
        self.ack_received = True
    
    def _send_byte(self, byte: int):
        """Send a byte using signal timing pattern."""
        # Send start signal
        os.kill(self.target_pid, signal.SIGUSR1)
        time.sleep(self.sleep_time)
        
        # Send 8 bits, MSB first (signal for 1, silence for 0)
        for i in range(7, -1, -1):
            bit = (byte >> i) & 1
            if bit:
                os.kill(self.target_pid, signal.SIGUSR1)
            time.sleep(self.sleep_time)
        
        # Send stop signal
        os.kill(self.target_pid, signal.SIGUSR1)
        time.sleep(self.sleep_time * 2)  # Longer pause between bytes
    
    def _send_frame(self, frame: bytes):
        """Send frame byte by byte."""
        for byte in frame:
            self._send_byte(byte)
    
    def _wait_for_ack(self) -> bool:
        """Wait for ACK with timeout."""
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.ack_received:
                self.ack_received = False
                return True
            time.sleep(0.01)
        return False
    
    def send_message(self, message: bytes) -> bool:
        """Send message with stop-and-wait ARQ."""
        # For first message (seq_num 0), prepend our PID
        if self.seq_num == 0:
            pid_bytes = os.getpid().to_bytes(4, 'big')
            message = pid_bytes + message
        
        frame = HDLCFrame.create_frame(message, self.seq_num)
        
        for attempt in range(self.max_retries):
            self._send_frame(frame)
            if self._wait_for_ack():
                self.seq_num = (self.seq_num + 1) % 256
                return True
        
        return False


class TextSender(SignalSender):
    """Interactive text sender."""
    
    def run(self):
        """Read lines from stdin and send them."""
        print(f"Sending to PID {self.target_pid}")
        
        try:
            while True:
                try:
                    line = input("> ").strip()
                    if line:
                        success = self.send_message(line.encode('utf-8'))
                        if success:
                            print("Sent")
                        else:
                            print("Failed")
                except EOFError:
                    break
        except KeyboardInterrupt:
            pass


class OneShotSender(SignalSender):
    """Sends one message and exits."""
    
    def __init__(self, target_pid: int, message: str, **kwargs):
        super().__init__(target_pid, **kwargs)
        self.message = message
    
    def run(self):
        """Send one message and exit."""
        success = self.send_message(self.message.encode('utf-8'))
        if success:
            print("Sent")
            return 0
        else:
            print("Failed")
            return 1


def main():
    parser = argparse.ArgumentParser(description='Signal-based message sender')
    parser.add_argument('pid', type=int, help='Target receiver PID')
    parser.add_argument('message', nargs='?', default=None, help='Message to send (optional)')
    
    args = parser.parse_args()
    
    if args.message:
        sender = OneShotSender(target_pid=args.pid, message=args.message)
        exit(sender.run())
    else:
        sender = TextSender(target_pid=args.pid)
        sender.run()


if __name__ == '__main__':
    main()