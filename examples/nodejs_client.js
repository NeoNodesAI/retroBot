/**
 * retroBot Node.js Client Example
 */
const axios = require('axios');

const API_URL = 'http://173.212.220.240:8000';

async function askRetroBot(question) {
    const response = await axios.post(`${API_URL}/runs/wait`, {
        assistant_id: 'retrobot-warden-001',
        input: {
            messages: [
                { role: 'user', content: question }
            ]
        }
    });
    
    return response.data;
}

async function createThread() {
    const response = await axios.post(`${API_URL}/threads`);
    return response.data.thread_id;
}

async function sendMessageToThread(threadId, message) {
    const response = await axios.post(`${API_URL}/threads/${threadId}/runs`, {
        input: {
            messages: [
                { role: 'user', content: message }
            ]
        }
    });
    
    return response.data;
}

async function main() {
    console.log('=== retroBot Node.js Client ===\n');
    
    try {
        // Example 1: Simple question
        console.log('1. Simple Question:');
        const result1 = await askRetroBot('What is the price of BTC?');
        const messages1 = result1.output.messages;
        console.log(messages1[messages1.length - 1].content);
        console.log('\n' + '='.repeat(50) + '\n');
        
        // Example 2: Retro command
        console.log('2. Retro Command:');
        const result2 = await askRetroBot('/retro help');
        const messages2 = result2.output.messages;
        console.log(messages2[messages2.length - 1].content);
        console.log('\n' + '='.repeat(50) + '\n');
        
        // Example 3: Thread conversation
        console.log('3. Thread Conversation:');
        const threadId = await createThread();
        console.log(`Created thread: ${threadId}\n`);
        
        // First message
        const msg1 = await sendMessageToThread(threadId, 'What is ETH price?');
        console.log('Q: What is ETH price?');
        console.log('A:', msg1.output.messages[msg1.output.messages.length - 1].content.substring(0, 200), '...\n');
        
        // Follow-up
        const msg2 = await sendMessageToThread(threadId, 'What about SOL?');
        console.log('Q: What about SOL?');
        console.log('A:', msg2.output.messages[msg2.output.messages.length - 1].content.substring(0, 200), '...');
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();

