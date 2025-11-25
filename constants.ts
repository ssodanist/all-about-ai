import { AICompany } from './types';

export const GRID_COLUMNS = 40;
export const GRID_ROWS = 25;
export const TOTAL_BLOCKS = GRID_COLUMNS * GRID_ROWS;

export const DEFAULT_COMPANIES: AICompany[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'Creators of ChatGPT and GPT-4.',
    share: 15,
    color: '#10a37f',
    textColor: '#ffffff',
    domain: 'openai.com',
    url: 'https://openai.com'
  },
  {
    id: 'google-deepmind',
    name: 'Google DeepMind',
    description: 'Gemini and AlphaGo.',
    share: 12,
    color: '#4285F4',
    textColor: '#ffffff',
    domain: 'deepmind.google',
    url: 'https://deepmind.google'
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Claude 3 and constitutional AI.',
    share: 8,
    color: '#d97757',
    textColor: '#ffffff',
    domain: 'anthropic.com',
    url: 'https://www.anthropic.com'
  },
  {
    id: 'perplex',
    name: 'Perplexity',
    description: 'AI answer engine.',
    share: 5,
    color: '#22B3AA',
    textColor: '#ffffff',
    domain: 'perplexity.ai',
    url: 'https://perplexity.ai'
  },
  {
    id: 'midjourney',
    name: 'Midjourney',
    description: 'Art generation.',
    share: 5,
    color: '#ffffff',
    textColor: '#000000',
    domain: 'midjourney.com',
    url: 'https://midjourney.com'
  },
  {
    id: 'huggingface',
    name: 'Hugging Face',
    description: 'The AI community hub.',
    share: 4,
    color: '#FFD21E',
    textColor: '#000000',
    domain: 'huggingface.co',
    url: 'https://huggingface.co'
  },
  {
    id: 'nvidia',
    name: 'NVIDIA',
    description: 'AI Hardware.',
    share: 4,
    color: '#76B900',
    textColor: '#ffffff',
    domain: 'nvidia.com',
    url: 'https://nvidianews.nvidia.com'
  },
  {
    id: 'meta',
    name: 'Meta Llama',
    description: 'Open source LLMs.',
    share: 3,
    color: '#0668E1',
    textColor: '#ffffff',
    domain: 'meta.com',
    url: 'https://ai.meta.com'
  },
  {
    id: 'stability',
    name: 'Stability AI',
    description: 'Stable Diffusion.',
    share: 3,
    color: '#4c2a78',
    textColor: '#ffffff',
    domain: 'stability.ai',
    url: 'https://stability.ai'
  },
  {
    id: 'microsoft',
    name: 'Microsoft Copilot',
    description: 'AI productivity.',
    share: 3,
    color: '#00A4EF',
    textColor: '#ffffff',
    domain: 'microsoft.com',
    url: 'https://microsoft.com/ai'
  },
  {
    id: 'xai',
    name: 'xAI',
    description: 'Grok.',
    share: 2.5,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'x.ai',
    url: 'https://x.ai'
  },
  {
    id: 'suno',
    name: 'Suno',
    description: 'Music generation.',
    share: 2.5,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'suno.com',
    url: 'https://suno.com'
  },
  {
    id: 'udio',
    name: 'Udio',
    description: 'Music creation.',
    share: 2,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'udio.com',
    url: 'https://www.udio.com'
  },
  {
    id: 'civitai',
    name: 'Civitai',
    description: 'Model sharing hub.',
    share: 2,
    color: '#223447',
    textColor: '#ffffff',
    domain: 'civitai.com',
    url: 'https://civitai.com'
  },
  {
    id: 'characterai',
    name: 'Character.ai',
    description: 'Chat with personas.',
    share: 2,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'character.ai',
    url: 'https://character.ai'
  },
  {
    id: 'runway',
    name: 'Runway',
    description: 'Video editing.',
    share: 1.5,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'runwayml.com',
    url: 'https://runwayml.com'
  },
  {
    id: 'pika',
    name: 'Pika',
    description: 'Video generation.',
    share: 1.5,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'pika.art',
    url: 'https://pika.art'
  },
  {
    id: 'leonardo',
    name: 'Leonardo.ai',
    description: 'Game assets & art.',
    share: 1.5,
    color: '#5E4AE3',
    textColor: '#ffffff',
    domain: 'leonardo.ai',
    url: 'https://leonardo.ai'
  },
  {
    id: 'elevenlabs',
    name: 'ElevenLabs',
    description: 'Voice cloning.',
    share: 1.5,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'elevenlabs.io',
    url: 'https://elevenlabs.io'
  },
  {
    id: 'poe',
    name: 'Poe',
    description: 'Fast chatbot aggregator.',
    share: 1.5,
    color: '#4B39EF',
    textColor: '#ffffff',
    domain: 'poe.com',
    url: 'https://poe.com'
  },
  {
    id: 'cohere',
    name: 'Cohere',
    description: 'Enterprise models.',
    share: 1,
    color: '#39594c',
    textColor: '#ffffff',
    domain: 'cohere.com',
    url: 'https://cohere.com'
  },
  {
    id: 'jasper',
    name: 'Jasper',
    description: 'Marketing AI.',
    share: 1,
    color: '#8955f2',
    textColor: '#ffffff',
    domain: 'jasper.ai',
    url: 'https://jasper.ai'
  },
  {
    id: 'copyai',
    name: 'Copy.ai',
    description: 'Copywriting.',
    share: 1,
    color: '#41E370',
    textColor: '#000000',
    domain: 'copy.ai',
    url: 'https://copy.ai'
  },
  {
    id: 'kling',
    name: 'Kling AI',
    description: 'Realistic video.',
    share: 1,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'klingai.com',
    url: 'https://klingai.com'
  },
  {
    id: 'luma',
    name: 'Luma Dream Machine',
    description: '3D and Video.',
    share: 1,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'lumalabs.ai',
    url: 'https://lumalabs.ai'
  },
  {
    id: 'canva',
    name: 'Canva',
    description: 'Magic Studio.',
    share: 1,
    color: '#00C4CC',
    textColor: '#ffffff',
    domain: 'canva.com',
    url: 'https://canva.com'
  },
  {
    id: 'notion',
    name: 'Notion AI',
    description: 'Workspace AI.',
    share: 1,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'notion.so',
    url: 'https://notion.so'
  },
  {
    id: 'adobe',
    name: 'Adobe Firefly',
    description: 'Creative generative AI.',
    share: 1,
    color: '#FF0000',
    textColor: '#ffffff',
    domain: 'adobe.com',
    url: 'https://firefly.adobe.com'
  },
  {
    id: 'cursor',
    name: 'Cursor',
    description: 'AI Code Editor.',
    share: 1,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'cursor.sh',
    url: 'https://cursor.sh'
  },
  {
    id: 'mistral',
    name: 'Mistral',
    description: 'European open models.',
    share: 1,
    color: '#F4B938',
    textColor: '#000000',
    domain: 'mistral.ai',
    url: 'https://mistral.ai'
  },
  {
    id: 'scale',
    name: 'Scale AI',
    description: 'Data labeling.',
    share: 1,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'scale.com',
    url: 'https://scale.com'
  },
  {
    id: 'groq',
    name: 'Groq',
    description: 'Fast inference.',
    share: 1,
    color: '#F55036',
    textColor: '#ffffff',
    domain: 'groq.com',
    url: 'https://groq.com'
  },
  {
    id: 'magnific',
    name: 'Magnific',
    description: 'Upscaling.',
    share: 1,
    color: '#FF00FF',
    textColor: '#ffffff',
    domain: 'magnific.ai',
    url: 'https://magnific.ai'
  },
  {
    id: 'replika',
    name: 'Replika',
    description: 'AI companion.',
    share: 1,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'replika.com',
    url: 'https://replika.com'
  },
  {
    id: 'framer',
    name: 'Framer',
    description: 'AI web design.',
    share: 1,
    color: '#000000',
    textColor: '#ffffff',
    domain: 'framer.com',
    url: 'https://framer.com'
  }
];