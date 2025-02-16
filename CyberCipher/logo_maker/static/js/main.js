// static/js/main.js
document.getElementById('generateBtn').addEventListener('click', async () => {
  const resultsDiv = document.querySelector('.results');
  const loader = document.getElementById('loader');
  const logoImg = document.getElementById('generatedLogo');
  const videoElement = document.getElementById('generatedVideo');
  const generateBtn = document.getElementById('generateBtn');
  
  // Show loader and disable button
  resultsDiv.style.display = 'block';
  loader.style.display = 'block';
  generateBtn.disabled = true;
  generateBtn.style.opacity = '0.7';
  generateBtn.textContent = 'Generating...';
  
  try {
      const response = await fetch('/generate', {
          method: 'POST'
      });
      
      if (!response.ok) {
          throw new Error('Generation failed');
      }
      
      const data = await response.json();
      
      if (data.success) {
          // Update media elements with new sources
          // Add timestamp to prevent caching
          logoImg.src = data.logo_url + '?t=' + new Date().getTime();
          videoElement.src = data.video_url + '?t=' + new Date().getTime();
          
          // Show media container
          document.querySelector('.media-container').style.display = 'flex';
      } else {
          throw new Error(data.error || 'Generation failed');
      }
  } catch (error) {
      console.error('Error:', error);
      alert('Failed to generate media: ' + error.message);
  } finally {
      // Hide loader and re-enable button
      loader.style.display = 'none';
      generateBtn.disabled = false;
      generateBtn.style.opacity = '1';
      generateBtn.textContent = 'Generate Logo & Video';
  }
});