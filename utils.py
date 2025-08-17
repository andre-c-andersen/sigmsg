"""Utilities for signal-based messaging with HDLC framing."""

import zlib
from typing import Optional


class HDLCFrame:
    """HDLC frame with 0x7E flag and bit stuffing."""
    
    FLAG = 0x7E
    ESCAPE = 0x7D
    ESCAPE_XOR = 0x20
    
    @classmethod
    def stuff_bytes(cls, data: bytes) -> bytes:
        """Apply byte stuffing to escape flag and escape bytes."""
        result = bytearray()
        for byte in data:
            if byte == cls.FLAG or byte == cls.ESCAPE:
                result.append(cls.ESCAPE)
                result.append(byte ^ cls.ESCAPE_XOR)
            else:
                result.append(byte)
        return bytes(result)
    
    @classmethod
    def unstuff_bytes(cls, data: bytes) -> bytes:
        """Remove byte stuffing."""
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i] == cls.ESCAPE and i + 1 < len(data):
                result.append(data[i + 1] ^ cls.ESCAPE_XOR)
                i += 2
            else:
                result.append(data[i])
                i += 1
        return bytes(result)
    
    @classmethod
    def create_frame(cls, payload: bytes, seq_num: int = 0) -> bytes:
        """Create HDLC frame with CRC32."""
        header = seq_num.to_bytes(1, 'big')
        crc = zlib.crc32(header + payload) & 0xffffffff
        frame_data = header + payload + crc.to_bytes(4, 'big')
        stuffed = cls.stuff_bytes(frame_data)
        return bytes([cls.FLAG]) + stuffed + bytes([cls.FLAG])
    
    @classmethod
    def parse_frame(cls, frame: bytes) -> Optional[tuple[bytes, int]]:
        """Parse HDLC frame and return (payload, seq_num) if valid."""
        if len(frame) < 2 or frame[0] != cls.FLAG or frame[-1] != cls.FLAG:
            return None
        
        try:
            unstuffed = cls.unstuff_bytes(frame[1:-1])
            if len(unstuffed) < 5:  # seq(1) + payload(min 0) + crc(4)
                return None
            
            seq_num = unstuffed[0]
            payload = unstuffed[1:-4]
            received_crc = int.from_bytes(unstuffed[-4:], 'big')
            calculated_crc = zlib.crc32(unstuffed[:-4]) & 0xffffffff
            
            if received_crc == calculated_crc:
                return payload, seq_num
            return None
        except Exception:
            return None