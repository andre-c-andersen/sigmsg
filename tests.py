#!/usr/bin/env python3
"""Tests for signal messaging system."""

from utils import HDLCFrame


def test_hdlc_framing():
    """Test HDLC frame creation and parsing."""
    print("Testing HDLC framing...")
    
    test_cases = [
        b"Hello",
        b"",  # Empty payload
        bytes([0x7E, 0x7D, 0x42]),  # Contains flag and escape bytes
        b"A" * 100,  # Long message
    ]
    
    for i, payload in enumerate(test_cases):
        print(f"Test {i+1}: {payload!r}")
        
        # Create frame
        frame = HDLCFrame.create_frame(payload, seq_num=i)
        print(f"  Frame: {frame.hex()}")
        
        # Parse frame
        result = HDLCFrame.parse_frame(frame)
        if result:
            parsed_payload, seq_num = result
            if parsed_payload == payload and seq_num == i:
                print(f"  ✓ PASS")
            else:
                print(f"  ✗ FAIL: payload or seq mismatch")
        else:
            print(f"  ✗ FAIL: could not parse frame")
    
    print()


def test_bit_stuffing():
    """Test HDLC bit stuffing."""
    print("Testing bit stuffing...")
    
    test_cases = [
        bytes([0x7E]),  # Flag byte
        bytes([0x7D]),  # Escape byte  
        bytes([0x7E, 0x7D, 0x42, 0x7E]),  # Multiple special bytes
        bytes(range(256)),  # All possible bytes
    ]
    
    for i, data in enumerate(test_cases):
        print(f"Test {i+1}: {data.hex()}")
        
        # Stuff and unstuff
        stuffed = HDLCFrame.stuff_bytes(data)
        unstuffed = HDLCFrame.unstuff_bytes(stuffed)
        
        print(f"  Stuffed: {stuffed.hex()}")
        if unstuffed == data:
            print(f"  ✓ PASS")
        else:
            print(f"  ✗ FAIL: {unstuffed.hex()}")
    
    print()


def test_edge_case_bytes():
    """Test encoding specific byte patterns."""
    print("Testing edge case bytes...")
    
    test_bytes = [
        (0x00, "00000000"),  # All zeros
        (0xFF, "11111111"),  # All ones  
        (0xAA, "10101010"),  # Alternating 1010
        (0x55, "01010101"),  # Alternating 0101
        (0x80, "10000000"),  # Single 1 at MSB
        (0x01, "00000001"),  # Single 1 at LSB
        (0x7E, "01111110"),  # HDLC flag
        (0x7D, "01111101"),  # HDLC escape
    ]
    
    for byte_val, binary in test_bytes:
        frame = HDLCFrame.create_frame(bytes([byte_val]), 0)
        print(f"Byte 0x{byte_val:02x} ({binary}): frame = {frame.hex()}")
    
    print()


def main():
    print("Running signal messaging tests...\n")
    
    test_hdlc_framing()
    test_bit_stuffing() 
    test_edge_case_bytes()
    
    print("All tests completed!")


if __name__ == '__main__':
    main()