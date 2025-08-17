# Signal Messaging - Toy Example

Simple signal-based messaging using POSIX signals. Send messages between processes using SIGUSR1/USR2 with HDLC framing.

## Quick Start

**Terminal 1** (receiver):
```bash
python3 receiver.py
# Outputs: Receiver PID: 12345
```

**Terminal 2** (sender):
```bash
python3 sender.py 12345 "Hello World"
# Outputs: Sent
```

## Files

- `receiver.py` - Message receiver (shows PID, prints messages)
- `sender.py` - Message sender (takes PID and message)  
- `utils.py` - HDLC framing with CRC32
- `tests.py` - Basic tests

## How It Works

- Sends bytes as signal timing patterns (SIGUSR1 = bit 1, silence = bit 0)
- Uses HDLC framing with 0x7E flags and CRC32 checksums
- Stop-and-wait ARQ with SIGUSR2 ACK responses
- Sender embeds PID in first message for automatic coordination

## Testing

```bash
python3 tests.py
```

## Notes

- POSIX only (Linux/macOS) - Windows lacks SIGUSR1/USR2
- Slow by design (~100 bytes/sec) for educational purposes
