/**
 * Carbon Coach Frontend Controller
 * Connects the modern emerald dashboard to Google ADK's FastAPI backend.
 */

// Configuration & State
const CONFIG = {
  appName: 'carbon_coach',
  userId: 'demo_user',
  dailyBenchmarkKg: 5.0,
};

let currentSessionId = null;
let sessionActivities = [];

// DOM Elements
const messagesStream = document.getElementById('messagesStream');
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const btnSend = document.getElementById('btnSend');
const todayTotalVal = document.getElementById('todayTotalVal');
const carbonGaugeCircle = document.getElementById('carbonGaugeCircle');
const gaugeStatusBadge = document.getElementById('gaugeStatusBadge');
const gaugeStatusText = document.getElementById('gaugeStatusText');
const gaugeHeadline = document.getElementById('gaugeHeadline');
const gaugeDesc = document.getElementById('gaugeDesc');
const benchmarkBarFill = document.getElementById('benchmarkBarFill');
const catTravelVal = document.getElementById('catTravelVal');
const catElecVal = document.getElementById('catElecVal');
const catFoodVal = document.getElementById('catFoodVal');
const catWasteVal = document.getElementById('catWasteVal');
const activityFeed = document.getElementById('activityFeed');
const emptyActivityState = document.getElementById('emptyActivityState');
const activityCountText = document.getElementById('activityCountText');
const btnLeaderboard = document.getElementById('btnLeaderboard');
const leaderboardModal = document.getElementById('leaderboardModal');
const btnCloseModal = document.getElementById('btnCloseModal');
const btnResetSession = document.getElementById('btnResetSession');

// Voice & Multilingual Elements
const btnMic = document.getElementById('btnMic');
const speechLangSelect = document.getElementById('speechLangSelect');
const voiceStatusBanner = document.getElementById('voiceStatusBanner');
const voiceStatusText = document.getElementById('voiceStatusText');
const btnVoiceCancel = document.getElementById('btnVoiceCancel');
const btnAudioToggle = document.getElementById('btnAudioToggle');
const audioToggleState = document.getElementById('audioToggleState');
const quickChipsBar = document.getElementById('quickChipsBar');
const chatTitleText = document.getElementById('chatTitleText');
const audioToggleLabel = document.getElementById('audioToggleLabel');
const welcomeMsgBubble = document.getElementById('welcomeMsgBubble');

// Dark / Light Theme Toggle Elements
const btnThemeToggle = document.getElementById('btnThemeToggle');
const themeToggleIcon = document.getElementById('themeToggleIcon');
const themeToggleText = document.getElementById('themeToggleText');

let isRecording = false;
let recognition = null;
let audioVoiceEnabled = true;

// ============================================================================
// 1. SESSION MANAGEMENT
// ============================================================================
async function initSession() {
  try {
    const res = await fetch(`/api/session?user_id=${CONFIG.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json();
    currentSessionId = data.id || data.sessionId;
    console.log('[Carbon Coach] Active ADK Session:', currentSessionId);
    await refreshSessionState();
  } catch (err) {
    console.error('[Carbon Coach] Error creating session:', err);
    appendAgentMessage(
      '⚠️ Notice: Could not connect to ADK server. Please ensure the backend is running on port 8000.'
    );
  }
}

async function refreshSessionState() {
  if (!currentSessionId) return;
  try {
    const res = await fetch(`/api/session-state?session_id=${currentSessionId}&user_id=${CONFIG.userId}`);
    const data = await res.json();
    sessionActivities = data?.state?.activities || [];
    updateDashboardUI(sessionActivities);
  } catch (err) {
    console.warn('[Carbon Coach] Could not fetch session state:', err);
  }
}

// ============================================================================
// 2. DASHBOARD UI UPDATES
// ============================================================================
function updateDashboardUI(activities) {
  const todayIso = new Date().toISOString().split('T')[0];

  // Category totals
  const totals = { travel: 0.0, electricity: 0.0, food: 0.0, waste: 0.0 };
  let todayTotal = 0.0;

  activities.forEach(act => {
    const kg = Number(act.kg_co2e) || 0;
    const cat = (act.category || 'other').toLowerCase();
    if (totals.hasOwnProperty(cat)) {
      totals[cat] += kg;
    }
    // Sum for today
    if (act.date === todayIso || !act.date) {
      todayTotal += kg;
    }
  });

  // Update Category Metric Cards
  catTravelVal.textContent = totals.travel.toFixed(3);
  catElecVal.textContent = totals.electricity.toFixed(3);
  catFoodVal.textContent = totals.food.toFixed(3);
  catWasteVal.textContent = totals.waste.toFixed(3);

  // Update Circular Carbon Gauge (radius 88px)
  todayTotalVal.textContent = todayTotal.toFixed(2);
  const benchmark = CONFIG.dailyBenchmarkKg;
  const ratio = Math.min(todayTotal / benchmark, 1.0);
  const circumference = 2 * Math.PI * 88; // ~552.92
  const offset = circumference * (1 - ratio);
  carbonGaugeCircle.style.strokeDashoffset = offset;

  // Progress Bar
  const barPercent = Math.min((todayTotal / (benchmark * 2)) * 100, 100);
  benchmarkBarFill.style.width = `${barPercent}%`;

  // Real-world Nature Equivalents Elements
  const treesAbsorbVal = document.getElementById('treesAbsorbVal');
  const phonesChargedVal = document.getElementById('phonesChargedVal');
  const cleanAirScore = document.getElementById('cleanAirScore');
  const natureLeadText = document.getElementById('natureLeadText');
  const naturePill = document.getElementById('naturePill');

  const treesNeeded = (todayTotal / 1.83).toFixed(1); // 1 mature tree absorbs ~1.83 kg/month
  const phonesCharged = Math.round(todayTotal / 0.008); // 1 smartphone charge is ~8g CO2e

  if (treesAbsorbVal) treesAbsorbVal.textContent = `${treesNeeded} tree-months`;
  if (phonesChargedVal) phonesChargedVal.textContent = `${phonesCharged.toLocaleString()} charges`;

  // Status Badge & Color thresholds
  if (todayTotal === 0) {
    carbonGaugeCircle.style.stroke = 'var(--emerald-primary)';
    gaugeStatusBadge.style.background = 'rgba(16, 185, 129, 0.15)';
    gaugeStatusBadge.style.color = 'var(--mint-accent)';
    gaugeStatusText.textContent = 'Zero Emissions';
    gaugeHeadline.textContent = 'Clean and sustainable day!';
    gaugeDesc.textContent = `Log your daily travel, AC, food, or waste to measure against the 5.0 kg benchmark.`;
    if (cleanAirScore) cleanAirScore.textContent = 'Pristine 🌿';
    if (naturePill) naturePill.textContent = 'Zero Impact Today';
  } else if (todayTotal <= benchmark * 0.7) {
    carbonGaugeCircle.style.stroke = 'var(--emerald-primary)';
    gaugeStatusBadge.style.background = 'rgba(16, 185, 129, 0.15)';
    gaugeStatusBadge.style.color = 'var(--mint-accent)';
    gaugeStatusText.textContent = 'Eco-Friendly & Safe';
    const diff = (benchmark - todayTotal).toFixed(2);
    gaugeHeadline.textContent = `Great! ${diff} kg CO₂e below benchmark`;
    gaugeDesc.textContent = `Your footprint is ${((todayTotal / benchmark) * 100).toFixed(0)}% of the daily average benchmark.`;
    if (cleanAirScore) cleanAirScore.textContent = 'Fresh & Healthy 🍃';
    if (naturePill) naturePill.textContent = 'Within Safe Planetary Limits';
  } else if (todayTotal <= benchmark) {
    carbonGaugeCircle.style.stroke = 'var(--color-warning)';
    gaugeStatusBadge.style.background = 'rgba(245, 158, 11, 0.15)';
    gaugeStatusBadge.style.color = '#fbbf24';
    gaugeStatusText.textContent = 'Approaching Daily Limit';
    const diff = (benchmark - todayTotal).toFixed(2);
    gaugeHeadline.textContent = `${diff} kg remaining before benchmark`;
    gaugeDesc.textContent = `You are at ${((todayTotal / benchmark) * 100).toFixed(0)}% of the 5.0 kg Indian daily benchmark.`;
    if (cleanAirScore) cleanAirScore.textContent = 'Moderate Smog Impact ⚠️';
    if (naturePill) naturePill.textContent = 'Approaching National Average';
  } else {
    carbonGaugeCircle.style.stroke = 'var(--color-danger)';
    gaugeStatusBadge.style.background = 'rgba(239, 68, 68, 0.15)';
    gaugeStatusBadge.style.color = '#f87171';
    gaugeStatusText.textContent = 'Above Daily Benchmark';
    const excess = (todayTotal - benchmark).toFixed(2);
    gaugeHeadline.textContent = `Exceeded benchmark by ${excess} kg`;
    gaugeDesc.textContent = `High emissions today. Check personalized tips below to reduce travel or cooling impacts!`;
    if (cleanAirScore) cleanAirScore.textContent = 'High Air Pollution 💨';
    if (naturePill) naturePill.textContent = 'Planetary Stress Warning';
  }

  // Update Activity Feed
  activityCountText.textContent = `${activities.length} ${activities.length === 1 ? 'activity' : 'activities'} logged`;
  if (activities.length === 0) {
    activityFeed.innerHTML = '';
    activityFeed.appendChild(emptyActivityState);
  } else {
    activityFeed.innerHTML = '';
    // Reverse chronological order
    [...activities].reverse().forEach(act => {
      const item = document.createElement('div');
      item.className = 'activity-item';

      const iconMap = {
        travel: '🚌',
        electricity: '⚡',
        food: '🥗',
        waste: '♻️',
      };
      const icon = iconMap[(act.category || '').toLowerCase()] || '🌱';

      item.innerHTML = `
        <div class="act-left">
          <div class="act-badge-icon">${icon}</div>
          <div>
            <div class="act-details">${escapeHtml(act.details || act.category)}</div>
            <div class="act-meta">${act.date || todayIso} • ${act.category || 'General'}</div>
          </div>
        </div>
        <div class="act-kg">+${Number(act.kg_co2e).toFixed(3)} kg</div>
      `;
      activityFeed.appendChild(item);
    });
  }
}

// ============================================================================
// 3. MESSAGING & ADK /RUN EXECUTION
// ============================================================================
async function handleUserSubmit(text) {
  const message = text.trim();
  if (!message) return;

  // Disable UI during response
  btnSend.disabled = true;
  userInput.value = '';

  // Render user bubble
  appendUserMessage(message);

  // Render typing indicator
  const typingElem = showTypingIndicator();

  try {
    const activeLang = speechLangSelect ? speechLangSelect.value : 'te-IN';
    let langInstruction = '';
    if (activeLang === 'te-IN') {
      langInstruction = '\n[Language: Telugu]';
    } else if (activeLang === 'hi-IN') {
      langInstruction = '\n[Language: Hindi]';
    } else {
      langInstruction = '\n[Language: English]';
    }

    const payload = {
      appName: CONFIG.appName,
      userId: CONFIG.userId,
      sessionId: currentSessionId,
      newMessage: {
        role: 'user',
        parts: [{ text: `${message}${langInstruction}` }],
      },
    };

    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const events = await res.json();
    removeTypingIndicator(typingElem);

    let agentResponseText = '';
    const toolBadges = [];

    // Check if backend returned an error object
    if (events && events.error) {
      appendAgentMessage(`⚠️ Backend error: ${events.error}`);
      return;
    }

    // Parse ADK events for functionCalls and text
    if (Array.isArray(events)) {
      events.forEach(ev => {
        if (ev.error_message) {
          toolBadges.push(`⚠️ ${ev.error_code || 'Error'}: ${ev.error_message}`);
        }
        const parts = ev?.content?.parts || [];
        parts.forEach(p => {
          if (p.text) {
            agentResponseText += p.text + '\n';
          }
          if (p.functionCall) {
            const name = p.functionCall.name;
            const args = p.functionCall.args || {};
            let argSummary = Object.entries(args)
              .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
              .join(', ');
            toolBadges.push(`⚡ ${name}(${argSummary})`);
          }
          if (p.functionResponse && p.functionResponse.response) {
            const r = p.functionResponse.response;
            if (r.kg_co2e !== undefined) {
              toolBadges.push(`📊 Result: ${r.kg_co2e} kg CO₂e`);
            }
          }
        });
      });
    }

    if (!agentResponseText.trim()) {
      if (toolBadges.length > 0) {
        agentResponseText = 'Tool calculations completed successfully. See tool execution details above.';
      } else {
        agentResponseText = 'Could not generate a response. Please check that the ADK backend server is running.';
      }
    }

    // Render agent bubble with tool badges
    appendAgentMessage(agentResponseText.trim(), toolBadges);

    // Speak response if voice audio is enabled
    speakAgentReply(agentResponseText.trim());

    // Refresh memory and dashboard metrics
    await refreshSessionState();
  } catch (err) {
    console.error('[Carbon Coach] Error invoking agent:', err);
    removeTypingIndicator(typingElem);
    appendAgentMessage('❌ Sorry, I encountered an error communicating with the agent server. Please try again.');
  } finally {
    btnSend.disabled = false;
    userInput.focus();
  }
}

// ============================================================================
// 4. CHAT DOM HELPERS
// ============================================================================
function appendUserMessage(text) {
  const msg = document.createElement('div');
  msg.className = 'message user';
  msg.innerHTML = `
    <div class="msg-bubble">${escapeHtml(text)}</div>
    <div class="msg-time">Just now</div>
  `;
  messagesStream.appendChild(msg);
  scrollToBottom();
}

function appendAgentMessage(text, toolBadges = []) {
  const msg = document.createElement('div');
  msg.className = 'message agent';

  let toolBadgesHtml = '';
  if (toolBadges && toolBadges.length > 0) {
    const badgesContent = toolBadges
      .map(b => `<div class="tool-badge"><span class="tool-icon">🛠️</span> ${escapeHtml(b)}</div>`)
      .join('');
    toolBadgesHtml = `<div class="tool-badge-container">${badgesContent}</div>`;
  }

  // Format simple markdown bold and lists
  let formattedText = escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n- /g, '<br>• ')
    .replace(/\n/g, '<br>');

  msg.innerHTML = `
    <div class="msg-bubble">
      ${toolBadgesHtml}
      <div>${formattedText}</div>
    </div>
    <div class="msg-time">Just now</div>
  `;
  messagesStream.appendChild(msg);
  scrollToBottom();
}

function showTypingIndicator() {
  const typing = document.createElement('div');
  typing.className = 'message agent typing-msg';
  typing.innerHTML = `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  messagesStream.appendChild(typing);
  scrollToBottom();
  return typing;
}

function removeTypingIndicator(elem) {
  if (elem && elem.parentNode) {
    elem.parentNode.removeChild(elem);
  }
}

function scrollToBottom() {
  messagesStream.scrollTop = messagesStream.scrollHeight;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

// ============================================================================
// 5. SPEECH RECOGNITION (MIC) & TEXT-TO-SPEECH (TTS)
// ============================================================================
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function initSpeechRecognition() {
  if (!SpeechRecognition) {
    console.warn('[Carbon Coach] Web Speech API not supported in this browser.');
    if (btnMic) {
      btnMic.title = 'Speech-to-text not supported in this browser. Please use Google Chrome or Edge.';
    }
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isRecording = true;
    btnMic.classList.add('recording');
    const lang = speechLangSelect.value;
    const langLabel = lang === 'te-IN' ? 'Telugu (తెలుగు)' : (lang === 'hi-IN' ? 'Hindi (हिंदी)' : 'English');
    voiceStatusText.textContent = `మాట్లాడండి (${langLabel} లో వింటున్నాను)...`;
    voiceStatusBanner.style.display = 'flex';
  };

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
      .map(result => result[0].transcript)
      .join('');
    userInput.value = transcript;

    // If final result, pause briefly and submit
    if (event.results[0].isFinal) {
      setTimeout(() => {
        stopSpeechRecognition();
        if (userInput.value.trim()) {
          handleUserSubmit(userInput.value.trim());
        }
      }, 500);
    }
  };

  recognition.onerror = (event) => {
    console.error('[Carbon Coach] Speech recognition error:', event.error);
    stopSpeechRecognition();
    if (event.error === 'not-allowed') {
      alert('Microphone permission was denied. Please allow microphone access in your browser settings to speak in Telugu or English.');
    }
  };

  recognition.onend = () => {
    stopSpeechRecognition();
  };
}

function startSpeechRecognition() {
  if (!recognition) {
    initSpeechRecognition();
  }
  if (!recognition) {
    alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
    return;
  }
  try {
    recognition.lang = speechLangSelect.value || 'te-IN';
    recognition.start();
  } catch (err) {
    console.warn('[Carbon Coach] Could not start speech recognition:', err);
    stopSpeechRecognition();
  }
}

function stopSpeechRecognition() {
  isRecording = false;
  if (btnMic) btnMic.classList.remove('recording');
  if (voiceStatusBanner) voiceStatusBanner.style.display = 'none';
  if (recognition) {
    try { recognition.stop(); } catch (_) {}
  }
}

// Text-to-Speech (TTS) Voice Reply
function speakAgentReply(text) {
  if (!audioVoiceEnabled || !('speechSynthesis' in window)) return;

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  // Strip markdown formatting & emojis for cleaner speech
  const cleanText = text
    .replace(/[*_#`~]/g, '')
    .replace(/[🛠️⚡📊🌿🌱🌍💡🏆❓🚌🍗]/g, '')
    .trim();

  if (!cleanText) return;

  const utterance = new SpeechSynthesisUtterance(cleanText);

  // Check if text contains Telugu Unicode characters (\u0C00 - \u0C7F)
  const isTelugu = /[\u0C00-\u0C7F]/.test(cleanText);
  const isHindi = /[\u0900-\u097F]/.test(cleanText);

  if (isTelugu) {
    utterance.lang = 'te-IN';
  } else if (isHindi) {
    utterance.lang = 'hi-IN';
  } else {
    utterance.lang = 'en-IN';
  }

  // Attempt to pick a matching system voice
  const voices = window.speechSynthesis.getVoices();
  const matchedVoice = voices.find(v => v.lang === utterance.lang || v.lang.startsWith(utterance.lang.split('-')[0]));
  if (matchedVoice) {
    utterance.voice = matchedVoice;
  }

  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

// ============================================================================
// 6. EVENT LISTENERS
// ============================================================================
chatForm.addEventListener('submit', e => {
  e.preventDefault();
  handleUserSubmit(userInput.value);
});

// Mic Button Click Listener
if (btnMic) {
  btnMic.addEventListener('click', () => {
    if (isRecording) {
      stopSpeechRecognition();
    } else {
      startSpeechRecognition();
    }
  });
}

// Cancel Voice Listening
if (btnVoiceCancel) {
  btnVoiceCancel.addEventListener('click', () => {
    stopSpeechRecognition();
  });
}

// ============================================================================
// 6. MULTILINGUAL I18N SYSTEM (TELUGU, HINDI, ENGLISH)
// ============================================================================
const I18N = {
  'te-IN': {
    langName: 'తెలుగు (Telugu)',
    placeholder: 'తెలుగులో చెప్పండి లేదా మైక్ వాడండి (ఉదా: 50 km బైక్, 4 గంటల ఏసీ)...',
    chatTitle: '💬 కార్బన్ కోచ్‌తో మాట్లాడండి',
    audioLabel: '🔊 వాయిస్ రీడ్:',
    voiceListening: 'మాట్లాడండి (తెలుగులో వింటున్నాను)...',
    voiceCancel: 'రద్దు (Stop)',
    welcomeBubble: `👋 <strong>నమస్కారం!</strong> నేను మీ <strong>కార్బన్ కోచ్ (Carbon Coach)</strong> ని.<br>
మీరు తెలుగులో మాట్లాడవచ్చు లేదా టైప్ చేయవచ్చు!<br>
మీ ప్రయాణం, విద్యుత్/ఏసీ, ఆహారం లేదా వ్యర్థాల గురించి చెప్పండి—ఉదాహరణకు <em>"నేను ఈరోజు 12 కిమీ బస్సులో ప్రయాణించాను మరియు 4 గంటలు ఏసీ వాడాను"</em>—నేను ఖచ్చితమైన ఉద్గారాలను లెక్కించి, ప్రకృతిపై ప్రభావం మరియు తగ్గించుకునే చిట్కాలను అందిస్తాను!`,
    langSwitchedNotice: '✨ **భాష మార్చబడింది:** కార్బన్ కోచ్ ఇప్పుడు పూర్తిగా తెలుగులో స్పందిస్తుంది! క్రింది చిట్కాలను ప్రయత్నించండి లేదా మైక్ ద్వారా మాట్లాడండి.',
    suggestions: [
      { label: '🚌 12 కిమీ బస్సు + 4 గంటల ఏసీ', text: 'నేను ఈరోజు 12 కిమీ బస్సులో ప్రయాణించాను మరియు 4 గంటలు ఏసీ వాడాను' },
      { label: '🍗 చికెన్ బిర్యానీ', text: 'నేను లంచ్ లో చికెన్ బిర్యానీ తిన్నాను' },
      { label: '🛵 50 కిమీ బైక్', text: 'నేను ఈరోజు 50 కిలోమీటర్లు బైక్ మీద ప్రయాణించాను' },
      { label: '❓ అస్పష్ట ప్రశ్న (టెస్ట్)', text: 'నేను ఈరోజు ప్రయాణించాను' },
      { label: '📊 ఈ వారం సమ్మరీ', text: 'ఈ వారం నా కార్బన్ ఫుట్‌ప్రింట్ సమ్మరీ ఎంత?' },
      { label: '💡 తగ్గింపు చిట్కాలు', text: 'నా కార్బన్ ఫుట్‌ప్రింట్ తగ్గించడానికి చిట్కాలు చెప్పండి' },
      { label: '🏆 క్యాంపస్ లీడర్‌బోర్డ్', text: 'క్యాంపస్ సస్టైనబిలిటీ లీడర్‌బోర్డ్ చూపించు' }
    ]
  },
  'en-IN': {
    langName: 'English (India)',
    placeholder: 'Describe your activity or click mic (e.g. 15 km by metro, 4h AC)...',
    chatTitle: '💬 Chat with Carbon Coach',
    audioLabel: '🔊 Voice Reply:',
    voiceListening: 'Speak now (Listening in English)...',
    voiceCancel: 'Stop',
    welcomeBubble: `👋 <strong>Namaste!</strong> I am your <strong>Carbon Coach</strong>.<br>
You can speak or type in English, Telugu, or Hindi!<br>
Tell me about your travel, electricity, food, or waste—like <em>"I travelled 12 km by bus today and used the AC for 4 hours"</em>—and I'll measure your emissions with zero-hallucination precision and suggest eco tips!`,
    langSwitchedNotice: '✨ **Language switched:** Carbon Coach will now respond in English! Try the suggestions below or use the mic.',
    suggestions: [
      { label: '🚌 12 km bus + 4h AC', text: 'I travelled 12 km by bus today and used the AC for 4 hours' },
      { label: '🍗 Chicken biryani', text: 'I had a chicken biryani for lunch' },
      { label: '🛵 50 km two-wheeler', text: 'I travelled 50 km by two-wheeler today' },
      { label: '❓ Ambiguous query test', text: 'I travelled today' },
      { label: '📊 Weekly summary', text: 'How did I do this week?' },
      { label: '💡 Reduction tips', text: 'How can I reduce my carbon footprint?' },
      { label: '🏆 Campus leaderboard', text: 'Show the campus sustainability leaderboard' }
    ]
  },
  'hi-IN': {
    langName: 'हिंदी (Hindi)',
    placeholder: 'अपनी गतिविधि बताएं या माइक दबाएं (उदा: 50 किमी बाइक, 4 घंटे एसी)...',
    chatTitle: '💬 कार्बन कोच से बात करें',
    audioLabel: '🔊 वॉइस उत्तर:',
    voiceListening: 'बोलिए (हिंदी में सुन रहा हूँ)...',
    voiceCancel: 'रोकें (Stop)',
    welcomeBubble: `👋 <strong>नमस्ते!</strong> मैं आपका <strong>कार्बन कोच (Carbon Coach)</strong> हूँ।<br>
आप हिंदी में बोल या लिख सकते हैं!<br>
अपनी यात्रा, बिजली/एसी, भोजन या कचरे के बारे में बताएं—जैसे <em>"मैंने आज 12 किमी बस से यात्रा की और 4 घंटे एसी चलाया"</em>—मैं आपके कार्बन उत्सर्जन की सटीक गणना करूँगा और प्रकृति पर प्रभाव व बचत के उपाय साझा करूँगा!`,
    langSwitchedNotice: '✨ **भाषा बदली गई:** कार्बन कोच अब हिंदी में उत्तर देगा! नीचे दिए गए सुझावों पर क्लिक करें या माइक दबाकर बोलें।',
    suggestions: [
      { label: '🚌 12 किमी बस + 4 घंटे एसी', text: 'मैंने आज 12 किमी बस से यात्रा की और 4 घंटे एसी चलाया' },
      { label: '🍗 चिकन बिरयानी', text: 'मैंने दोपहर के खाने में चिकन बिरयानी खाई' },
      { label: '🛵 50 किमी बाइक', text: 'मैंने आज 50 किमी बाइक चलाई' },
      { label: '❓ अस्पष्ट प्रश्न परीक्षण', text: 'मैंने आज यात्रा की' },
      { label: '📊 साप्ताहिक सारांश', text: 'इस सप्ताह मेरा कार्बन स्कोर कैसा रहा?' },
      { label: '💡 बचत के उपाय', text: 'मैं अपना कार्बन फुटप्रिंट कैसे कम करूँ?' },
      { label: '🏆 कैंपस लीडरबोर्ड', text: 'कैंपस सस्टेनेबिलिटी लीडरबोर्ड दिखाएं' }
    ]
  }
};

function renderLanguageUI(lang, announceSwitch = false) {
  const dict = I18N[lang] || I18N['te-IN'];

  // Update Input & Headers
  if (userInput) userInput.placeholder = dict.placeholder;
  if (chatTitleText) chatTitleText.textContent = dict.chatTitle;
  if (audioToggleLabel) audioToggleLabel.textContent = dict.audioLabel;
  if (voiceStatusText && !isRecording) voiceStatusText.textContent = dict.voiceListening;
  if (btnVoiceCancel) btnVoiceCancel.textContent = dict.voiceCancel;

  // Update initial welcome bubble if visible
  if (welcomeMsgBubble) {
    welcomeMsgBubble.innerHTML = dict.welcomeBubble;
  }

  // Dynamically re-render Quick Action Chips
  if (quickChipsBar) {
    quickChipsBar.innerHTML = '';
    dict.suggestions.forEach(item => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'chip-btn' + (lang === 'te-IN' ? ' chip-telugu' : '');
      btn.textContent = item.label;
      btn.setAttribute('data-text', item.text);
      btn.addEventListener('click', () => {
        handleUserSubmit(item.text);
      });
      quickChipsBar.appendChild(btn);
    });
  }

  // If user changed language during chat, announce with an agent pill
  if (announceSwitch) {
    appendAgentMessage(dict.langSwitchedNotice);
    speakAgentReply(dict.langSwitchedNotice);
  }

  try {
    localStorage.setItem('carbon_coach_lang', lang);
  } catch (_) {}
}

// ============================================================================
// 7. EVENT LISTENERS
// ============================================================================
chatForm.addEventListener('submit', e => {
  e.preventDefault();
  handleUserSubmit(userInput.value);
});

// Mic Button Click Listener
if (btnMic) {
  btnMic.addEventListener('click', () => {
    if (isRecording) {
      stopSpeechRecognition();
    } else {
      startSpeechRecognition();
    }
  });
}

// Cancel Voice Listening
if (btnVoiceCancel) {
  btnVoiceCancel.addEventListener('click', () => {
    stopSpeechRecognition();
  });
}

// Language Selector Change Listener
if (speechLangSelect) {
  speechLangSelect.addEventListener('change', () => {
    const selected = speechLangSelect.value;
    renderLanguageUI(selected, true);
    // If currently recording, restart with new language
    if (isRecording) {
      stopSpeechRecognition();
      setTimeout(startSpeechRecognition, 300);
    }
  });
}

// Voice Readout Audio Toggle
if (btnAudioToggle) {
  btnAudioToggle.addEventListener('click', () => {
    audioVoiceEnabled = !audioVoiceEnabled;
    if (audioVoiceEnabled) {
      btnAudioToggle.classList.add('active');
      audioToggleState.textContent = 'ON';
    } else {
      btnAudioToggle.classList.remove('active');
      audioToggleState.textContent = 'OFF';
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    }
  });
}

// Campus Leaderboard Modal
btnLeaderboard.addEventListener('click', () => {
  leaderboardModal.classList.add('active');
});

btnCloseModal.addEventListener('click', () => {
  leaderboardModal.classList.remove('active');
});

leaderboardModal.addEventListener('click', e => {
  if (e.target === leaderboardModal) {
    leaderboardModal.classList.remove('active');
  }
});

// Reset Session
btnResetSession.addEventListener('click', async () => {
  const activeLang = speechLangSelect ? speechLangSelect.value : 'te-IN';
  const dict = I18N[activeLang] || I18N['te-IN'];
  if (confirm('Start a fresh session? This will clear the current footprint log.')) {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    await initSession();
    messagesStream.innerHTML = `
      <div class="message agent">
        <div class="msg-bubble">
          ${dict.welcomeBubble}
        </div>
        <div class="msg-time">Just now</div>
      </div>
    `;
  }
});

// ============================================================================
// 8. THEME MANAGEMENT (DARK / LIGHT MODE)
// ============================================================================
function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
    if (themeToggleIcon) themeToggleIcon.textContent = '🌙';
    if (themeToggleText) themeToggleText.textContent = 'Dark Mode';
  } else {
    document.documentElement.removeAttribute('data-theme');
    if (themeToggleIcon) themeToggleIcon.textContent = '☀️';
    if (themeToggleText) themeToggleText.textContent = 'Light Mode';
  }
  try {
    localStorage.setItem('carbon_coach_theme', theme);
  } catch (_) {}
}

function initTheme() {
  let savedTheme = 'dark';
  try {
    savedTheme = localStorage.getItem('carbon_coach_theme') || 'dark';
  } catch (_) {}
  applyTheme(savedTheme);

  if (btnThemeToggle) {
    btnThemeToggle.addEventListener('click', () => {
      const isLight = document.documentElement.getAttribute('data-theme') === 'light';
      applyTheme(isLight ? 'dark' : 'light');
    });
  }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  initTheme();
  
  // Initialize language from saved preference or default to Telugu
  let savedLang = 'te-IN';
  try {
    savedLang = localStorage.getItem('carbon_coach_lang') || 'te-IN';
  } catch (_) {}
  if (speechLangSelect) {
    speechLangSelect.value = savedLang;
  }
  renderLanguageUI(savedLang, false);

  initSession();
  initSpeechRecognition();

  // Ensure voice list is loaded for TTS
  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices();
    };
  }
});
