import requests
from flask import Flask, request, jsonify, render_template, Blueprint
from PIL import Image
import base64
from io import BytesIO
import os
from typing import Tuple, Optional

app = Flask(__name__)

# Ensure static image directory exists
os.makedirs("static/images", exist_ok=True)

def generate_image(
    prompt: str,
    api_key: str = "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",
    cfg_scale: float = 5,
    steps: int = 25,
    seed: int = 0,
    save_path: Optional[str] = None
) -> Tuple[Image.Image, str]:
    """
    Generate an image using NVIDIA's Stability AI API.
    
    Args:
        prompt (str): The text prompt describing the image to generate.
        api_key (str): NVIDIA API key.
        cfg_scale (float): Configuration scale for image generation.
        steps (int): Number of steps for image generation.
        seed (int): Random seed for reproducibility.
        save_path (str, optional): Path to save the generated image. If None, image won't be saved.

    Returns:
        Tuple[Image.Image, str]: Tuple containing the PIL Image object and the base64 string of the image.
    
    Raises:
        Exception: If API request fails or response is invalid.
    """
    try:
        # API endpoint
        url = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-xl"
        
        # Headers for the request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        
        # Payload for the request
        payload = {
            "text_prompts": [{"text": prompt + " This logo is to be generated for startups, so make sure the logo synmbolizes their goals and ideals. Make sure it is catchy, if there any text or any symbolization make it bold and center.", "weight": 1}],
            "cfg_scale": cfg_scale,
            "sampler": "K_DPM_2_ANCESTRAL",
            "seed": seed,
            "steps": steps
        }
        
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Extract and decode the base64 image
        if "artifacts" not in data or not data["artifacts"]:
            raise ValueError("No image data in response")
            
        base64_image = data["artifacts"][0]["base64"]
        image_bytes = base64.b64decode(base64_image)
        image = Image.open(BytesIO(image_bytes))
        
        # Save the image if a path is provided
        if save_path:
            image.save(save_path, "PNG")
            print(f"✅ Image saved successfully to {save_path}")
        
        return image, base64_image
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except ValueError as e:
        raise Exception(f"Invalid response format: {str(e)}")
    except IOError as e:
        raise Exception(f"Failed to save image: {str(e)}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        prompt = request.json.get('prompt', 'generate a logo for a robot startup that makes robot pets')
        
        # Generate the image and save it
        save_path = "static/images/generated_image.png"
        generate_image(prompt=prompt, save_path=save_path)

        return jsonify({
            'success': True,
            'image_url': f'/{save_path}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)