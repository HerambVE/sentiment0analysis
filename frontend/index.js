const apiUrl = ''; // REPLACE WITH YOUR API GATEWAY URL
const analyzeButton = document.getElementById('analyze-button');
const feedbackTextarea = document.getElementById('feedback');
const loadingIndicator = document.getElementById('loading-indicator');
const resultContainer = document.getElementById('result-container');
const overallSentimentSpan = document.getElementById('overall-sentiment');
const confidenceScoresList = document.getElementById('confidence-scores');
const analyzedTextSpan = document.getElementById('analyzed-text');

analyzeButton.addEventListener('click', async () => {
  const text = feedbackTextarea.value.trim();
  if (!text) {
    alert('Please enter some text to analyze.');
    return;
  }

  loadingIndicator.style.display = 'block';
  resultContainer.style.display = 'none';

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'An error occurred during analysis.');
    }

    const data = await response.json();
    console.log('API Response:', data);

    analyzedTextSpan.textContent = data.text;
    overallSentimentSpan.textContent = data.sentiment;
    overallSentimentSpan.className = 'sentiment-' + data.sentiment.toLowerCase();

    confidenceScoresList.innerHTML = '';
    for (const [key, value] of Object.entries(data.confidence_scores)) {
      const listItem = document.createElement('li');
      listItem.innerHTML = `<strong>${key}:</strong> ${(value * 100).toFixed(2)}%`;
      confidenceScoresList.appendChild(listItem);
    }

    resultContainer.style.display = 'block';

  } catch (error) {
    console.error('Fetch Error:', error);
    alert(`Failed to analyze sentiment: ${error.message}`);
  } finally {
    loadingIndicator.style.display = 'none';
  }
});
