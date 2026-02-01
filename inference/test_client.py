#!/usr/bin/env python3
"""
Test Client for Inference API
Loads a local image and sends it to the /infer endpoint
"""

import requests
import json
from pathlib import Path


def test_inference(image_path: str, server_url: str = "http://localhost:8000"):
    """
    Test the inference endpoint with a local image
    
    Args:
        image_path: Path to a local JPEG/PNG image
        server_url: URL of the inference server (default: local)
    """
    # Check if image exists
    if not Path(image_path).exists():
        print(f"❌ Error: Image not found at {image_path}")
        return
    
    print(f"📤 Sending image: {image_path}")
    print(f"🌐 Server: {server_url}/infer")
    
    try:
        # Open and send the image file
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f, "image/jpeg")}
            response = requests.post(f"{server_url}/infer", files=files)
        
        # Check response status
        if response.status_code == 200:
            print("✅ Inference successful!\n")
            
            # Parse and display results
            results = response.json()
            print("📊 Results:")
            print(json.dumps(results, indent=2))
            
            # Summary
            if "detections" in results:
                print(f"\n🎯 Detected {len(results['detections'])} objects:")
                for i, det in enumerate(results['detections'], 1):
                    print(f"  {i}. {det['label']} "
                          f"(confidence: {det['confidence']:.2%}) "
                          f"at {det['bbox']}")
        else:
            print(f"❌ Error: Server returned status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to {server_url}")
        print("   Make sure the server is running: python server.py")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    # Usage instructions
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <image_path> [server_url]")
        print("\nExamples:")
        print("  python test_client.py test_image.jpg")
        print("  python test_client.py test_image.jpg http://your-vm-ip:8000")
        print("\nTo test, you'll need an image file.")
        print("You can download one with:")
        print("  curl -o test_image.jpg https://via.placeholder.com/640")
        sys.exit(1)
    
    image_path = sys.argv[1]
    server_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    test_inference(image_path, server_url)
