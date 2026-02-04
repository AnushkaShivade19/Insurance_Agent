/* static/js/offline_bot.js */

const OFFLINE_KNOWLEDGE = [
    {
        keywords: ["hi", "hello", "namaste", "hey", "start"],
        answer: "Namaste! 🙏 I am currently in <b>Offline Mode</b>. I can still help you find agents, view policies, or guide you on claims."
    },
    {
        keywords: ["claim", "accident", "file", "report"],
        answer: "<b>Offline Claim Guide:</b><br>1. Go to Dashboard > File Claim.<br>2. Upload photos (they will sync when internet returns).<br>3. Or call <b>1800-123-BIMA</b>."
    },
    {
        keywords: ["policy", "status", "active", "check", "my policy"],
        answer: "You can view your downloaded policies in the <a href='/dashboard/'>Dashboard</a>. We saved them for you!"
    },
    {
        keywords: ["agent", "contact", "call", "help", "number"],
        answer: "Our helpline works without internet! Call us: <a href='tel:18001232462'>1800-123-BIMA</a>."
    },
    {
        keywords: ["buy", "purchase", "new", "plan"],
        answer: "To buy a new policy, you need an active internet connection. Please try again when you have signal."
    }
];

function getOfflineResponse(text) {
    text = text.toLowerCase();
    
    // 1. Find a matching keyword
    for (let item of OFFLINE_KNOWLEDGE) {
        for (let key of item.keywords) {
            if (text.includes(key)) {
                return item.answer;
            }
        }
    }
    
    // 2. Default Answer if no match
    return "I am in <b>Offline Mode</b> 📶. <br>I can't check live data, but I can help with 'Claims', 'Agents', or 'My Policies'.";
}